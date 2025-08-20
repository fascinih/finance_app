"""
LLM Service for Finance App.
Integração com Ollama para análise inteligente de transações financeiras.
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
import httpx
from loguru import logger
import time
from dataclasses import dataclass

from src.config import settings
from src.models import CacheManager


@dataclass
class LLMResponse:
    """Response from LLM analysis."""
    category: str
    confidence: float
    reasoning: str
    tags: List[str]
    subcategory: Optional[str] = None
    is_recurring: Optional[bool] = None
    merchant_type: Optional[str] = None


class OllamaService:
    """Service for interacting with Ollama LLM."""
    
    def __init__(self):
        self.base_url = settings.OLLAMA_HOST
        self.default_model = settings.OLLAMA_DEFAULT_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
        self.max_retries = settings.OLLAMA_MAX_RETRIES
        self.cache_ttl = 3600  # 1 hour cache
        
    async def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to Ollama API with retries."""
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}{endpoint}",
                        json=data
                    )
                    
                    if response.status_code == 200:
                        return response.json()
                    else:
                        logger.warning(f"Ollama API returned {response.status_code}: {response.text}")
                        
            except httpx.TimeoutException:
                logger.warning(f"Ollama request timeout (attempt {attempt + 1}/{self.max_retries})")
            except Exception as e:
                logger.error(f"Ollama request error (attempt {attempt + 1}/{self.max_retries}): {e}")
            
            if attempt < self.max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        raise Exception(f"Failed to connect to Ollama after {self.max_retries} attempts")
    
    async def check_health(self) -> bool:
        """Check if Ollama service is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
    
    async def list_models(self) -> List[str]:
        """Get list of available models."""
        try:
            response = await self._make_request("/api/tags", {})
            models = response.get("models", [])
            return [model.get("name", "") for model in models]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    async def categorize_transaction(
        self, 
        description: str, 
        amount: float, 
        counterpart: Optional[str] = None,
        location: Optional[str] = None,
        date: Optional[str] = None,
        model: Optional[str] = None
    ) -> LLMResponse:
        """
        Categorize a financial transaction using LLM.
        
        Args:
            description: Transaction description
            amount: Transaction amount (negative for expenses)
            counterpart: Counterpart name/merchant
            location: Transaction location
            date: Transaction date
            model: Model to use (defaults to configured model)
            
        Returns:
            LLMResponse with categorization results
        """
        
        # Create cache key
        cache_key = f"llm_categorize:{hash(f'{description}:{amount}:{counterpart}')}"
        
        # Check cache first
        cached_result = CacheManager.get(cache_key)
        if cached_result:
            try:
                cached_data = json.loads(cached_result)
                return LLMResponse(**cached_data)
            except Exception:
                pass  # Cache miss, continue with LLM call
        
        # Prepare context
        context_parts = [f"Descrição: {description}"]
        
        if amount < 0:
            context_parts.append(f"Valor: R$ {abs(amount):,.2f} (despesa)")
        else:
            context_parts.append(f"Valor: R$ {amount:,.2f} (receita)")
        
        if counterpart:
            context_parts.append(f"Estabelecimento: {counterpart}")
        
        if location:
            context_parts.append(f"Local: {location}")
        
        if date:
            context_parts.append(f"Data: {date}")
        
        transaction_context = " | ".join(context_parts)
        
        # Create prompt for Brazilian financial categorization
        prompt = f"""Você é um especialista em categorização de transações financeiras brasileiras. 

Analise a seguinte transação e forneça uma categorização detalhada:

{transaction_context}

Responda APENAS com um JSON válido no seguinte formato:
{{
    "category": "nome_da_categoria_principal",
    "subcategory": "subcategoria_específica",
    "confidence": 0.95,
    "reasoning": "explicação_breve_da_categorização",
    "tags": ["tag1", "tag2", "tag3"],
    "is_recurring": true/false,
    "merchant_type": "tipo_do_estabelecimento"
}}

Categorias principais disponíveis:
- Alimentação (supermercado, restaurante, delivery)
- Transporte (combustível, uber, transporte público)
- Moradia (aluguel, condomínio, energia, água, gás)
- Saúde (plano, medicamento, consulta)
- Educação (escola, curso, material)
- Lazer (cinema, viagem, entretenimento)
- Vestuário (roupa, calçado, acessório)
- Tecnologia (celular, internet, software)
- Bancos e Taxas (tarifa, juros, anuidade)
- Salário (remuneração, benefício)
- Investimentos (aplicação, rendimento)
- Outros

