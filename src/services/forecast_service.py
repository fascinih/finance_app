"""
Financial Forecasting Service.
Previsões financeiras usando Prophet e ARIMA.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import warnings
from loguru import logger

# Suppress warnings from forecasting libraries
warnings.filterwarnings('ignore')

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logger.warning("Prophet not available. Install with: pip install prophet")

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.seasonal import seasonal_decompose
    from statsmodels.stats.diagnostic import acorr_ljungbox
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logger.warning("Statsmodels not available. Install with: pip install statsmodels")

from sqlalchemy.orm import Session
from src.models import Transaction, Category


@dataclass
class ForecastResult:
    """Resultado de previsão financeira."""
    dates: List[date]
    values: List[float]
    lower_bound: List[float]
    upper_bound: List[float]
    confidence_interval: float
    model_type: str
    accuracy_metrics: Dict[str, float]
    seasonality_detected: bool
    trend_direction: str  # 'increasing', 'decreasing', 'stable'


class FinancialForecaster:
    """Serviço de previsão financeira."""
    
    def __init__(self):
        self.min_data_points = 30  # Mínimo de pontos para previsão confiável
        self.default_forecast_days = 90  # Padrão de 3 meses
        
    def forecast_expenses(
        self, 
        db: Session, 
        category_id: Optional[int] = None,
        days_back: int = 365,
        forecast_days: int = 90,
        model_type: str = "auto"
    ) -> ForecastResult:
        """
        Prevê despesas futuras.
        
        Args:
            db: Sessão do banco de dados
            category_id: ID da categoria (None para todas)
            days_back: Dias históricos para análise
            forecast_days: Dias para prever
            model_type: Tipo de modelo ('prophet', 'arima', 'auto')
            
        Returns:
            Resultado da previsão
        """
        
        # Buscar dados históricos
        historical_data = self._get_historical_expenses(db, category_id, days_back)
        
        if len(historical_data) < self.min_data_points:
            raise ValueError(f"Dados insuficientes. Mínimo: {self.min_data_points}, encontrados: {len(historical_data)}")
        
        # Preparar dados para previsão
        df = self._prepare_time_series_data(historical_data)
        
        # Escolher modelo automaticamente se necessário
        if model_type == "auto":
            model_type = self._select_best_model(df)
        
        # Executar previsão
        if model_type == "prophet" and PROPHET_AVAILABLE:
            return self._forecast_with_prophet(df, forecast_days)
        elif model_type == "arima" and STATSMODELS_AVAILABLE:
            return self._forecast_with_arima(df, forecast_days)
        else:
            # Fallback para método simples
            return self._forecast_simple(df, forecast_days)
    
    def forecast_income(
        self, 
        db: Session, 
        days_back: int = 365,
        forecast_days: int = 90
    ) -> ForecastResult:
        """Prevê receitas futuras."""
        
        # Buscar receitas históricas
        cutoff_date = date.today() - timedelta(days=days_back)
        
        income_data = db.query(
            Transaction.date,
            Transaction.amount
        ).filter(
            Transaction.date >= cutoff_date,
            Transaction.amount > 0  # Apenas receitas
        ).order_by(Transaction.date).all()
        
        if len(income_data) < self.min_data_points:
            raise ValueError(f"Dados de receita insuficientes: {len(income_data)}")
        
        # Agrupar por dia
        daily_income = {}
        for tx_date, amount in income_data:
            if tx_date not in daily_income:
                daily_income[tx_date] = 0
            daily_income[tx_date] += float(amount)
        
        # Preparar DataFrame
        df = pd.DataFrame([
            {"ds": dt, "y": amount} 
            for dt, amount in daily_income.items()
        ])
        
        # Preencher dias sem receita com 0
        df = self._fill_missing_dates(df)
        
        # Usar Prophet para receitas (melhor para sazonalidade)
        if PROPHET_AVAILABLE:
            return self._forecast_with_prophet(df, forecast_days)
        else:
            return self._forecast_simple(df, forecast_days)
    
    def forecast_cash_flow(
        self, 
        db: Session, 
        days_back: int = 365,
        forecast_days: int = 90
    ) -> Dict[str, ForecastResult]:
        """
        Prevê fluxo de caixa (receitas - despesas).
        
        Returns:
            Dicionário com previsões de receitas, despesas e fluxo líquido
        """
        
        try:
            # Prever receitas
            income_forecast = self.forecast_income(db, days_back, forecast_days)
            
            # Prever despesas
            expense_forecast = self.forecast_expenses(db, None, days_back, forecast_days)
            
            # Calcular fluxo líquido
            net_values = [
                income - abs(expense) 
                for income, expense in zip(income_forecast.values, expense_forecast.values)
            ]
            
            net_lower = [
                income_lower - abs(expense_upper)
                for income_lower, expense_upper in zip(income_forecast.lower_bound, expense_forecast.upper_bound)
            ]
            
            net_upper = [
                income_upper - abs(expense_lower)
                for income_upper, expense_lower in zip(income_forecast.upper_bound, expense_forecast.lower_bound)
            ]
            
            # Determinar tendência do fluxo
            trend_direction = "stable"
            if len(net_values) > 1:
                trend_slope = np.polyfit(range(len(net_values)), net_values, 1)[0]
                if trend_slope > 10:  # R$ 10/dia
                    trend_direction = "increasing"
                elif trend_slope < -10:
                    trend_direction = "decreasing"
            
            net_forecast = ForecastResult(
                dates=income_forecast.dates,
                values=net_values,
                lower_bound=net_lower,
                upper_bound=net_upper,
                confidence_interval=0.8,  # Média das confianças
                model_type="composite",
                accuracy_metrics={},
                seasonality_detected=income_forecast.seasonality_detected or expense_forecast.seasonality_detected,
                trend_direction=trend_direction
            )
            
            return {
                "income": income_forecast,
                "expenses": expense_forecast,
                "net_flow": net_forecast
            }
            
        except Exception as e:
            logger.error(f"Erro na previsão de fluxo de caixa: {e}")
            raise
    
    def _get_historical_expenses(
        self, 
        db: Session, 
        category_id: Optional[int], 
        days_back: int
    ) -> List[Tuple[date, float]]:
        """Busca dados históricos de despesas."""
        
        cutoff_date = date.today() - timedelta(days=days_back)
        
        query = db.query(
            Transaction.date,
            Transaction.amount
        ).filter(
            Transaction.date >= cutoff_date,
            Transaction.amount < 0  # Apenas despesas
        )
        
        if category_id:
            query = query.filter(Transaction.category_id == category_id)
        
        return query.order_by(Transaction.date).all()
    
    def _prepare_time_series_data(self, raw_data: List[Tuple[date, float]]) -> pd.DataFrame:
        """Prepara dados para análise de séries temporais."""
        
        # Agrupar por dia e somar valores
        daily_expenses = {}
        for tx_date, amount in raw_data:
            if tx_date not in daily_expenses:
                daily_expenses[tx_date] = 0
            daily_expenses[tx_date] += abs(float(amount))  # Converter para positivo
        
        # Criar DataFrame
        df = pd.DataFrame([
            {"ds": dt, "y": amount} 
            for dt, amount in daily_expenses.items()
        ])
        
        # Preencher dias sem gastos com 0
        df = self._fill_missing_dates(df)
        
        return df
    
    def _fill_missing_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preenche datas faltantes com valor 0."""
        
        if df.empty:
            return df
        
        # Criar range completo de datas
        min_date = df['ds'].min()
        max_date = df['ds'].max()
        date_range = pd.date_range(start=min_date, end=max_date, freq='D')
        
        # Criar DataFrame completo
        complete_df = pd.DataFrame({'ds': date_range})
        
        # Merge com dados existentes
        df = complete_df.merge(df, on='ds', how='left')
        df['y'] = df['y'].fillna(0)
        
        return df
    
    def _select_best_model(self, df: pd.DataFrame) -> str:
        """Seleciona o melhor modelo baseado nos dados."""
        
        # Critérios para seleção:
        # - Prophet: bom para sazonalidade e tendências
        # - ARIMA: bom para dados estacionários
        # - Simple: fallback
        
        if not PROPHET_AVAILABLE and not STATSMODELS_AVAILABLE:
            return "simple"
        
        # Verificar sazonalidade
        if len(df) >= 60:  # Pelo menos 2 meses
            try:
                # Detectar sazonalidade semanal
                df_weekly = df.set_index('ds').resample('W').sum()
                if len(df_weekly) >= 8:  # Pelo menos 8 semanas
                    weekly_std = df_weekly['y'].std()
                    weekly_mean = df_weekly['y'].mean()
                    cv = weekly_std / weekly_mean if weekly_mean > 0 else 0
                    
                    # Se há variação significativa, usar Prophet
                    if cv > 0.3 and PROPHET_AVAILABLE:
                        return "prophet"
            except Exception:
                pass
        
        # Fallback para ARIMA se disponível
        if STATSMODELS_AVAILABLE:
            return "arima"
        elif PROPHET_AVAILABLE:
            return "prophet"
        else:
            return "simple"
    
    def _forecast_with_prophet(self, df: pd.DataFrame, forecast_days: int) -> ForecastResult:
        """Previsão usando Prophet."""
        
        try:
            # Configurar Prophet
            model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=len(df) >= 365,
                changepoint_prior_scale=0.05,
                seasonality_prior_scale=10.0,
                interval_width=0.8
            )
            
            # Treinar modelo
            model.fit(df)
            
            # Criar datas futuras
            future = model.make_future_dataframe(periods=forecast_days)
            
            # Fazer previsão
            forecast = model.predict(future)
            
            # Extrair resultados futuros
            future_forecast = forecast.tail(forecast_days)
            
            # Detectar sazonalidade
            seasonality_detected = any([
                'weekly' in model.seasonalities,
                'yearly' in model.seasonalities,
                len(model.seasonalities) > 0
            ])
            
            # Determinar tendência
            trend_values = forecast['trend'].tail(forecast_days).values
            trend_direction = "stable"
            if len(trend_values) > 1:
                trend_slope = np.polyfit(range(len(trend_values)), trend_values, 1)[0]
                if trend_slope > 1:
                    trend_direction = "increasing"
                elif trend_slope < -1:
                    trend_direction = "decreasing"
            
            # Calcular métricas de acurácia (usando dados históricos)
            historical_forecast = forecast.head(len(df))
            mae = np.mean(np.abs(historical_forecast['yhat'] - df['y']))
            mape = np.mean(np.abs((df['y'] - historical_forecast['yhat']) / np.maximum(df['y'], 1))) * 100
            
            return ForecastResult(
                dates=[d.date() for d in future_forecast['ds']],
                values=future_forecast['yhat'].tolist(),
                lower_bound=future_forecast['yhat_lower'].tolist(),
                upper_bound=future_forecast['yhat_upper'].tolist(),
                confidence_interval=0.8,
                model_type="prophet",
                accuracy_metrics={"mae": mae, "mape": mape},
                seasonality_detected=seasonality_detected,
                trend_direction=trend_direction
            )
            
        except Exception as e:
            logger.error(f"Erro no Prophet: {e}")
            return self._forecast_simple(df, forecast_days)
    
    def _forecast_with_arima(self, df: pd.DataFrame, forecast_days: int) -> ForecastResult:
        """Previsão usando ARIMA."""
        
        try:
            # Preparar série temporal
            ts = df.set_index('ds')['y']
            
            # Determinar parâmetros ARIMA automaticamente
            # Usar (1,1,1) como padrão para dados financeiros
            order = (1, 1, 1)
            
            # Treinar modelo ARIMA
            model = ARIMA(ts, order=order)
            fitted_model = model.fit()
            
            # Fazer previsão
            forecast_result = fitted_model.forecast(steps=forecast_days, alpha=0.2)  # 80% CI
            
            # Gerar datas futuras
            last_date = df['ds'].max()
            future_dates = [
                last_date + timedelta(days=i+1) 
                for i in range(forecast_days)
            ]
            
            # Extrair valores e intervalos de confiança
            forecast_values = forecast_result.tolist()
            
            # ARIMA não fornece intervalos de confiança facilmente
            # Usar desvio padrão dos resíduos como aproximação
            residuals_std = np.std(fitted_model.resid)
            lower_bound = [max(0, v - 1.96 * residuals_std) for v in forecast_values]
            upper_bound = [v + 1.96 * residuals_std for v in forecast_values]
            
            # Determinar tendência
            trend_direction = "stable"
            if len(forecast_values) > 1:
                trend_slope = np.polyfit(range(len(forecast_values)), forecast_values, 1)[0]
                if trend_slope > 1:
                    trend_direction = "increasing"
                elif trend_slope < -1:
                    trend_direction = "decreasing"
            
            # Calcular métricas
            fitted_values = fitted_model.fittedvalues
            mae = np.mean(np.abs(fitted_values - ts))
            mape = np.mean(np.abs((ts - fitted_values) / np.maximum(ts, 1))) * 100
            
            return ForecastResult(
                dates=[d.date() for d in future_dates],
                values=forecast_values,
                lower_bound=lower_bound,
                upper_bound=upper_bound,
                confidence_interval=0.8,
                model_type="arima",
                accuracy_metrics={"mae": mae, "mape": mape},
                seasonality_detected=False,  # ARIMA básico não detecta sazonalidade
                trend_direction=trend_direction
            )
            
        except Exception as e:
            logger.error(f"Erro no ARIMA: {e}")
            return self._forecast_simple(df, forecast_days)
    
    def _forecast_simple(self, df: pd.DataFrame, forecast_days: int) -> ForecastResult:
        """Previsão simples usando médias móveis."""
        
        # Calcular média móvel dos últimos 30 dias
        window = min(30, len(df))
        recent_avg = df['y'].tail(window).mean()
        
        # Calcular tendência simples
        if len(df) >= 7:
            recent_trend = df['y'].tail(7).mean() - df['y'].tail(14).head(7).mean()
        else:
            recent_trend = 0
        
        # Gerar previsões
        future_dates = []
        forecast_values = []
        last_date = df['ds'].max()
        
        for i in range(forecast_days):
            future_date = last_date + timedelta(days=i+1)
            future_dates.append(future_date.date())
            
            # Valor base + tendência
            forecast_value = max(0, recent_avg + (recent_trend * (i + 1) / 7))
            forecast_values.append(forecast_value)
        
        # Intervalos de confiança baseados no desvio padrão
        std_dev = df['y'].std()
        lower_bound = [max(0, v - 1.96 * std_dev) for v in forecast_values]
        upper_bound = [v + 1.96 * std_dev for v in forecast_values]
        
        # Determinar tendência
        trend_direction = "stable"
        if recent_trend > 1:
            trend_direction = "increasing"
        elif recent_trend < -1:
            trend_direction = "decreasing"
        
        return ForecastResult(
            dates=future_dates,
            values=forecast_values,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            confidence_interval=0.6,  # Menor confiança para método simples
            model_type="simple",
            accuracy_metrics={"mae": std_dev, "mape": 20.0},
            seasonality_detected=False,
            trend_direction=trend_direction
        )
    
    def analyze_seasonality(self, db: Session, category_id: Optional[int] = None) -> Dict[str, Any]:
        """Analisa padrões sazonais nos gastos."""
        
        # Buscar dados de pelo menos 1 ano
        historical_data = self._get_historical_expenses(db, category_id, 365)
        
        if len(historical_data) < 100:  # Mínimo para análise sazonal
            return {"seasonality_detected": False, "message": "Dados insuficientes"}
        
        # Preparar dados
        df = self._prepare_time_series_data(historical_data)
        
        # Análise por dia da semana
        df['weekday'] = pd.to_datetime(df['ds']).dt.day_name()
        weekday_avg = df.groupby('weekday')['y'].mean().to_dict()
        
        # Análise por mês
        df['month'] = pd.to_datetime(df['ds']).dt.month_name()
        monthly_avg = df.groupby('month')['y'].mean().to_dict()
        
        # Detectar padrões
        weekday_cv = np.std(list(weekday_avg.values())) / np.mean(list(weekday_avg.values()))
        monthly_cv = np.std(list(monthly_avg.values())) / np.mean(list(monthly_avg.values()))
        
        return {
            "seasonality_detected": weekday_cv > 0.2 or monthly_cv > 0.2,
            "weekday_patterns": weekday_avg,
            "monthly_patterns": monthly_avg,
            "weekday_variation": weekday_cv,
            "monthly_variation": monthly_cv,
            "insights": self._generate_seasonality_insights(weekday_avg, monthly_avg)
        }
    
    def _generate_seasonality_insights(
        self, 
        weekday_avg: Dict[str, float], 
        monthly_avg: Dict[str, float]
    ) -> List[str]:
        """Gera insights sobre padrões sazonais."""
        
        insights = []
        
        # Análise de dias da semana
        if weekday_avg:
            max_day = max(weekday_avg.items(), key=lambda x: x[1])
            min_day = min(weekday_avg.items(), key=lambda x: x[1])
            
            if max_day[1] > min_day[1] * 1.5:
                insights.append(f"Gastos são {max_day[1]/min_day[1]:.1f}x maiores às {max_day[0]}s")
        
        # Análise de meses
        if monthly_avg:
            max_month = max(monthly_avg.items(), key=lambda x: x[1])
            min_month = min(monthly_avg.items(), key=lambda x: x[1])
            
            if max_month[1] > min_month[1] * 1.3:
                insights.append(f"Pico de gastos em {max_month[0]} (R$ {max_month[1]:,.2f})")
        
        return insights


# Global forecaster instance
financial_forecaster = FinancialForecaster()

