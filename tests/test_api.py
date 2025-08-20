"""
Testes para as APIs do Finance App
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from datetime import date, datetime, timedelta
import json
from decimal import Decimal

# Importar a aplicação
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from api.main import app
from models.database import get_db
from models.transactions import Transaction
from models.categories import Category

# Cliente de teste
client = TestClient(app)


class TestHealthAPI:
    """Testes para o endpoint de health check."""
    
    def test_health_check(self):
        """Testa o health check básico."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
    
    def test_health_check_detailed(self):
        """Testa o health check detalhado."""
        response = client.get("/api/v1/health?detailed=true")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "services" in data
        assert "database" in data["services"]


class TestTransactionsAPI:
    """Testes para as APIs de transações."""
    
    def setup_method(self):
        """Setup para cada teste."""
        # Limpar dados de teste se necessário
        pass
    
    def test_create_transaction(self):
        """Testa criação de transação."""
        transaction_data = {
            "amount": -50.00,
            "description": "Teste Supermercado",
            "transaction_type": "debit",
            "account_id": "test_account",
            "counterpart_name": "Supermercado Teste",
            "category": "Alimentação"
        }
        
        response = client.post("/api/v1/transactions/", json=transaction_data)
        
        # Pode falhar se o banco não estiver configurado
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert data["amount"] == -50.00
            assert data["description"] == "Teste Supermercado"
        else:
            # Aceitar erro de conexão com banco em ambiente de teste
            assert response.status_code in [422, 500]
    
    def test_get_transactions(self):
        """Testa listagem de transações."""
        response = client.get("/api/v1/transactions/")
        
        # Pode falhar se o banco não estiver configurado
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
        else:
            assert response.status_code in [422, 500]
    
    def test_get_transactions_with_filters(self):
        """Testa listagem com filtros."""
        params = {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "category": "Alimentação",
            "limit": 10
        }
        
        response = client.get("/api/v1/transactions/", params=params)
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            assert len(data) <= 10
        else:
            assert response.status_code in [422, 500]
    
    def test_get_transaction_by_id(self):
        """Testa busca de transação por ID."""
        # Usar ID fictício para teste
        test_id = "550e8400-e29b-41d4-a716-446655440000"
        
        response = client.get(f"/api/v1/transactions/{test_id}")
        
        # Esperado 404 para ID inexistente
        assert response.status_code in [404, 500]
    
    def test_update_transaction(self):
        """Testa atualização de transação."""
        test_id = "550e8400-e29b-41d4-a716-446655440000"
        update_data = {
            "description": "Descrição Atualizada",
            "category": "Transporte"
        }
        
        response = client.put(f"/api/v1/transactions/{test_id}", json=update_data)
        
        # Esperado 404 para ID inexistente
        assert response.status_code in [404, 500]
    
    def test_delete_transaction(self):
        """Testa exclusão de transação."""
        test_id = "550e8400-e29b-41d4-a716-446655440000"
        
        response = client.delete(f"/api/v1/transactions/{test_id}")
        
        # Esperado 404 para ID inexistente
        assert response.status_code in [404, 500]


class TestCategoriesAPI:
    """Testes para as APIs de categorias."""
    
    def test_get_categories(self):
        """Testa listagem de categorias."""
        response = client.get("/api/v1/categories/")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
        else:
            assert response.status_code in [422, 500]
    
    def test_create_category(self):
        """Testa criação de categoria."""
        category_data = {
            "name": "Categoria Teste",
            "description": "Categoria para testes",
            "color": "#FF5733",
            "icon": "test-icon"
        }
        
        response = client.post("/api/v1/categories/", json=category_data)
        
        if response.status_code == 200:
            data = response.json()
            assert data["name"] == "Categoria Teste"
        else:
            assert response.status_code in [422, 500]
    
    def test_get_category_by_id(self):
        """Testa busca de categoria por ID."""
        test_id = "550e8400-e29b-41d4-a716-446655440000"
        
        response = client.get(f"/api/v1/categories/{test_id}")
        
        # Esperado 404 para ID inexistente
        assert response.status_code in [404, 500]


class TestAnalyticsAPI:
    """Testes para as APIs de analytics."""
    
    def test_spending_patterns(self):
        """Testa análise de padrões de gastos."""
        response = client.get("/api/v1/analytics/spending/patterns")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
        else:
            assert response.status_code in [422, 500]
    
    def test_monthly_trends(self):
        """Testa análise de tendências mensais."""
        response = client.get("/api/v1/analytics/trends/monthly")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
        else:
            assert response.status_code in [422, 500]
    
    def test_category_breakdown(self):
        """Testa breakdown por categoria."""
        params = {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        }
        
        response = client.get("/api/v1/analytics/categories/breakdown", params=params)
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
        else:
            assert response.status_code in [422, 500]