Use sempre nomes em português brasileiro. Seja preciso e consistente."""

        try:
            # Make LLM request
            model_name = model or self.default_model
            
            request_data = {
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low temperature for consistent categorization
                    "top_p": 0.9,
                    "num_predict": 500
                }
            }
            
            start_time = time.time()
            response = await self._make_request("/api/generate", request_data)
            response_time = time.time() - start_time
            
            logger.debug(f"LLM categorization took {response_time:.2f}s")
            
            # Parse response
            llm_output = response.get("response", "").strip()
            
            # Try to extract JSON from response
            try:
                # Find JSON in response (sometimes LLM adds extra text)
                json_start = llm_output.find("{")
                json_end = llm_output.rfind("}") + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = llm_output[json_start:json_end]
                    result_data = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")
                
                # Validate and create response
                llm_response = LLMResponse(
                    category=result_data.get("category", "Outros"),
                    confidence=min(max(float(result_data.get("confidence", 0.5)), 0.0), 1.0),
                    reasoning=result_data.get("reasoning", "Categorização automática"),
                    tags=result_data.get("tags", []),
                    subcategory=result_data.get("subcategory"),
                    is_recurring=result_data.get("is_recurring"),
                    merchant_type=result_data.get("merchant_type")
                )
                
                # Cache successful result
                cache_data = {
                    "category": llm_response.category,
                    "confidence": llm_response.confidence,
                    "reasoning": llm_response.reasoning,
                    "tags": llm_response.tags,
                    "subcategory": llm_response.subcategory,
                    "is_recurring": llm_response.is_recurring,
                    "merchant_type": llm_response.merchant_type
                }
                CacheManager.set(cache_key, json.dumps(cache_data), self.cache_ttl)
                
                return llm_response
                
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Failed to parse LLM response: {e}")
                logger.debug(f"Raw LLM output: {llm_output}")
                
                # Fallback categorization
                return self._fallback_categorization(description, amount)
                
        except Exception as e:
            logger.error(f"LLM categorization failed: {e}")
            return self._fallback_categorization(description, amount)
    
    def _fallback_categorization(self, description: str, amount: float) -> LLMResponse:
        """Fallback categorization using simple rules."""
        
        description_lower = description.lower()
        
        # Simple keyword-based categorization
        if any(word in description_lower for word in ["supermercado", "mercado", "padaria", "acougue"]):
            category = "Alimentação"
            subcategory = "Supermercado"
        elif any(word in description_lower for word in ["restaurante", "lanchonete", "delivery", "ifood"]):
            category = "Alimentação"
            subcategory = "Restaurante"
        elif any(word in description_lower for word in ["uber", "99", "taxi", "combustivel", "posto"]):
            category = "Transporte"
            subcategory = "Combustível" if "posto" in description_lower else "Aplicativo"
        elif any(word in description_lower for word in ["salario", "remuneracao", "pagamento"]):
            category = "Salário"
            subcategory = "Remuneração"
        elif any(word in description_lower for word in ["aluguel", "condominio", "energia", "agua", "gas"]):
            category = "Moradia"
            subcategory = "Contas Básicas"
        else:
            category = "Outros"
            subcategory = None
        
        return LLMResponse(
            category=category,
            confidence=0.3,  # Low confidence for fallback
            reasoning="Categorização baseada em palavras-chave (fallback)",
            tags=[],
            subcategory=subcategory,
            is_recurring=None,
            merchant_type=None
        )
    
    async def analyze_spending_pattern(
        self, 
        transactions: List[Dict[str, Any]], 
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze spending patterns using LLM.
        
        Args:
            transactions: List of transaction data
            model: Model to use
            
        Returns:
            Analysis results with insights and recommendations
        """
        
        if not transactions:
            return {"insights": [], "recommendations": [], "summary": "Nenhuma transação para análise"}
        
        # Prepare transaction summary
        total_expenses = sum(abs(tx["amount"]) for tx in transactions if tx["amount"] < 0)
        total_income = sum(tx["amount"] for tx in transactions if tx["amount"] > 0)
        transaction_count = len(transactions)
        
        # Group by category
        category_totals = {}
        for tx in transactions:
            category = tx.get("category", "Outros")
            if category not in category_totals:
                category_totals[category] = 0
            category_totals[category] += abs(tx["amount"])
        
        # Top categories
        top_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Create analysis prompt
        prompt = f"""Você é um consultor financeiro especializado em análise de gastos pessoais no Brasil.

Analise os seguintes dados financeiros e forneça insights e recomendações:

RESUMO FINANCEIRO:
- Total de transações: {transaction_count}
- Receitas: R$ {total_income:,.2f}
- Despesas: R$ {total_expenses:,.2f}
- Saldo líquido: R$ {total_income - total_expenses:,.2f}

PRINCIPAIS CATEGORIAS DE GASTOS:
{chr(10).join([f"- {cat}: R$ {amount:,.2f} ({amount/total_expenses*100:.1f}%)" for cat, amount in top_categories])}

Responda APENAS com um JSON válido no seguinte formato:
{{
    "summary": "resumo_geral_da_situação_financeira",
    "insights": [
        "insight_1_sobre_padrões_de_gastos",
        "insight_2_sobre_categorias_principais",
        "insight_3_sobre_oportunidades"
    ],
    "recommendations": [
        "recomendação_1_específica_e_acionável",
        "recomendação_2_para_otimização",
        "recomendação_3_para_controle"
    ],
    "alerts": [
        "alerta_1_sobre_gastos_excessivos",
        "alerta_2_sobre_padrões_preocupantes"
    ],
    "score": 85
}}

Seja específico, prático e focado na realidade brasileira. Use linguagem clara e acessível."""

        try:
            model_name = model or self.default_model
            
            request_data = {
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "top_p": 0.9,
                    "num_predict": 800
                }
            }
            
            response = await self._make_request("/api/generate", request_data)
            llm_output = response.get("response", "").strip()
            
            # Parse JSON response
            json_start = llm_output.find("{")
            json_end = llm_output.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = llm_output[json_start:json_end]
                analysis = json.loads(json_str)
                
                # Add metadata
                analysis["generated_at"] = time.time()
                analysis["model_used"] = model_name
                analysis["transaction_count"] = transaction_count
                
                return analysis
            else:
                raise ValueError("No JSON found in LLM response")
                
        except Exception as e:
            logger.error(f"LLM spending analysis failed: {e}")
            
            # Fallback analysis
            return {
                "summary": f"Análise de {transaction_count} transações com saldo líquido de R$ {total_income - total_expenses:,.2f}",
                "insights": [
                    f"Maior categoria de gastos: {top_categories[0][0]} (R$ {top_categories[0][1]:,.2f})" if top_categories else "Sem dados suficientes",
                    f"Taxa de gastos: {total_expenses/total_income*100:.1f}% da receita" if total_income > 0 else "Receita insuficiente",
                    "Análise detalhada indisponível (modo fallback)"
                ],
                "recommendations": [
                    "Revise os gastos nas principais categorias",
                    "Estabeleça um orçamento mensal",
                    "Monitore transações recorrentes"
                ],
                "alerts": [],
                "score": 50,
                "generated_at": time.time(),
                "model_used": "fallback",
                "transaction_count": transaction_count
            }
    
    async def detect_anomalies(
        self, 
        recent_transactions: List[Dict[str, Any]], 
        historical_average: Dict[str, float],
        model: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalous transactions using LLM analysis.
        
        Args:
            recent_transactions: Recent transactions to analyze
            historical_average: Historical spending averages by category
            model: Model to use
            
        Returns:
            List of detected anomalies with explanations
        """
        
        anomalies = []
        
        for tx in recent_transactions:
            category = tx.get("category", "Outros")
            amount = abs(tx["amount"])
            avg_amount = historical_average.get(category, 0)
            
            # Simple threshold-based detection
            if avg_amount > 0 and amount > avg_amount * 2:  # 2x above average
                anomalies.append({
                    "transaction_id": tx.get("id"),
                    "description": tx.get("description"),
                    "amount": amount,
                    "category": category,
                    "anomaly_type": "high_amount",
                    "severity": "medium" if amount < avg_amount * 3 else "high",
                    "explanation": f"Valor {amount/avg_amount:.1f}x acima da média histórica (R$ {avg_amount:,.2f})",
                    "recommendation": "Verifique se esta transação está correta"
                })
        
        return anomalies[:10]  # Limit to top 10 anomalies


# Global service instance
llm_service = OllamaService()

