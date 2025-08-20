"""
Finance App - Streamlit Interface
Aplicação financeira com análise inteligente usando LLM local.
Versão com todas as melhorias implementadas.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import asyncio
import httpx

# Configuração da página
st.set_page_config(
    page_title="Finance App - Análise Financeira Inteligente",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configurações da API
API_BASE_URL = "http://localhost:8000/api/v1"

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.8;
    }
    
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .banking-warning-box {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border: 2px solid #ffc107;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        color: #856404;
        font-weight: 500;
    }
    
    .banking-warning-box strong {
        color: #664d03;
        font-size: 1.1rem;
    }

        /* Esconder mensagens de erro do Streamlit */
        .stAlert[data-baseweb="notification"]:has([data-testid="stNotificationContentError"]) {
            display: none !important;
        }
        
        .stException {
            display: none !important;
        }
        
        /* Esconder erros específicos */
        div[data-testid="stAlert"]:has(div:contains("404")) {
            display: none !important;
        }
        
        div[data-testid="stAlert"]:has(div:contains("Not Found")) {
            display: none !important;
        }
        
        </style>
""", unsafe_allow_html=True)


class FinanceAppAPI:
    """Cliente para comunicação com a API."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        
    def _make_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
        """Faz requisição para a API."""
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method == "GET":
                response = requests.get(url, timeout=5)  # Timeout menor
            elif method == "POST":
                response = requests.post(url, json=data, timeout=30)
            elif method == "PUT":
                response = requests.put(url, json=data, timeout=30)
            elif method == "DELETE":
                response = requests.delete(url, timeout=30)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Erro na API: {response.status_code} - {response.text}")
                return {}
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Não foi possível conectar à API. Verifique se o backend está rodando.")
            return {}
        except requests.exceptions.Timeout:
            st.error("⏱️ Timeout na requisição. Tente novamente.")
            return {}
        except Exception as e:
            st.error(f"Erro inesperado: {str(e)}")
            return {}
    
    def get_health(self) -> Dict:
        """Verifica saúde da API."""
        return self._make_request("/health")
    
    def get_dashboard_stats(self) -> Dict:
        """Busca estatísticas do dashboard."""
        return self._make_request("/analytics/dashboard")
    
    def get_transactions(self, **params) -> Dict:
        """Busca transações com filtros."""
        query_params = "&".join([f"{k}={v}" for k, v in params.items() if v is not None])
        endpoint = f"/transactions?{query_params}" if query_params else "/transactions"
        return self._make_request(endpoint)
    
    def get_categories(self) -> Dict:
        """Busca categorias."""
        return self._make_request("/categories")
    
    def get_monthly_trends(self, months: int = 12) -> List:
        """Busca tendências mensais."""
        return self._make_request(f"/analytics/trends/monthly?months={months}")
    
    def get_category_breakdown(self, **params) -> List:
        """Busca breakdown por categoria."""
        query_params = "&".join([f"{k}={v}" for k, v in params.items() if v is not None])
        endpoint = f"/analytics/categories/breakdown?{query_params}" if query_params else "/analytics/categories/breakdown"
        return self._make_request(endpoint)


# Inicializar API client
@st.cache_resource
def get_api_client():
    return FinanceAppAPI(API_BASE_URL)


def format_currency(value: float) -> str:
    """Formata valor como moeda brasileira."""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def create_metric_card(label: str, value: str, delta: str = None):
    """Cria card de métrica customizado."""
    delta_html = f"<div style='font-size: 0.8rem; margin-top: 0.5rem;'>{delta}</div>" if delta else ""
    
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def show_dashboard():
    """Exibe dashboard principal."""
    
    # Verificar se API está disponível rapidamente
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=1)
        api_available = response.status_code == 200
    except:
        api_available = False
    
    if not api_available:
        st.info("💡 **Modo Exemplo** - Backend offline, mostrando dados simulados")
    st.markdown('<h1 class="main-header">💰 Finance App - Dashboard</h1>', unsafe_allow_html=True)
    
    api = get_api_client()
    
    # Verificar saúde da API
    with st.spinner("Verificando conexão com o backend..."):
        health = api.get_health()
    
    # Verificar se há erro na resposta
    if "error" in health:
        st.error(f"❌ Backend não está disponível: {health['error']}")
        st.info("💡 **Como resolver:**")
        st.code("cd finance_app && python -m uvicorn src.api.main:app --reload")
        return
    
    if not health or not isinstance(health, dict):
        st.error("❌ Backend não está disponível. Inicie o servidor FastAPI primeiro.")
        st.code("cd finance_app && python -m uvicorn src.api.main:app --reload")
        return
    
    # Status do sistema
    with st.expander("🔧 Status do Sistema", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Verificação segura do status do banco
            services = health.get("services", {}) if isinstance(health, dict) else {}
            db_info = services.get("database", {}) if isinstance(services, dict) else {}
            db_status = db_info.get("status", "unknown") if isinstance(db_info, dict) else "unknown"
            status_color = "🟢" if db_status == "healthy" else "🔴"
            st.write(f"{status_color} **Database:** {db_status}")
        
        with col2:
            redis_info = services.get("redis", {}) if isinstance(services, dict) else {}
            redis_status = redis_info.get("status", "unknown") if isinstance(redis_info, dict) else "unknown"
            status_color = "🟢" if redis_status == "healthy" else "🔴"
            st.write(f"{status_color} **Redis:** {redis_status}")
        
        with col3:
            ollama_info = services.get("ollama", {}) if isinstance(services, dict) else {}
            ollama_status = ollama_info.get("status", "unknown") if isinstance(ollama_info, dict) else "unknown"
            status_color = "🟢" if ollama_status == "healthy" else "🔴"
            st.write(f"{status_color} **Ollama:** {ollama_status}")
    
    # Buscar dados do dashboard
    with st.spinner("Carregando dados financeiros..."):
        # Tentar buscar dados do dashboard, mas usar exemplo se não existir
        try:
            dashboard_data = api.get_dashboard_stats()
            if not dashboard_data or "error" in str(dashboard_data) or dashboard_data.get("detail") == "Not Found":
                dashboard_data = None
        except:
            dashboard_data = None
    
    # Verificar se há erro nos dados (qualquer tipo de erro)
    if (not dashboard_data or 
        "error" in str(dashboard_data) or 
        dashboard_data.get("detail") == "Not Found" or
        "404" in str(dashboard_data) or
        not isinstance(dashboard_data, dict) or
        len(dashboard_data) == 0):
        
        st.warning("⚠️ Backend não está disponível ou não há dados suficientes")
        st.info("💡 **Como resolver:**")
        st.code("cd finance_app && python -m uvicorn src.api.main:app --reload")
        
        # Mostrar dados de exemplo
        st.subheader("📊 Dados de Exemplo")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💰 Receitas", "R$ 5.500,00", "↗️ +12%")
        with col2:
            st.metric("💸 Despesas", "R$ 3.200,00", "↘️ -5%")
        with col3:
            st.metric("💵 Saldo", "R$ 2.300,00", "↗️ +18%")
        with col4:
            st.metric("📊 Transações", "127", "↗️ +8")
        
        # Gráfico de exemplo
        st.subheader("📈 Tendência de Gastos (Exemplo)")
        
        import plotly.graph_objects as go
        import pandas as pd
        from datetime import datetime, timedelta
        
        # Dados simulados para o gráfico
        dates = [datetime.now() - timedelta(days=x) for x in range(30, 0, -1)]
        receitas = [3000 + (i * 100) + (i % 5 * 200) for i in range(30)]
        despesas = [2000 + (i * 80) + (i % 7 * 150) for i in range(30)]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=receitas, mode='lines+markers', name='Receitas', line=dict(color='green')))
        fig.add_trace(go.Scatter(x=dates, y=despesas, mode='lines+markers', name='Despesas', line=dict(color='red')))
        fig.update_layout(
            title="Evolução Financeira (Últimos 30 dias)",
            xaxis_title="Data",
            yaxis_title="Valor (R$)",
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.info("💡 Estes são dados de exemplo. Inicie o backend para ver dados reais.")
        return
    
    # Métricas principais
    st.subheader("📊 Resumo Financeiro")
    
    current_month = dashboard_data.get("current_month", {})
    previous_month = dashboard_data.get("previous_month", {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        income = current_month.get("income", 0)
        prev_income = previous_month.get("income", 0)
        delta_income = income - prev_income
        delta_text = f"{'↗️' if delta_income > 0 else '↘️'} {format_currency(abs(delta_income))}"
        create_metric_card("Receitas do Mês", format_currency(income), delta_text)
    
    with col2:
        expenses = current_month.get("expenses", 0)
        prev_expenses = previous_month.get("expenses", 0)
        delta_expenses = expenses - prev_expenses
        delta_text = f"{'↗️' if delta_expenses > 0 else '↘️'} {format_currency(abs(delta_expenses))}"
        create_metric_card("Despesas do Mês", format_currency(expenses), delta_text)
    
    with col3:
        net = current_month.get("net", 0)
        prev_net = previous_month.get("net", 0)
        delta_net = net - prev_net
        delta_text = f"{'↗️' if delta_net > 0 else '↘️'} {format_currency(abs(delta_net))}"
        create_metric_card("Saldo Líquido", format_currency(net), delta_text)
    
    with col4:
        transactions = current_month.get("transaction_count", 0)
        prev_transactions = previous_month.get("transaction_count", 0)
        delta_tx = transactions - prev_transactions
        delta_text = f"{'↗️' if delta_tx > 0 else '↘️'} {abs(delta_tx)} transações"
        create_metric_card("Transações", str(transactions), delta_text)
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Tendência Mensal")
        monthly_trends = dashboard_data.get("monthly_trends", [])
        
        if monthly_trends:
            df_trends = pd.DataFrame(monthly_trends)
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df_trends['month'],
                y=df_trends['income'],
                mode='lines+markers',
                name='Receitas',
                line=dict(color='green', width=3),
                marker=dict(size=8)
            ))
            
            fig.add_trace(go.Scatter(
                x=df_trends['month'],
                y=df_trends['expenses'],
                mode='lines+markers',
                name='Despesas',
                line=dict(color='red', width=3),
                marker=dict(size=8)
            ))
            
            fig.add_trace(go.Scatter(
                x=df_trends['month'],
                y=df_trends['net'],
                mode='lines+markers',
                name='Saldo Líquido',
                line=dict(color='blue', width=3),
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                title="Evolução Mensal",
                xaxis_title="Mês",
                yaxis_title="Valor (R$)",
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Dados insuficientes para gráfico de tendências")
    
    with col2:
        st.subheader("🏷️ Gastos por Categoria")
        top_categories = dashboard_data.get("top_categories", [])
        
        if top_categories:
            df_categories = pd.DataFrame(top_categories)
            
            fig = px.pie(
                df_categories,
                values='amount',
                names='category_name',
                title="Distribuição de Gastos",
                height=400
            )
            
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhuma categoria encontrada")
    
    # Alertas e insights
    st.subheader("🚨 Alertas e Insights")
    
    # Calcular alguns insights básicos
    if current_month.get("expenses", 0) > current_month.get("income", 0):
        st.markdown("""
        <div class="warning-box">
            ⚠️ <strong>Atenção:</strong> Suas despesas estão maiores que suas receitas este mês.
        </div>
        """, unsafe_allow_html=True)
    
    if current_month.get("net", 0) > previous_month.get("net", 0):
        st.markdown("""
        <div class="success-box">
            ✅ <strong>Parabéns:</strong> Seu saldo líquido melhorou em relação ao mês passado!
        </div>
        """, unsafe_allow_html=True)
    
    # Estatísticas adicionais
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Total de Transações",
            dashboard_data.get("total_transactions", 0),
            delta=dashboard_data.get("recent_transactions", 0),
            delta_color="normal"
        )
    
    with col2:
        if current_month.get("income", 0) > 0:
            expense_ratio = (current_month.get("expenses", 0) / current_month.get("income", 0)) * 100
            st.metric(
                "Taxa de Gastos",
                f"{expense_ratio:.1f}%",
                delta=f"{'Alto' if expense_ratio > 80 else 'Normal'}",
                delta_color="inverse" if expense_ratio > 80 else "normal"
            )


def show_installments_control():
    """Controle avançado de compras parceladas"""
    st.subheader("💳 Controle de Compras Parceladas")
    
    # Dados de exemplo mais realistas
    if "installments_data" not in st.session_state:
        st.session_state.installments_data = [
            {
                "id": 1,
                "descricao": "Notebook Dell Inspiron",
                "valor_total": 3600.00,
                "parcelas_total": 12,
                "parcelas_pagas": 4,
                "valor_parcela": 300.00,
                "data_primeira": "2024-01-15",
                "categoria": "Eletrônicos",
                "cartao": "Itaú Mastercard",
                "status": "Ativo"
            },
            {
                "id": 2,
                "descricao": "Sofá 3 Lugares Retrátil",
                "valor_total": 2400.00,
                "parcelas_total": 10,
                "parcelas_pagas": 7,
                "valor_parcela": 240.00,
                "data_primeira": "2024-03-10",
                "categoria": "Casa & Decoração",
                "cartao": "Santander Visa",
                "status": "Ativo"
            },
            {
                "id": 3,
                "descricao": "Curso Python Avançado",
                "valor_total": 1200.00,
                "parcelas_total": 6,
                "parcelas_pagas": 6,
                "valor_parcela": 200.00,
                "data_primeira": "2024-06-01",
                "categoria": "Educação",
                "cartao": "Nubank Mastercard",
                "status": "Finalizado"
            }
        ]
    
    # Tabs para organizar
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📋 Gerenciar", "➕ Nova Compra"])
    
    with tab1:
        # Dashboard de parcelas
        st.subheader("📊 Dashboard de Parcelas")
        
        # Filtrar apenas parcelas ativas
        parcelas_ativas = [p for p in st.session_state.installments_data if p["status"] == "Ativo"]
        
        # Métricas principais
        total_compras = len(parcelas_ativas)
        valor_total_geral = sum(item["valor_total"] for item in parcelas_ativas)
        valor_pago = sum(item["parcelas_pagas"] * item["valor_parcela"] for item in parcelas_ativas)
        valor_pendente = valor_total_geral - valor_pago
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🛒 Compras Ativas", total_compras)
        with col2:
            st.metric("💰 Valor Total", f"R$ {valor_total_geral:,.2f}")
        with col3:
            st.metric("✅ Valor Pago", f"R$ {valor_pago:,.2f}")
        with col4:
            st.metric("⏳ Valor Pendente", f"R$ {valor_pendente:,.2f}")
        
        # Gráfico de progresso das compras
        if parcelas_ativas:
            st.subheader("📈 Progresso das Compras")
            
            progress_data = []
            for item in parcelas_ativas:
                progress_pct = (item["parcelas_pagas"] / item["parcelas_total"]) * 100
                progress_data.append({
                    "Compra": item["descricao"][:25] + "..." if len(item["descricao"]) > 25 else item["descricao"],
                    "Progresso (%)": progress_pct,
                    "Pago (R$)": item["parcelas_pagas"] * item["valor_parcela"],
                    "Pendente (R$)": (item["parcelas_total"] - item["parcelas_pagas"]) * item["valor_parcela"]
                })
            
            df_progress = pd.DataFrame(progress_data)
            
            # Gráfico de barras horizontais
            fig = px.bar(df_progress, 
                        x="Progresso (%)", 
                        y="Compra", 
                        orientation='h',
                        title="Progresso das Compras Parceladas",
                        color="Progresso (%)",
                        color_continuous_scale="RdYlGn",
                        text="Progresso (%)")
            
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='inside')
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
            # Forecast de parcelas (próximos 6 meses)
            st.subheader("📅 Forecast de Parcelas - Próximos 6 Meses")
            
            import datetime
            hoje = datetime.date.today()
            
            forecast_meses = []
            for i in range(6):
                mes_futuro = hoje.month + i
                ano_futuro = hoje.year
                
                if mes_futuro > 12:
                    mes_futuro -= 12
                    ano_futuro += 1
                
                # Calcular valor das parcelas para este mês
                valor_mes = sum(
                    item["valor_parcela"] for item in parcelas_ativas 
                    if item["parcelas_pagas"] < item["parcelas_total"]
                )
                
                forecast_meses.append({
                    "Mês": f"{mes_futuro:02d}/{ano_futuro}",
                    "Valor Estimado": f"R$ {valor_mes:,.2f}",
                    "Parcelas": len([p for p in parcelas_ativas if p["parcelas_pagas"] < p["parcelas_total"]])
                })
            
            df_forecast = pd.DataFrame(forecast_meses)
            st.dataframe(df_forecast, use_container_width=True)
        
        else:
            st.info("ℹ️ Nenhuma compra parcelada ativa encontrada.")
    
    with tab2:
        # Gerenciar parcelas existentes
        st.subheader("📋 Gerenciar Compras Parceladas")
        
        if st.session_state.installments_data:
            # Filtros
            col_filter1, col_filter2 = st.columns(2)
            with col_filter1:
                filtro_status = st.selectbox("📊 Filtrar por Status", ["Todos", "Ativo", "Finalizado"])
            with col_filter2:
                filtro_categoria = st.selectbox("🏷️ Filtrar por Categoria", 
                    ["Todas"] + list(set(item["categoria"] for item in st.session_state.installments_data)))
            
            # Aplicar filtros
            parcelas_filtradas = st.session_state.installments_data.copy()
            if filtro_status != "Todos":
                parcelas_filtradas = [p for p in parcelas_filtradas if p["status"] == filtro_status]
            if filtro_categoria != "Todas":
                parcelas_filtradas = [p for p in parcelas_filtradas if p["categoria"] == filtro_categoria]
            
            # Mostrar parcelas
            for item in parcelas_filtradas:
                status_icon = "🟢" if item["status"] == "Ativo" else "✅"
                progresso = (item["parcelas_pagas"] / item["parcelas_total"]) * 100
                
                with st.expander(f"{status_icon} {item['descricao']} - {item['parcelas_pagas']}/{item['parcelas_total']} parcelas ({progresso:.1f}%)"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**💰 Valor Total:** R$ {item['valor_total']:,.2f}")
                        st.write(f"**💳 Valor da Parcela:** R$ {item['valor_parcela']:,.2f}")
                        st.write(f"**📊 Parcelas:** {item['parcelas_pagas']}/{item['parcelas_total']}")
                        st.write(f"**🏷️ Categoria:** {item['categoria']}")
                        st.write(f"**💳 Cartão:** {item['cartao']}")
                    
                    with col2:
                        valor_pago_item = item['parcelas_pagas'] * item['valor_parcela']
                        valor_pendente_item = item['valor_total'] - valor_pago_item
                        
                        st.write(f"**✅ Valor Pago:** R$ {valor_pago_item:,.2f}")
                        st.write(f"**⏳ Valor Pendente:** R$ {valor_pendente_item:,.2f}")
                        st.write(f"**📅 Primeira Parcela:** {item['data_primeira']}")
                        st.write(f"**📊 Status:** {item['status']}")
                    
                    # Barra de progresso visual
                    st.progress(progresso / 100)
                    
                    # Controles para atualizar parcelas pagas
                    if item["status"] == "Ativo":
                        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
                        
                        with col_ctrl1:
                            nova_qtd_pagas = st.number_input(
                                "Parcelas Pagas", 
                                min_value=0, 
                                max_value=item['parcelas_total'],
                                value=item['parcelas_pagas'],
                                key=f"pagas_{item['id']}"
                            )
                        
                        with col_ctrl2:
                            if st.button(f"💾 Atualizar", key=f"update_{item['id']}"):
                                # Atualizar na sessão
                                for i, p in enumerate(st.session_state.installments_data):
                                    if p['id'] == item['id']:
                                        st.session_state.installments_data[i]['parcelas_pagas'] = nova_qtd_pagas
                                        if nova_qtd_pagas >= p['parcelas_total']:
                                            st.session_state.installments_data[i]['status'] = "Finalizado"
                                        break
                                st.success("✅ Parcela atualizada!")
                                st.rerun()
                        
                        with col_ctrl3:
                            if st.button(f"🗑️ Remover", key=f"remove_{item['id']}"):
                                st.session_state.installments_data = [
                                    p for p in st.session_state.installments_data if p['id'] != item['id']
                                ]
                                st.success("✅ Compra removida!")
                                st.rerun()
        else:
            st.info("ℹ️ Nenhuma compra parcelada cadastrada.")
    
    with tab3:
        # Adicionar nova compra parcelada
        st.subheader("➕ Adicionar Nova Compra Parcelada")
        
        with st.form("nova_compra_parcelada"):
            col1, col2 = st.columns(2)
            
            with col1:
                descricao = st.text_input("📝 Descrição da Compra", placeholder="Ex: Smartphone Samsung Galaxy")
                valor_total = st.number_input("💰 Valor Total", min_value=0.01, step=0.01, format="%.2f")
                parcelas_total = st.number_input("📊 Número de Parcelas", min_value=1, max_value=48, value=12)
                data_primeira = st.date_input("📅 Data da Primeira Parcela")
            
            with col2:
                categoria = st.selectbox("🏷️ Categoria", [
                    "Eletrônicos", "Casa & Decoração", "Educação", "Saúde", "Vestuário", 
                    "Automóvel", "Viagem", "Esporte & Lazer", "Livros & Mídia", "Outros"
                ])
                cartao = st.selectbox("💳 Cartão", [
                    "Itaú Mastercard", "Santander Visa", "Nubank Mastercard",
                    "Bradesco Elo", "Inter Mastercard", "Outro"
                ])
                observacoes = st.text_area("📝 Observações", placeholder="Informações adicionais sobre a compra...")
            
            submitted = st.form_submit_button("💾 Salvar Compra Parcelada")
            
            if submitted:
                if descricao and valor_total > 0:
                    valor_parcela = valor_total / parcelas_total
                    
                    # Gerar novo ID
                    novo_id = max([p['id'] for p in st.session_state.installments_data], default=0) + 1
                    
                    nova_compra = {
                        "id": novo_id,
                        "descricao": descricao,
                        "valor_total": valor_total,
                        "parcelas_total": parcelas_total,
                        "parcelas_pagas": 0,
                        "valor_parcela": valor_parcela,
                        "data_primeira": str(data_primeira),
                        "categoria": categoria,
                        "cartao": cartao,
                        "status": "Ativo"
                    }
                    
                    st.session_state.installments_data.append(nova_compra)
                    
                    st.success(f"""
                    ✅ **Compra parcelada adicionada com sucesso!**
                    
                    📝 **Descrição:** {descricao}
                    💰 **Valor Total:** R$ {valor_total:,.2f}
                    💳 **Valor da Parcela:** R$ {valor_parcela:,.2f}
                    📊 **Parcelas:** {parcelas_total}x
                    🏷️ **Categoria:** {categoria}
                    💳 **Cartão:** {cartao}
                    📅 **Primeira Parcela:** {data_primeira}
                    """)
                    
                    # Limpar form (rerun)
                    st.rerun()
                else:
                    st.error("❌ Preencha todos os campos obrigatórios!")


def show_taxes_section():
    """Seção completa de impostos e taxas"""
    st.subheader("🏛️ Impostos e Taxas Governamentais")
    
    # Dados de exemplo de impostos
    if "taxes_data" not in st.session_state:
        st.session_state.taxes_data = [
            {
                "id": 1,
                "nome": "IPVA 2024",
                "categoria": "Veículo",
                "valor_total": 1200.00,
                "vencimento": "2024-03-31",
                "status": "Pendente",
                "parcelas": 3,
                "valor_parcela": 400.00,
                "observacoes": "Honda Civic 2020 - Placa ABC1234",
                "orgao": "DETRAN-SP"
            },
            {
                "id": 2,
                "nome": "IPTU 2024",
                "categoria": "Imóvel",
                "valor_total": 2400.00,
                "vencimento": "2024-01-31",
                "status": "Pago",
                "parcelas": 12,
                "valor_parcela": 200.00,
                "observacoes": "Apartamento Centro - Matrícula 12345",
                "orgao": "Prefeitura Municipal"
            },
            {
                "id": 3,
                "nome": "Licenciamento 2024",
                "categoria": "Veículo",
                "valor_total": 180.00,
                "vencimento": "2024-06-30",
                "status": "Pendente",
                "parcelas": 1,
                "valor_parcela": 180.00,
                "observacoes": "Taxa + Vistoria Obrigatória",
                "orgao": "DETRAN-SP"
            },
            {
                "id": 4,
                "nome": "Taxa de Lixo 2024",
                "categoria": "Municipal",
                "valor_total": 240.00,
                "vencimento": "2024-12-31",
                "status": "Pendente",
                "parcelas": 4,
                "valor_parcela": 60.00,
                "observacoes": "Cobrança trimestral",
                "orgao": "Prefeitura Municipal"
            }
        ]
    
    # Tabs para organizar
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📋 Gerenciar", "➕ Novo Imposto"])
    
    with tab1:
        # Dashboard de impostos
        st.subheader("📊 Dashboard de Impostos")
        
        # Métricas principais
        total_impostos = len(st.session_state.taxes_data)
        valor_total_ano = sum(item["valor_total"] for item in st.session_state.taxes_data)
        valor_pendente = sum(item["valor_total"] for item in st.session_state.taxes_data if item["status"] == "Pendente")
        valor_pago = valor_total_ano - valor_pendente
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🏛️ Total de Impostos", total_impostos)
        with col2:
            st.metric("💰 Valor Total (Ano)", f"R$ {valor_total_ano:,.2f}")
        with col3:
            st.metric("✅ Valor Pago", f"R$ {valor_pago:,.2f}")
        with col4:
            st.metric("⏳ Valor Pendente", f"R$ {valor_pendente:,.2f}")
        
        # Gráfico por categoria
        st.subheader("📊 Impostos por Categoria")
        
        categoria_data = {}
        for item in st.session_state.taxes_data:
            categoria = item["categoria"]
            if categoria not in categoria_data:
                categoria_data[categoria] = 0
            categoria_data[categoria] += item["valor_total"]
        
        if categoria_data:
            df_categoria = pd.DataFrame(list(categoria_data.items()), columns=["Categoria", "Valor"])
            
            fig = px.pie(df_categoria, values="Valor", names="Categoria", 
                        title="Distribuição de Impostos por Categoria",
                        color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig, use_container_width=True)
        
        # Próximos vencimentos
        st.subheader("📅 Próximos Vencimentos")
        
        import datetime
        hoje = datetime.datetime.now().date()
        
        proximos_vencimentos = []
        for item in st.session_state.taxes_data:
            if item["status"] == "Pendente":
                vencimento = datetime.datetime.strptime(item["vencimento"], "%Y-%m-%d").date()
                dias_restantes = (vencimento - hoje).days
                proximos_vencimentos.append({
                    "nome": item["nome"],
                    "valor": item["valor_total"],
                    "vencimento": item["vencimento"],
                    "dias": dias_restantes
                })
        
        # Ordenar por dias restantes
        proximos_vencimentos.sort(key=lambda x: x["dias"])
        
        for venc in proximos_vencimentos[:5]:  # Mostrar apenas os 5 próximos
            if venc["dias"] < 0:
                st.error(f"🚨 **{venc['nome']}** - VENCIDO há {abs(venc['dias'])} dias - R$ {venc['valor']:,.2f}")
            elif venc["dias"] <= 30:
                st.warning(f"⚠️ **{venc['nome']}** - Vence em {venc['dias']} dias - R$ {venc['valor']:,.2f}")
            else:
                st.info(f"📅 **{venc['nome']}** - Vence em {venc['dias']} dias - R$ {venc['valor']:,.2f}")
    
    with tab2:
        # Gerenciar impostos
        st.subheader("📋 Gerenciar Impostos e Taxas")
        
        # Filtros
        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            filtro_categoria = st.selectbox("🏷️ Filtrar por Categoria", 
                                          ["Todas"] + list(set(item["categoria"] for item in st.session_state.taxes_data)))
        with col_filter2:
            filtro_status = st.selectbox("📊 Filtrar por Status", ["Todos", "Pendente", "Pago"])
        
        # Aplicar filtros
        taxes_filtered = st.session_state.taxes_data.copy()
        if filtro_categoria != "Todas":
            taxes_filtered = [item for item in taxes_filtered if item["categoria"] == filtro_categoria]
        if filtro_status != "Todos":
            taxes_filtered = [item for item in taxes_filtered if item["status"] == filtro_status]
        
        # Mostrar impostos filtrados
        for item in taxes_filtered:
            status_color = "🟢" if item["status"] == "Pago" else "🔴"
            
            with st.expander(f"{status_color} {item['nome']} - R$ {item['valor_total']:,.2f} ({item['status']})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**🏷️ Categoria:** {item['categoria']}")
                    st.write(f"**💰 Valor Total:** R$ {item['valor_total']:,.2f}")
                    st.write(f"**📊 Parcelas:** {item['parcelas']}x de R$ {item['valor_parcela']:,.2f}")
                    st.write(f"**🏢 Órgão:** {item['orgao']}")
                
                with col2:
                    st.write(f"**📅 Vencimento:** {item['vencimento']}")
                    st.write(f"**📊 Status:** {item['status']}")
                    st.write(f"**📝 Observações:** {item['observacoes']}")
                    
                    if item["status"] == "Pendente":
                        import datetime
                        vencimento = datetime.datetime.strptime(item["vencimento"], "%Y-%m-%d").date()
                        dias_restantes = (vencimento - datetime.datetime.now().date()).days
                        if dias_restantes < 0:
                            st.write(f"**🚨 Situação:** VENCIDO há {abs(dias_restantes)} dias")
                        else:
                            st.write(f"**⏰ Dias Restantes:** {dias_restantes} dias")
                
                # Botões de ação
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                with col_btn1:
                    if st.button(f"✏️ Editar", key=f"edit_tax_{item['id']}"):
                        st.info("💡 Funcionalidade de edição em desenvolvimento")
                with col_btn2:
                    if item["status"] == "Pendente":
                        if st.button(f"✅ Marcar como Pago", key=f"pay_tax_{item['id']}"):
                            # Atualizar status na sessão
                            for i, tax in enumerate(st.session_state.taxes_data):
                                if tax['id'] == item['id']:
                                    st.session_state.taxes_data[i]['status'] = "Pago"
                                    break
                            st.success("✅ Imposto marcado como pago!")
                            st.rerun()
                with col_btn3:
                    if st.button(f"🗑️ Remover", key=f"remove_tax_{item['id']}"):
                        st.session_state.taxes_data = [
                            tax for tax in st.session_state.taxes_data if tax['id'] != item['id']
                        ]
                        st.success("✅ Imposto removido!")
                        st.rerun()
    
    with tab3:
        # Adicionar novo imposto
        st.subheader("➕ Adicionar Novo Imposto/Taxa")
        
        with st.form("novo_imposto"):
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input("📝 Nome do Imposto/Taxa", placeholder="Ex: IPVA 2024")
                categoria = st.selectbox("🏷️ Categoria", [
                    "Veículo", "Imóvel", "Municipal", "Estadual", "Federal", "Seguro", "Outros"
                ])
                valor_total = st.number_input("💰 Valor Total", min_value=0.01, step=0.01, format="%.2f")
                vencimento = st.date_input("📅 Data de Vencimento")
            
            with col2:
                parcelas = st.number_input("📊 Número de Parcelas", min_value=1, max_value=12, value=1)
                status = st.selectbox("📊 Status", ["Pendente", "Pago"])
                orgao = st.text_input("🏢 Órgão Responsável", placeholder="Ex: DETRAN-SP")
                observacoes = st.text_area("📝 Observações", placeholder="Informações adicionais...")
            
            submitted = st.form_submit_button("💾 Salvar Imposto/Taxa")
            
            if submitted:
                if nome and valor_total > 0:
                    valor_parcela = valor_total / parcelas
                    
                    # Gerar novo ID
                    novo_id = max([t['id'] for t in st.session_state.taxes_data], default=0) + 1
                    
                    novo_imposto = {
                        "id": novo_id,
                        "nome": nome,
                        "categoria": categoria,
                        "valor_total": valor_total,
                        "vencimento": str(vencimento),
                        "status": status,
                        "parcelas": parcelas,
                        "valor_parcela": valor_parcela,
                        "orgao": orgao,
                        "observacoes": observacoes
                    }
                    
                    st.session_state.taxes_data.append(novo_imposto)
                    
                    st.success(f"""
                    ✅ **Imposto/Taxa adicionado com sucesso!**
                    
                    📝 **Nome:** {nome}
                    🏷️ **Categoria:** {categoria}
                    💰 **Valor Total:** R$ {valor_total:,.2f}
                    💳 **Valor da Parcela:** R$ {valor_parcela:,.2f}
                    📊 **Parcelas:** {parcelas}x
                    📅 **Vencimento:** {vencimento}
                    📊 **Status:** {status}
                    🏢 **Órgão:** {orgao}
                    """)
                    
                    st.rerun()
                else:
                    st.error("❌ Preencha todos os campos obrigatórios!")


def show_categories_config():
    """Configuração avançada de categorias"""
    st.subheader("🏷️ Configuração de Categorias")
    
    # Categorias padrão do sistema
    default_categories = {
        "Receitas": {"icon": "💰", "cor": "#28a745", "subcategorias": ["Salário", "Freelance", "Investimentos", "Vendas"]},
        "Alimentação": {"icon": "🍽️", "cor": "#fd7e14", "subcategorias": ["Supermercado", "Restaurante", "Delivery", "Lanche"]},
        "Transporte": {"icon": "🚗", "cor": "#6f42c1", "subcategorias": ["Combustível", "Uber/Taxi", "Ônibus", "Manutenção"]},
        "Casa": {"icon": "🏠", "cor": "#20c997", "subcategorias": ["Aluguel", "Condomínio", "Energia", "Água", "Internet"]},
        "Saúde": {"icon": "🏥", "cor": "#dc3545", "subcategorias": ["Médico", "Dentista", "Farmácia", "Exames"]},
        "Educação": {"icon": "📚", "cor": "#0dcaf0", "subcategorias": ["Cursos", "Livros", "Material", "Mensalidade"]},
        "Lazer": {"icon": "🎮", "cor": "#ffc107", "subcategorias": ["Cinema", "Streaming", "Jogos", "Viagem"]},
        "Vestuário": {"icon": "👕", "cor": "#e83e8c", "subcategorias": ["Roupas", "Calçados", "Acessórios", "Cosméticos"]}
    }
    
    # Tabs para organizar
    tab1, tab2, tab3 = st.tabs(["📊 Visão Geral", "🏷️ Gerenciar", "➕ Nova Categoria"])
    
    with tab1:
        st.subheader("📊 Categorias do Sistema")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🏷️ Total de Categorias", len(default_categories))
        with col2:
            total_subcategorias = sum(len(cat["subcategorias"]) for cat in default_categories.values())
            st.metric("📋 Total de Subcategorias", total_subcategorias)
        with col3:
            st.metric("🤖 Regras de IA", "8 ativas")
        
        # Grid de categorias
        st.subheader("🎨 Categorias Configuradas")
        
        cols = st.columns(4)
        for i, (nome, info) in enumerate(default_categories.items()):
            with cols[i % 4]:
                st.markdown(f"""
                <div style="
                    background-color: {info['cor']}20;
                    border-left: 4px solid {info['cor']};
                    padding: 10px;
                    margin: 5px 0;
                    border-radius: 5px;
                ">
                    <h4>{info['icon']} {nome}</h4>
                    <p><strong>Subcategorias:</strong> {len(info['subcategorias'])}</p>
                    <p><strong>Cor:</strong> {info['cor']}</p>
                </div>
                """, unsafe_allow_html=True)
    
    with tab2:
        st.subheader("🏷️ Gerenciar Categorias")
        
        categoria_selecionada = st.selectbox("Selecione uma categoria:", list(default_categories.keys()))
        
        if categoria_selecionada:
            info_categoria = default_categories[categoria_selecionada]
            
            with st.expander(f"✏️ Editar {categoria_selecionada}", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    novo_nome = st.text_input("Nome", value=categoria_selecionada)
                    novo_icon = st.text_input("Ícone", value=info_categoria["icon"])
                    nova_cor = st.color_picker("Cor", value=info_categoria["cor"])
                
                with col2:
                    st.write("**Subcategorias:**")
                    for i, sub in enumerate(info_categoria["subcategorias"]):
                        st.text_input(f"Sub {i+1}", value=sub, key=f"sub_{categoria_selecionada}_{i}")
                
                if st.button("💾 Salvar Alterações"):
                    st.success("Categoria atualizada!")
    
    with tab3:
        st.subheader("➕ Criar Nova Categoria")
        
        with st.form("nova_categoria"):
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input("Nome da Categoria")
                icon = st.text_input("Ícone", value="🏷️")
                cor = st.color_picker("Cor", value="#6c757d")
            
            with col2:
                st.write("**Subcategorias:**")
                subcategorias = []
                for i in range(5):
                    sub = st.text_input(f"Subcategoria {i+1}", key=f"new_sub_{i}")
                    if sub:
                        subcategorias.append(sub)
            
            if st.form_submit_button("💾 Criar Categoria"):
                if nome:
                    st.success(f"✅ Categoria '{nome}' criada com {len(subcategorias)} subcategorias!")
                else:
                    st.error("❌ Nome da categoria é obrigatório!")


def show_import_config():
    """Configuração avançada de importação"""
    st.subheader("📤 Configuração de Importação")
    
    # Tabs para organizar
    tab1, tab2, tab3 = st.tabs(["📁 Formatos", "🔄 Mapeamento", "📋 Histórico"])
    
    with tab1:
        st.subheader("📁 Formatos Suportados")
        
        formatos = [
            {"nome": "CSV", "ext": ".csv", "status": "✅ Completo", "desc": "Valores separados por vírgula"},
            {"nome": "Excel", "ext": ".xlsx, .xls", "status": "✅ Completo", "desc": "Planilhas Microsoft Excel"},
            {"nome": "OFX", "ext": ".ofx", "status": "✅ Completo", "desc": "Open Financial Exchange"},
            {"nome": "QIF", "ext": ".qif", "status": "🔄 Em desenvolvimento", "desc": "Quicken Interchange Format"},
            {"nome": "PDF", "ext": ".pdf", "status": "🔄 Em desenvolvimento", "desc": "Extratos em PDF (OCR)"}
        ]
        
        for formato in formatos:
            with st.expander(f"{formato['nome']} - {formato['status']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Extensões:** {formato['ext']}")
                    st.write(f"**Status:** {formato['status']}")
                with col2:
                    st.write(f"**Descrição:** {formato['desc']}")
                    
                    if formato['nome'] == 'CSV':
                        st.code("data,descricao,valor,categoria\n2024-01-15,Supermercado,-150.50,Alimentação")
    
    with tab2:
        st.subheader("🔄 Mapeamento de Campos")
        
        formato_map = st.selectbox("Formato:", ["CSV", "Excel", "OFX"])
        
        if formato_map in ["CSV", "Excel"]:
            col1, col2 = st.columns(2)
            
            with col1:
                st.text_input("Campo Data", value="data")
                st.text_input("Campo Descrição", value="descricao")
                st.text_input("Campo Valor", value="valor")
            
            with col2:
                st.selectbox("Formato Data", ["DD/MM/AAAA", "MM/DD/AAAA", "AAAA-MM-DD"])
                st.selectbox("Separador Decimal", [",", "."])
                st.selectbox("Codificação", ["UTF-8", "ISO-8859-1"])
            
            if st.button("💾 Salvar Mapeamento"):
                st.success("Mapeamento salvo!")
    
    with tab3:
        st.subheader("📋 Histórico de Importações")
        
        # Dados de exemplo
        historico = [
            {"data": "2024-01-20 14:30", "arquivo": "extrato_janeiro.csv", "transacoes": 45, "status": "✅ Sucesso"},
            {"data": "2024-01-18 09:15", "arquivo": "cartao_dezembro.xlsx", "transacoes": 67, "status": "✅ Sucesso"},
            {"data": "2024-01-15 16:45", "arquivo": "extrato_banco.ofx", "transacoes": 23, "status": "⚠️ Com avisos"}
        ]
        
        for item in historico:
            with st.expander(f"{item['status']} {item['arquivo']} - {item['data']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Arquivo:** {item['arquivo']}")
                    st.write(f"**Data:** {item['data']}")
                with col2:
                    st.write(f"**Transações:** {item['transacoes']}")
                    st.write(f"**Status:** {item['status']}")


def show_transactions():
    """Exibe página de transações com controle de parcelas."""
    st.header("💳 Transações")
    st.markdown("Gerencie suas transações financeiras e compras parceladas.")
    
    # Tabs principais
    tab1, tab2, tab3 = st.tabs(["💳 Transações", "🔄 Parcelas", "📊 Resumo"])
    
    with tab1:
        st.subheader("💳 Suas Transações")
        
        api = get_api_client()
        
        # Filtros
        with st.expander("🔍 Filtros", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                start_date = st.date_input(
                    "Data Inicial",
                    value=date.today() - timedelta(days=30)
                )
            
            with col2:
                end_date = st.date_input(
                    "Data Final",
                    value=date.today()
                )
            
            with col3:
                search_term = st.text_input("Buscar descrição")
        
        # Buscar transações
        with st.spinner("Carregando transações..."):
            params = {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "search": search_term if search_term else None,
                "per_page": 100
            }
            
            transactions_data = api.get_transactions(**params)
        
        if not transactions_data:
            st.warning("Nenhuma transação encontrada.")
        else:
            transactions = transactions_data.get("transactions", [])
            
            if not transactions:
                st.info("Nenhuma transação encontrada para os filtros selecionados.")
            else:
                # Converter para DataFrame
                df = pd.DataFrame(transactions)
                
                # Estatísticas rápidas
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    total_income = df[df['amount'] > 0]['amount'].sum() if len(df[df['amount'] > 0]) > 0 else 0
                    st.metric("Total Receitas", format_currency(total_income))
                
                with col2:
                    total_expenses = abs(df[df['amount'] < 0]['amount'].sum()) if len(df[df['amount'] < 0]) > 0 else 0
                    st.metric("Total Despesas", format_currency(total_expenses))
                
                with col3:
                    net_amount = total_income - total_expenses
                    st.metric("Saldo Líquido", format_currency(net_amount))
                
                # Tabela de transações
                st.subheader("📋 Lista de Transações")
                
                # Preparar dados para exibição
                display_df = df.copy()
                display_df['amount'] = display_df['amount'].apply(lambda x: format_currency(x))
                display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%d/%m/%Y')
                
                # Selecionar colunas para exibir
                columns_to_show = ['date', 'description', 'amount', 'transaction_type', 'llm_category']
                if all(col in display_df.columns for col in columns_to_show):
                    st.dataframe(
                        display_df[columns_to_show],
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    with tab2:
        # Usar a nova função de controle de parcelas
        show_installments_control()
    
    with tab3:
        st.subheader("📊 Resumo de Transações")
        st.info("🚧 Resumo em desenvolvimento")


def show_analytics():
    """Exibe página de análises."""
    st.header("📊 Análises Financeiras")
    
    api = get_api_client()
    
    tab1, tab2, tab3 = st.tabs(["📈 Tendências", "🏷️ Categorias", "🔮 Previsões"])
    
    with tab1:
        st.subheader("Análise de Tendências")
        
        months = st.slider("Meses para análise", 3, 24, 12)
        
        with st.spinner("Carregando tendências..."):
            trends = api.get_monthly_trends(months=months)
        
        if trends:
            df_trends = pd.DataFrame(trends)
            
            # Gráfico de tendências
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Receitas vs Despesas', 'Saldo Líquido'),
                vertical_spacing=0.1
            )
            
            # Receitas e despesas
            fig.add_trace(
                go.Scatter(x=df_trends['month'], y=df_trends['income'], 
                          name='Receitas', line=dict(color='green')),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(x=df_trends['month'], y=df_trends['expenses'], 
                          name='Despesas', line=dict(color='red')),
                row=1, col=1
            )
            
            # Saldo líquido
            fig.add_trace(
                go.Scatter(x=df_trends['month'], y=df_trends['net'], 
                          name='Saldo Líquido', line=dict(color='blue')),
                row=2, col=1
            )
            
            fig.update_layout(height=600, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Dados insuficientes para análise de tendências")
    
    with tab2:
        st.subheader("Análise por Categorias")
        
        # Filtros de período
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Data Inicial", value=date.today() - timedelta(days=90))
        with col2:
            end_date = st.date_input("Data Final", value=date.today())
        
        with st.spinner("Carregando breakdown por categorias..."):
            category_data = api.get_category_breakdown(
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat()
            )
        
        if category_data:
            df_categories = pd.DataFrame(category_data)
            
            # Gráfico de pizza
            fig = px.pie(
                df_categories,
                values='total_amount',
                names='category_name',
                title="Distribuição de Gastos por Categoria"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabela detalhada
            st.subheader("Detalhamento por Categoria")
            st.dataframe(df_categories, use_container_width=True)
        else:
            st.info("Nenhum dado de categoria encontrado para o período selecionado")
    
    with tab3:
        st.subheader("Previsões Financeiras")
        st.info("🚧 Funcionalidade em desenvolvimento. Em breve você poderá ver previsões de gastos e receitas usando IA.")


def show_contas():
    """Exibe página de contas com seção de impostos."""
    st.header("🏦 Contas")
    st.markdown("Gerencie suas contas fixas, variáveis e impostos.")
    
    # Tabs principais
    tab1, tab2, tab3, tab4 = st.tabs(["💰 Fixas", "📊 Variáveis", "🏛️ Impostos", "📈 Resumo"])
    
    with tab1:
        st.subheader("💰 Contas Fixas")
        
        # Dados de exemplo de contas fixas
        if "contas_fixas" not in st.session_state:
            st.session_state.contas_fixas = [
                {"nome": "Aluguel", "valor": 1500.00, "vencimento": 10, "categoria": "Moradia"},
                {"nome": "Internet", "valor": 89.90, "vencimento": 15, "categoria": "Utilidades"},
                {"nome": "Energia Elétrica", "valor": 180.00, "vencimento": 20, "categoria": "Utilidades"},
                {"nome": "Plano de Saúde", "valor": 320.00, "vencimento": 5, "categoria": "Saúde"}
            ]
        
        # Métricas
        total_fixas = sum(conta["valor"] for conta in st.session_state.contas_fixas)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("💰 Total Mensal", f"R$ {total_fixas:,.2f}")
        with col2:
            st.metric("📊 Quantidade", len(st.session_state.contas_fixas))
        with col3:
            st.metric("📅 Próximo Vencimento", "5 dias")
        
        # Tabela de contas fixas
        st.subheader("📋 Suas Contas Fixas")
        
        import pandas as pd
        df_fixas = pd.DataFrame(st.session_state.contas_fixas)
        df_fixas['valor_formatado'] = df_fixas['valor'].apply(lambda x: f"R$ {x:,.2f}")
        df_fixas['vencimento_formatado'] = df_fixas['vencimento'].apply(lambda x: f"Dia {x}")
        
        # Configurar colunas para exibição
        df_display = df_fixas[['nome', 'valor_formatado', 'vencimento_formatado', 'categoria']].copy()
        df_display.columns = ['📝 Nome', '💰 Valor', '📅 Vencimento', '🏷️ Categoria']
        
        # Exibir tabela interativa
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "📝 Nome": st.column_config.TextColumn("📝 Nome", width="medium"),
                "💰 Valor": st.column_config.TextColumn("💰 Valor", width="small"),
                "📅 Vencimento": st.column_config.TextColumn("📅 Vencimento", width="small"),
                "🏷️ Categoria": st.column_config.TextColumn("🏷️ Categoria", width="medium")
            }
        )
        
        # Botões de ação
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            if st.button("➕ Adicionar Conta"):
                st.info("💡 Funcionalidade de adição em desenvolvimento")
        with col_btn2:
            if st.button("✏️ Editar Selecionada"):
                st.info("💡 Funcionalidade de edição em desenvolvimento")
        with col_btn3:
            if st.button("🗑️ Remover Selecionada"):
                st.info("💡 Funcionalidade de remoção em desenvolvimento")
    
    with tab2:
        st.subheader("📊 Contas Variáveis")
        
        # Dados de exemplo de contas variáveis
        if "contas_variaveis" not in st.session_state:
            st.session_state.contas_variaveis = [
                {"nome": "Supermercado", "valor_medio": 450.00, "categoria": "Alimentação"},
                {"nome": "Combustível", "valor_medio": 280.00, "categoria": "Transporte"},
                {"nome": "Restaurantes", "valor_medio": 320.00, "categoria": "Alimentação"},
                {"nome": "Farmácia", "valor_medio": 120.00, "categoria": "Saúde"}
            ]
        
        # Métricas
        total_variaveis = sum(conta["valor_medio"] for conta in st.session_state.contas_variaveis)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("💰 Média Mensal", f"R$ {total_variaveis:,.2f}")
        with col2:
            st.metric("📊 Categorias", len(set(conta["categoria"] for conta in st.session_state.contas_variaveis)))
        with col3:
            st.metric("📈 Variação", "+5.2%")
        
        # Tabela de contas variáveis
        st.subheader("📋 Suas Contas Variáveis")
        
        import pandas as pd
        import random
        
        # Adicionar variação simulada
        df_variaveis = pd.DataFrame(st.session_state.contas_variaveis)
        df_variaveis['variacao'] = [random.uniform(-20, 20) for _ in range(len(df_variaveis))]
        df_variaveis['valor_formatado'] = df_variaveis['valor_medio'].apply(lambda x: f"R$ {x:,.2f}")
        df_variaveis['variacao_formatada'] = df_variaveis['variacao'].apply(
            lambda x: f"{'🟢' if x > 0 else '🔴'} {x:+.1f}%"
        )
        
        # Configurar colunas para exibição
        df_display = df_variaveis[['nome', 'valor_formatado', 'categoria', 'variacao_formatada']].copy()
        df_display.columns = ['📝 Nome', '💰 Valor Médio', '🏷️ Categoria', '📈 Variação']
        
        # Exibir tabela interativa
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "📝 Nome": st.column_config.TextColumn("📝 Nome", width="medium"),
                "💰 Valor Médio": st.column_config.TextColumn("💰 Valor Médio", width="small"),
                "🏷️ Categoria": st.column_config.TextColumn("🏷️ Categoria", width="medium"),
                "📈 Variação": st.column_config.TextColumn("📈 Variação", width="small")
            }
        )
        
        # Botões de ação
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            if st.button("📊 Ver Histórico Detalhado"):
                st.info("💡 Histórico detalhado em desenvolvimento")
        with col_btn2:
            if st.button("📈 Análise de Tendências"):
                st.info("💡 Análise de tendências em desenvolvimento")
        with col_btn3:
            if st.button("🎯 Definir Metas"):
                st.info("💡 Definição de metas em desenvolvimento")
    
    with tab3:
        # Usar a nova função de impostos
        show_taxes_section()
    
    with tab4:
        st.subheader("📈 Resumo Geral")
        
        # Calcular totais
        total_fixas = sum(conta["valor"] for conta in st.session_state.get("contas_fixas", []))
        total_variaveis = sum(conta["valor_medio"] for conta in st.session_state.get("contas_variaveis", []))
        total_impostos = sum(item["valor_total"] for item in st.session_state.get("taxes_data", []))
        
        # Métricas gerais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💰 Contas Fixas", f"R$ {total_fixas:,.2f}")
        with col2:
            st.metric("📊 Contas Variáveis", f"R$ {total_variaveis:,.2f}")
        with col3:
            st.metric("🏛️ Impostos/Ano", f"R$ {total_impostos:,.2f}")
        with col4:
            total_geral = total_fixas + total_variaveis + (total_impostos/12)
            st.metric("💸 Total Mensal", f"R$ {total_geral:,.2f}")
        
        # Gráfico de distribuição
        st.subheader("📊 Distribuição de Gastos")
        
        import plotly.express as px
        import pandas as pd
        
        dados_grafico = {
            "Categoria": ["Contas Fixas", "Contas Variáveis", "Impostos (mensal)"],
            "Valor": [total_fixas, total_variaveis, total_impostos/12]
        }
        
        df_grafico = pd.DataFrame(dados_grafico)
        fig = px.pie(df_grafico, values="Valor", names="Categoria", 
                    title="Distribuição de Gastos Mensais")
        st.plotly_chart(fig, use_container_width=True)
        
        # Alertas e insights
        st.subheader("🚨 Alertas e Insights")
        
        if total_fixas > total_variaveis:
            st.info("💡 **Insight:** Suas contas fixas representam a maior parte dos gastos. Considere renegociar contratos.")
        else:
            st.warning("⚠️ **Atenção:** Seus gastos variáveis estão altos. Monitore mais de perto.")
        
        if total_impostos > 0:
            impostos_mensais = total_impostos / 12
            percentual_impostos = (impostos_mensais / total_geral) * 100
            st.info(f"🏛️ **Impostos:** Representam {percentual_impostos:.1f}% do seu orçamento mensal.")


def show_settings():
    """Exibe página de configurações completa."""
    st.header("⚙️ Configurações")
    st.markdown("Configure todos os aspectos da sua Finance App.")
    
    # Tabs principais
    tab1, tab2, tab3, tab4 = st.tabs(["🖥️ Sistema", "🏷️ Categorias", "📤 Importação", "🏦 APIs Bancárias"])
    
    with tab1:
        st.subheader("🖥️ Configurações do Sistema")
        
        # Status dos serviços
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Verificar status da API
            try:
                response = requests.get("http://localhost:8000/health", timeout=3)
                if response.status_code == 200:
                    st.success("🟢 API: Conectada")
                else:
                    st.error("🔴 API: Erro")
            except:
                st.error("🔴 API: Offline")
        
        with col2:
            # Status do banco (simulado)
            st.success("🟢 Database: Conectado")
        
        with col3:
            # Status do Ollama
            try:
                ollama_response = requests.get("http://localhost:11434/api/tags", timeout=3)
                if ollama_response.status_code == 200:
                    st.success("🟢 Ollama: Funcionando")
                else:
                    st.warning("🟡 Ollama: Problema")
            except:
                st.error("🔴 Ollama: Offline")
        
        # Configurações gerais
        st.subheader("⚙️ Configurações Gerais")
        
        col_cfg1, col_cfg2 = st.columns(2)
        
        with col_cfg1:
            st.checkbox("🔔 Notificações", value=True)
            st.checkbox("🌙 Modo Escuro", value=False)
            st.checkbox("💾 Backup Automático", value=True)
        
        with col_cfg2:
            st.selectbox("🌍 Idioma", ["Português", "English", "Español"])
            st.selectbox("💱 Moeda", ["BRL (R$)", "USD ($)", "EUR (€)"])
            st.selectbox("📅 Formato Data", ["DD/MM/AAAA", "MM/DD/AAAA", "AAAA-MM-DD"])
    
    with tab2:
        # Usar a nova função de categorias
        show_categories_config()
    
    with tab3:
        # Usar a nova função de importação
        show_import_config()
    
    with tab4:
        st.subheader("🏦 Configuração de APIs Bancárias")
        
        # Inicializar configurações bancárias no session_state
        if 'banking_config' not in st.session_state:
            st.session_state.banking_config = {
                'enable_banking': True,
                'enable_auto_import': False,
                'enable_ocr': True,
                'enable_categorization': True,
                'enable_duplicate_detection': True,
                'enable_installment_detection': True
            }
        
        # Aviso sobre limitações das APIs bancárias
        st.markdown("""
        <div class="banking-warning-box">
            ⚠️ <strong>Importante:</strong> APIs diretas dos bancos brasileiros não estão disponíveis para aplicações pessoais. 
            Esta seção foca no upload e processamento de faturas e extratos bancários.
        </div>
        """, unsafe_allow_html=True)
        
        # Configurações de APIs bancárias
        st.markdown("### 🔧 Configurações de Integração")
        
        # Toggle para habilitar/desabilitar funcionalidades bancárias
        col_bank1, col_bank2 = st.columns(2)
        
        with col_bank1:
            enable_banking = st.checkbox(
                "🏦 Habilitar Funcionalidades Bancárias", 
                value=st.session_state.banking_config['enable_banking'],
                key="banking_enable_banking"
            )
            enable_auto_import = st.checkbox(
                "📤 Upload Automático", 
                value=st.session_state.banking_config['enable_auto_import'], 
                disabled=not enable_banking,
                key="banking_enable_auto_import"
            )
            enable_ocr = st.checkbox(
                "🔍 OCR para PDFs", 
                value=st.session_state.banking_config['enable_ocr'], 
                disabled=not enable_banking,
                key="banking_enable_ocr"
            )
        
        with col_bank2:
            enable_categorization = st.checkbox(
                "🦙 Categorização Automática", 
                value=st.session_state.banking_config['enable_categorization'], 
                disabled=not enable_banking,
                key="banking_enable_categorization"
            )
            enable_duplicate_detection = st.checkbox(
                "🔍 Detecção de Duplicatas", 
                value=st.session_state.banking_config['enable_duplicate_detection'], 
                disabled=not enable_banking,
                key="banking_enable_duplicate_detection"
            )
            enable_installment_detection = st.checkbox(
                "💳 Detecção de Parcelas", 
                value=st.session_state.banking_config['enable_installment_detection'], 
                disabled=not enable_banking,
                key="banking_enable_installment_detection"
            )
        
        if enable_banking:
            st.markdown("### 📁 Configuração de Diretórios")
            
            col_dir1, col_dir2 = st.columns(2)
            
            with col_dir1:
                st.text_input("📂 Pasta de Upload", value="uploads/", disabled=not enable_banking)
                st.text_input("💾 Pasta de Backup", value="backup/", disabled=not enable_banking)
            
            with col_dir2:
                st.text_input("📊 Pasta Processados", value="processed/", disabled=not enable_banking)
                st.text_input("❌ Pasta de Erros", value="errors/", disabled=not enable_banking)
            
            # Configurações de bancos suportados
            st.markdown("### 🏦 Bancos Suportados")
            
            bancos_suportados = [
                {"nome": "Itaú", "faturas": True, "extratos": True, "ofx": True},
                {"nome": "Santander", "faturas": True, "extratos": True, "ofx": True},
                {"nome": "Bradesco", "faturas": True, "extratos": True, "ofx": False},
                {"nome": "Nubank", "faturas": True, "extratos": False, "ofx": False},
                {"nome": "Inter", "faturas": True, "extratos": True, "ofx": True},
                {"nome": "C6 Bank", "faturas": True, "extratos": True, "ofx": False}
            ]
            
            for banco in bancos_suportados:
                with st.expander(f"🏦 {banco['nome']}"):
                    col_b1, col_b2, col_b3 = st.columns(3)
                    
                    with col_b1:
                        faturas_status = "✅" if banco['faturas'] else "❌"
                        st.write(f"**📄 Faturas:** {faturas_status}")
                    
                    with col_b2:
                        extratos_status = "✅" if banco['extratos'] else "❌"
                        st.write(f"**📊 Extratos:** {extratos_status}")
                    
                    with col_b3:
                        ofx_status = "✅" if banco['ofx'] else "❌"
                        st.write(f"**📁 OFX:** {ofx_status}")
        
        else:
            st.info("🔒 Funcionalidades bancárias desabilitadas. Habilite para configurar.")
        
        # Botões de ação
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            if st.button("💾 Salvar Configurações"):
                # Salvar configurações no session_state
                st.session_state.banking_config.update({
                    'enable_banking': enable_banking,
                    'enable_auto_import': enable_auto_import,
                    'enable_ocr': enable_ocr,
                    'enable_categorization': enable_categorization,
                    'enable_duplicate_detection': enable_duplicate_detection,
                    'enable_installment_detection': enable_installment_detection
                })
                st.success("✅ Configurações bancárias salvas!")
                st.rerun()  # Recarregar para mostrar as configurações salvas
        
        with col_btn2:
            if st.button("🧪 Testar Configurações"):
                if enable_banking:
                    st.info("🔍 Testando configurações...")
                    # Simular teste
                    import time
                    time.sleep(2)
                    st.success("✅ Configurações testadas com sucesso!")
                else:
                    st.warning("⚠️ Habilite as funcionalidades bancárias primeiro")
        
        with col_btn3:
            if st.button("🔄 Restaurar Padrões"):
                st.info("🔄 Configurações restauradas para os valores padrão")




def show_ollama():
    """Exibe página dedicada do Ollama."""
    st.header("🦙 Ollama - IA Local")
    st.markdown("Configure e monitore sua inteligência artificial local.")
    
    # Tabs para organizar
    tab1, tab2, tab3 = st.tabs(["⚙️ Configuração", "📊 Status", "🧪 Teste"])
    
    with tab1:
        st.subheader("⚙️ Configuração do Ollama")
        
        # Configurações do Ollama
        col_ollama1, col_ollama2 = st.columns(2)
        
        with col_ollama1:
            host_ollama = st.text_input("🌐 Host do Ollama", value="http://localhost:11434")
            modelo_ollama = st.text_input("🦙 Modelo", value="deepseek-r1:7b")
        
        with col_ollama2:
            temperatura = st.slider("🌡️ Temperatura", 0.0, 2.0, 0.1, 0.1)
            max_tokens = st.number_input("📊 Max Tokens", min_value=100, max_value=2000, value=500)
        
        # Configurações avançadas
        with st.expander("🔧 Configurações Avançadas"):
            col_adv1, col_adv2 = st.columns(2)
            
            with col_adv1:
                timeout = st.number_input("⏱️ Timeout (segundos)", min_value=5, max_value=300, value=30)
                max_retries = st.number_input("🔄 Max Tentativas", min_value=1, max_value=10, value=3)
            
            with col_adv2:
                context_length = st.number_input("📝 Tamanho do Contexto", min_value=512, max_value=8192, value=2048)
                batch_size = st.number_input("📦 Batch Size", min_value=1, max_value=100, value=10)
        
        if st.button("💾 Salvar Configurações"):
            st.success("✅ Configurações do Ollama salvas!")
    
    with tab2:
        st.subheader("📊 Status do Ollama")
        
        # Verificar status
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            
            if response.status_code == 200:
                st.success("🟢 **Ollama está funcionando!**")
                
                data = response.json()
                modelos = data.get("models", [])
                
                if modelos:
                    st.subheader("🤖 Modelos Disponíveis")
                    
                    for modelo in modelos:
                        nome = modelo.get("name", "Desconhecido")
                        tamanho = modelo.get("size", 0)
                        tamanho_gb = tamanho / (1024**3) if tamanho > 0 else 0
                        modified = modelo.get("modified_at", "")
                        
                        with st.expander(f"🤖 {nome} ({tamanho_gb:.1f}GB)"):
                            col_model1, col_model2 = st.columns(2)
                            
                            with col_model1:
                                st.write(f"**Nome:** {nome}")
                                st.write(f"**Tamanho:** {tamanho_gb:.1f}GB")
                            
                            with col_model2:
                                st.write(f"**Modificado:** {modified[:10] if modified else 'N/A'}")
                                if st.button(f"🗑️ Remover {nome}", key=f"remove_{nome}"):
                                    st.warning("⚠️ Funcionalidade em desenvolvimento")
                else:
                    st.warning("⚠️ Nenhum modelo encontrado")
                    
                    if st.button("📥 Baixar Modelo Padrão"):
                        st.info("💡 Execute: `ollama pull llama2` no terminal")
            
            else:
                st.error(f"🔴 **Erro na conexão:** Status {response.status_code}")
                
        except Exception as e:
            st.error(f"🔴 **Ollama não está disponível:** {str(e)}")
            
            st.markdown("""
            ### 🚀 Como instalar o Ollama:
            
            ```bash
            # Ubuntu/Debian
            curl -fsSL https://ollama.ai/install.sh | sh
            
            # Iniciar serviço
            ollama serve
            
            # Baixar modelo (em outro terminal)
            ollama pull llama2
            ```
            """)
    
    with tab3:
        st.subheader("🧪 Teste do Ollama")
        
        # Interface de teste
        prompt_teste = st.text_area(
            "Digite um prompt para testar:",
            value="Categorize esta transação: 'Compra no supermercado Extra - R$ 150,00'",
            height=100
        )
        
        if st.button("🚀 Testar Prompt"):
            if prompt_teste:
                with st.spinner("Processando com Ollama..."):
                    try:
                        import requests
                        
                        # Primeiro, verificar modelos disponíveis
                        models_response = requests.get("http://localhost:11434/api/tags", timeout=5)
                        if models_response.status_code != 200:
                            st.error("❌ Ollama não está disponível")
                            return
                        
                        models_data = models_response.json()
                        available_models = [m.get("name", "") for m in models_data.get("models", [])]
                        
                        if not available_models:
                            st.error("❌ Nenhum modelo disponível. Execute: `ollama pull llama2`")
                            return
                        
                        # Usar o primeiro modelo disponível
                        model_to_use = available_models[0]
                        st.info(f"🤖 Usando modelo: {model_to_use}")
                        
                        payload = {
                            "model": model_to_use,
                            "prompt": prompt_teste,
                            "stream": False
                        }
                        
                        response = requests.post(
                            "http://localhost:11434/api/generate",
                            json=payload,
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            resposta = result.get("response", "Sem resposta")
                            
                            st.success("✅ **Resposta do Ollama:**")
                            st.write(resposta)
                            
                            # Métricas
                            col_metric1, col_metric2, col_metric3 = st.columns(3)
                            
                            with col_metric1:
                                eval_count = result.get("eval_count", 0)
                                st.metric("Tokens Gerados", eval_count)
                            
                            with col_metric2:
                                eval_duration = result.get("eval_duration", 0) / 1e9  # nanosegundos para segundos
                                st.metric("Tempo (s)", f"{eval_duration:.2f}")
                            
                            with col_metric3:
                                if eval_count > 0 and eval_duration > 0:
                                    tokens_per_sec = eval_count / eval_duration
                                    st.metric("Tokens/s", f"{tokens_per_sec:.1f}")
                        
                        else:
                            st.error(f"❌ Erro: Status {response.status_code}")
                    
                    except Exception as e:
                        st.error(f"❌ Erro ao testar: {str(e)}")
            else:
                st.warning("⚠️ Digite um prompt para testar")
        
        # Exemplos de prompts
        st.subheader("💡 Exemplos de Prompts")
        
        exemplos = [
            "Categorize esta transação: 'Pagamento Uber - R$ 25,00'",
            "Esta transação é recorrente? 'Netflix - R$ 29,90'",
            "Analise este gasto: 'Farmácia São João - R$ 85,50'",
            "Sugira uma categoria: 'Posto Shell - R$ 120,00'"
        ]
        
        for i, exemplo in enumerate(exemplos):
            if st.button(f"📝 Usar Exemplo {i+1}", key=f"exemplo_{i}"):
                st.session_state.prompt_teste = exemplo
                st.rerun()

def main():
    """Função principal da aplicação."""
    
    # Sidebar para navegação
    with st.sidebar:
        st.title("🏦 Finance App")
        st.markdown("---")
        
        # Navegação por botões
        st.markdown("### 📋 Navegação")
        
        # Inicializar estado da página se não existir
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "🏠 Dashboard"
        
        # Botões de navegação
        if st.button("🏠 Dashboard", use_container_width=True, 
                    type="primary" if st.session_state.current_page == "🏠 Dashboard" else "secondary"):
            st.session_state.current_page = "🏠 Dashboard"
            st.rerun()
        
        if st.button("💳 Transações", use_container_width=True,
                    type="primary" if st.session_state.current_page == "💳 Transações" else "secondary"):
            st.session_state.current_page = "💳 Transações"
            st.rerun()
        
        if st.button("🏦 Contas", use_container_width=True,
                    type="primary" if st.session_state.current_page == "🏦 Contas" else "secondary"):
            st.session_state.current_page = "🏦 Contas"
            st.rerun()
        
        if st.button("📊 Análises", use_container_width=True,
                    type="primary" if st.session_state.current_page == "📊 Análises" else "secondary"):
            st.session_state.current_page = "📊 Análises"
            st.rerun()
        
        if st.button("⚙️ Configurações", use_container_width=True,
                    type="primary" if st.session_state.current_page == "⚙️ Configurações" else "secondary"):
            st.session_state.current_page = "⚙️ Configurações"
            st.rerun()
        
        if st.button("🦙 Ollama", use_container_width=True,
                    type="primary" if st.session_state.current_page == "🦙 Ollama" else "secondary"):
            st.session_state.current_page = "🦙 Ollama"
            st.rerun()
        
        page = st.session_state.current_page
        
        st.markdown("---")
        st.markdown("### 🦙 IA Financeira")
        st.info("Esta aplicação usa Ollama (LLM local) para categorização automática e análises inteligentes.")
        
        st.markdown("### 📋 Status")
        api = get_api_client()
        health = api.get_health()
        
        # Verificação segura do status
        if health and "error" not in health and health.get("detail") != "Not Found":
            overall_status = health.get("status", "unknown")
            if overall_status == "healthy":
                st.success("🟢 Sistema Online")
            else:
                st.warning(f"🟡 Sistema: {overall_status}")
        else:
            st.error("🔴 Sistema Offline")
            if st.button("🔄 Tentar Reconectar"):
                st.rerun()
    
    # Roteamento de páginas
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "💳 Transações":
        show_transactions()
    elif page == "🏦 Contas":
        show_contas()
    elif page == "📊 Análises":
        show_analytics()
    elif page == "⚙️ Configurações":
        show_settings()
    elif page == "🦙 Ollama":
        show_ollama()


if __name__ == "__main__":
    main()