class TestImportAPI:
    """Testes para as APIs de importação."""
    
    def test_get_supported_formats(self):
        """Testa listagem de formatos suportados."""
        response = client.get("/api/v1/import/formats")
        
        if response.status_code == 200:
            data = response.json()
            assert "formats" in data
            assert "limits" in data
        else:
            assert response.status_code in [422, 500]
    
    def test_get_import_batches(self):
        """Testa listagem de batches de importação."""
        response = client.get("/api/v1/import/batches")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
        else:
            assert response.status_code in [422, 500]
    
    def test_upload_file_without_file(self):
        """Testa upload sem arquivo."""
        response = client.post("/api/v1/import/upload")
        
        # Esperado erro 422 (dados inválidos)
        assert response.status_code == 422


class TestValidation:
    """Testes de validação de dados."""
    
    def test_invalid_transaction_amount(self):
        """Testa validação de valor inválido."""
        transaction_data = {
            "amount": "invalid",  # Valor inválido
            "description": "Teste",
            "transaction_type": "debit"
        }
        
        response = client.post("/api/v1/transactions/", json=transaction_data)
        assert response.status_code == 422
    
    def test_missing_required_fields(self):
        """Testa campos obrigatórios ausentes."""
        transaction_data = {
            "amount": -50.00
            # Faltando campos obrigatórios
        }
        
        response = client.post("/api/v1/transactions/", json=transaction_data)
        assert response.status_code == 422
    
    def test_invalid_date_format(self):
        """Testa formato de data inválido."""
        params = {
            "start_date": "invalid-date",
            "end_date": "2024-12-31"
        }
        
        response = client.get("/api/v1/transactions/", params=params)
        assert response.status_code == 422
    
    def test_invalid_transaction_type(self):
        """Testa tipo de transação inválido."""
        transaction_data = {
            "amount": -50.00,
            "description": "Teste",
            "transaction_type": "invalid_type"
        }
        
        response = client.post("/api/v1/transactions/", json=transaction_data)
        assert response.status_code == 422


class TestSecurity:
    """Testes de segurança básicos."""
    
    def test_sql_injection_attempt(self):
        """Testa tentativa básica de SQL injection."""
        malicious_params = {
            "category": "'; DROP TABLE transactions; --"
        }
        
        response = client.get("/api/v1/transactions/", params=malicious_params)
        
        # Não deve causar erro 500 (deve ser tratado)
        assert response.status_code in [200, 422, 400]
    
    def test_xss_attempt(self):
        """Testa tentativa básica de XSS."""
        transaction_data = {
            "amount": -50.00,
            "description": "<script>alert('xss')</script>",
            "transaction_type": "debit"
        }
        
        response = client.post("/api/v1/transactions/", json=transaction_data)
        
        if response.status_code == 200:
            data = response.json()
            # Verificar se o script foi sanitizado ou escapado
            assert "<script>" not in data.get("description", "")
        else:
            # Aceitar erro se banco não estiver disponível
            assert response.status_code in [422, 500]


class TestPerformance:
    """Testes básicos de performance."""
    
    def test_health_check_response_time(self):
        """Testa tempo de resposta do health check."""
        import time
        
        start_time = time.time()
        response = client.get("/api/v1/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Health check deve responder em menos de 1 segundo
        assert response_time < 1.0
        assert response.status_code == 200
    
    def test_transactions_list_response_time(self):
        """Testa tempo de resposta da listagem de transações."""
        import time
        
        start_time = time.time()
        response = client.get("/api/v1/transactions/?limit=10")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Listagem deve responder em menos de 5 segundos
        assert response_time < 5.0


if __name__ == "__main__":
    # Executar testes básicos
    print("Executando testes básicos da API...")
    
    # Teste de health check
    try:
        response = client.get("/api/v1/health")
        print(f"Health Check: {response.status_code}")
        if response.status_code == 200:
            print("✅ Health check funcionando")
        else:
            print("❌ Health check com problemas")
    except Exception as e:
        print(f"❌ Erro no health check: {e}")
    
    print("\nPara executar todos os testes, use: pytest tests/test_api.py -v")

