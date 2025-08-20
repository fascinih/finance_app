"""
Serviço de Integração Bancária - Finance App
Gerencia conexões e sincronização com APIs bancárias.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
import base64
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from ..models.database import Base, engine
from ..models.transactions import Transaction
from ..config.settings import get_settings

# Configurar logging
logger = logging.getLogger(__name__)

# Modelo para configurações bancárias (seria criado como tabela)
class BankConfig:
    """Modelo para configurações bancárias."""
    
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.user_id = data.get('user_id')
        self.bank_id = data.get('bank_id')
        self.bank_name = data.get('bank_name')
        self.api_type = data.get('api_type')
        self.auth_type = data.get('auth_type')
        self.credentials = data.get('credentials', {})
        self.sync_settings = data.get('sync_settings', {})
        self.endpoints = data.get('endpoints', {})
        self.status = data.get('status', 'configured')
        self.created_at = data.get('created_at', datetime.now())
        self.updated_at = data.get('updated_at', datetime.now())
        self.last_sync = data.get('last_sync')


class BankingService:
    """Serviço para integração com APIs bancárias."""
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.encryption_key = self._get_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Cache para configurações e tokens
        self._config_cache = {}
        self._token_cache = {}
        
        # Status de sincronização
        self._sync_status = {}
    
    def _get_encryption_key(self) -> bytes:
        """Obtém chave de criptografia para credenciais."""
        # Em produção, usar variável de ambiente ou key management service
        key = getattr(self.settings, 'ENCRYPTION_KEY', None)
        if not key:
            # Gerar chave temporária (em produção, deve ser persistente)
            key = Fernet.generate_key()
        
        if isinstance(key, str):
            key = key.encode()
        
        return key
    
    def _encrypt_credentials(self, credentials: dict) -> str:
        """Criptografa credenciais sensíveis."""
        try:
            json_str = json.dumps(credentials)
            encrypted = self.cipher.encrypt(json_str.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Erro ao criptografar credenciais: {e}")
            raise
    
    def _decrypt_credentials(self, encrypted_credentials: str) -> dict:
        """Descriptografa credenciais."""
        try:
            encrypted_bytes = base64.b64decode(encrypted_credentials.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return json.loads(decrypted.decode())
        except Exception as e:
            logger.error(f"Erro ao descriptografar credenciais: {e}")
            return {}
    
    async def validate_credentials(self, bank_id: str, credentials: dict) -> dict:
        """Valida credenciais do banco."""
        
        try:
            # Validações específicas por banco
            if bank_id == "itau":
                return await self._validate_itau_credentials(credentials)
            elif bank_id == "bradesco":
                return await self._validate_bradesco_credentials(credentials)
            elif bank_id == "santander":
                return await self._validate_santander_credentials(credentials)
            elif bank_id == "bb":
                return await self._validate_bb_credentials(credentials)
            elif bank_id == "nubank":
                return await self._validate_nubank_credentials(credentials)
            elif bank_id == "inter":
                return await self._validate_inter_credentials(credentials)
            else:
                return {"valid": False, "error": "Banco não suportado"}
                
        except Exception as e:
            logger.error(f"Erro na validação de credenciais para {bank_id}: {e}")
            return {"valid": False, "error": str(e)}
    
    async def _validate_itau_credentials(self, credentials: dict) -> dict:
        """Valida credenciais do Itaú."""
        
        required_fields = ["client_id", "client_secret", "redirect_uri"]
        
        # Verificar campos obrigatórios
        for field in required_fields:
            if not credentials.get(field):
                return {"valid": False, "error": f"Campo obrigatório: {field}"}
        
        # Testar autenticação (simulado)
        try:
            # Em produção, faria requisição real para o endpoint de auth
            await asyncio.sleep(1)  # Simular latência
            
            # Simular validação
            if len(credentials["client_id"]) < 10:
                return {"valid": False, "error": "Client ID inválido"}
            
            return {
                "valid": True,
                "message": "Credenciais válidas",
                "sandbox": credentials.get("sandbox", False)
            }
            
        except Exception as e:
            return {"valid": False, "error": f"Erro na validação: {str(e)}"}
    
    async def _validate_bradesco_credentials(self, credentials: dict) -> dict:
        """Valida credenciais do Bradesco."""
        
        required_fields = ["client_id", "client_secret", "certificate"]
        
        for field in required_fields:
            if not credentials.get(field):
                return {"valid": False, "error": f"Campo obrigatório: {field}"}
        
        # Validar certificado
        try:
            cert_data = base64.b64decode(credentials["certificate"])
            # Em produção, validaria o certificado
            
            return {
                "valid": True,
                "message": "Credenciais e certificado válidos"
            }
            
        except Exception as e:
            return {"valid": False, "error": f"Certificado inválido: {str(e)}"}
    
    async def _validate_santander_credentials(self, credentials: dict) -> dict:
        """Valida credenciais do Santander."""
        
        required_fields = ["client_id", "client_secret", "api_key"]
        
        for field in required_fields:
            if not credentials.get(field):
                return {"valid": False, "error": f"Campo obrigatório: {field}"}
        
        return {"valid": True, "message": "Credenciais válidas"}
    
    async def _validate_bb_credentials(self, credentials: dict) -> dict:
        """Valida credenciais do Banco do Brasil."""
        
        required_fields = ["client_id", "client_secret", "developer_key"]
        
        for field in required_fields:
            if not credentials.get(field):
                return {"valid": False, "error": f"Campo obrigatório: {field}"}
        
        return {"valid": True, "message": "Credenciais válidas"}
    
    async def _validate_nubank_credentials(self, credentials: dict) -> dict:
        """Valida credenciais do Nubank."""
        
        required_fields = ["cpf", "password"]
        
        for field in required_fields:
            if not credentials.get(field):
                return {"valid": False, "error": f"Campo obrigatório: {field}"}
        
        # Validar formato do CPF
        cpf = credentials["cpf"].replace(".", "").replace("-", "")
        if len(cpf) != 11 or not cpf.isdigit():
            return {"valid": False, "error": "CPF inválido"}
        
        return {
            "valid": True,
            "message": "Credenciais válidas",
            "warning": "API não oficial - pode parar de funcionar"
        }
    
    async def _validate_inter_credentials(self, credentials: dict) -> dict:
        """Valida credenciais do Inter."""
        
        required_fields = ["client_id", "client_secret", "certificate"]
        
        for field in required_fields:
            if not credentials.get(field):
                return {"valid": False, "error": f"Campo obrigatório: {field}"}
        
        return {"valid": True, "message": "Credenciais válidas"}
    
    def create_bank_config(self, user_id: str, config_data: dict) -> dict:
        """Cria nova configuração de banco."""
        
        try:
            # Criptografar credenciais
            encrypted_credentials = self._encrypt_credentials(config_data["credentials"])
            
            # Criar configuração (em produção, salvaria no banco)
            config_id = f"config_{user_id}_{config_data['bank_id']}_{int(datetime.now().timestamp())}"
            
            config = {
                "id": config_id,
                "user_id": user_id,
                "bank_id": config_data["bank_id"],
                "bank_name": config_data["bank_name"],
                "api_type": config_data["api_type"],
                "auth_type": config_data["auth_type"],
                "encrypted_credentials": encrypted_credentials,
                "sync_settings": config_data["sync_settings"],
                "endpoints": config_data["endpoints"],
                "status": "configured",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "last_sync": None
            }
            
            # Salvar no cache (em produção, salvaria no banco)
            self._config_cache[config_id] = config
            
            # Retornar sem credenciais
            return {
                "id": config["id"],
                "bank_id": config["bank_id"],
                "bank_name": config["bank_name"],
                "api_type": config["api_type"],
                "auth_type": config["auth_type"],
                "status": config["status"],
                "created_at": config["created_at"],
                "updated_at": config["updated_at"],
                "last_sync": config["last_sync"],
                "sync_settings": config["sync_settings"]
            }
            
        except Exception as e:
            logger.error(f"Erro ao criar configuração: {e}")
            raise
    
    def get_user_bank_configs(self, user_id: str) -> List[dict]:
        """Lista configurações de bancos do usuário."""
        
        # Em produção, buscaria do banco de dados
        user_configs = []
        
        for config_id, config in self._config_cache.items():
            if config["user_id"] == user_id:
                user_configs.append({
                    "id": config["id"],
                    "bank_id": config["bank_id"],
                    "bank_name": config["bank_name"],
                    "api_type": config["api_type"],
                    "auth_type": config["auth_type"],
                    "status": config["status"],
                    "created_at": config["created_at"],
                    "updated_at": config["updated_at"],
                    "last_sync": config["last_sync"],
                    "sync_settings": config["sync_settings"]
                })
        
        return user_configs
    
    def get_bank_config(self, config_id: str, user_id: str) -> Optional[dict]:
        """Busca configuração específica."""
        
        config = self._config_cache.get(config_id)
        
        if config and config["user_id"] == user_id:
            return {
                "id": config["id"],
                "bank_id": config["bank_id"],
                "bank_name": config["bank_name"],
                "api_type": config["api_type"],
                "auth_type": config["auth_type"],
                "status": config["status"],
                "created_at": config["created_at"],
                "updated_at": config["updated_at"],
                "last_sync": config["last_sync"],
                "sync_settings": config["sync_settings"]
            }
        
        return None
    
    def update_bank_config(self, config_id: str, user_id: str, update_data: dict) -> dict:
        """Atualiza configuração de banco."""
        
        config = self._config_cache.get(config_id)
        
        if not config or config["user_id"] != user_id:
            raise ValueError("Configuração não encontrada")
        
        # Atualizar campos
        if "credentials" in update_data:
            config["encrypted_credentials"] = self._encrypt_credentials(update_data["credentials"])
        
        if "sync_settings" in update_data:
            config["sync_settings"] = update_data["sync_settings"]
        
        config["updated_at"] = datetime.now()
        
        # Salvar no cache
        self._config_cache[config_id] = config
        
        return self.get_bank_config(config_id, user_id)
    
    def delete_bank_config(self, config_id: str, user_id: str) -> bool:
        """Remove configuração de banco."""
        
        config = self._config_cache.get(config_id)
        
        if config and config["user_id"] == user_id:
            del self._config_cache[config_id]
            return True
        
        return False
    
    async def test_connection(self, config_id: str) -> dict:
        """Testa conexão com o banco."""
        
        config = self._config_cache.get(config_id)
        if not config:
            return {"success": False, "message": "Configuração não encontrada"}
        
        try:
            # Descriptografar credenciais
            credentials = self._decrypt_credentials(config["encrypted_credentials"])
            
            # Testar conexão específica por banco
            bank_id = config["bank_id"]
            
            start_time = datetime.now()
            
            if bank_id == "itau":
                result = await self._test_itau_connection(credentials, config["endpoints"])
            elif bank_id == "nubank":
                result = await self._test_nubank_connection(credentials)
            else:
                # Teste genérico para outros bancos
                result = await self._test_generic_connection(credentials, config["endpoints"])
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            result["response_time"] = response_time
            return result
            
        except Exception as e:
            logger.error(f"Erro ao testar conexão: {e}")
            return {"success": False, "message": str(e)}
    
    async def _test_itau_connection(self, credentials: dict, endpoints: dict) -> dict:
        """Testa conexão com Itaú."""
        
        try:
            # Simular autenticação OAuth2
            await asyncio.sleep(1)
            
            # Simular resposta de sucesso
            return {
                "success": True,
                "message": "Conexão estabelecida com sucesso",
                "account_info": {
                    "bank": "Itaú Unibanco",
                    "agency": "1234",
                    "account": "56789-0",
                    "balance": "R$ 1.234,56"
                }
            }
            
        except Exception as e:
            return {"success": False, "message": f"Erro na conexão: {str(e)}"}
    
    async def _test_nubank_connection(self, credentials: dict) -> dict:
        """Testa conexão com Nubank."""
        
        try:
            # Simular login
            await asyncio.sleep(2)
            
            return {
                "success": True,
                "message": "Login realizado com sucesso",
                "account_info": {
                    "bank": "Nubank",
                    "account_type": "Conta Digital",
                    "balance": "R$ 987,65"
                }
            }
            
        except Exception as e:
            return {"success": False, "message": f"Erro no login: {str(e)}"}
    
    async def _test_generic_connection(self, credentials: dict, endpoints: dict) -> dict:
        """Teste genérico para outros bancos."""
        
        try:
            await asyncio.sleep(1.5)
            
            return {
                "success": True,
                "message": "Conexão testada com sucesso",
                "account_info": {
                    "status": "connected"
                }
            }
            
        except Exception as e:
            return {"success": False, "message": f"Erro na conexão: {str(e)}"}
    
    def is_sync_in_progress(self, config_id: str) -> bool:
        """Verifica se há sincronização em andamento."""
        
        status = self._sync_status.get(config_id, {})
        return status.get("status") == "in_progress"
    
    async def sync_bank_data(self, config_id: str, user_id: str, days: int, force: bool = False):
        """Sincroniza dados do banco."""
        
        config = self._config_cache.get(config_id)
        if not config or config["user_id"] != user_id:
            logger.error(f"Configuração não encontrada: {config_id}")
            return
        
        # Marcar como em progresso
        self._sync_status[config_id] = {
            "status": "in_progress",
            "started_at": datetime.now(),
            "progress": 0
        }
        
        try:
            logger.info(f"Iniciando sincronização para {config['bank_name']}")
            
            # Descriptografar credenciais
            credentials = self._decrypt_credentials(config["encrypted_credentials"])
            
            # Sincronizar por banco
            bank_id = config["bank_id"]
            
            if bank_id == "itau":
                result = await self._sync_itau_data(credentials, config["endpoints"], days)
            elif bank_id == "nubank":
                result = await self._sync_nubank_data(credentials, days)
            else:
                result = await self._sync_generic_data(credentials, config["endpoints"], days)
            
            # Atualizar status
            self._sync_status[config_id] = {
                "status": "completed",
                "started_at": self._sync_status[config_id]["started_at"],
                "completed_at": datetime.now(),
                "transactions_imported": result["transactions_imported"],
                "success": True
            }
            
            # Atualizar última sincronização
            config["last_sync"] = datetime.now()
            self._config_cache[config_id] = config
            
            logger.info(f"Sincronização concluída: {result['transactions_imported']} transações")
            
        except Exception as e:
            logger.error(f"Erro na sincronização: {e}")
            
            self._sync_status[config_id] = {
                "status": "error",
                "started_at": self._sync_status[config_id]["started_at"],
                "completed_at": datetime.now(),
                "error_message": str(e),
                "success": False
            }
    
    async def _sync_itau_data(self, credentials: dict, endpoints: dict, days: int) -> dict:
        """Sincroniza dados do Itaú."""
        
        try:
            # Simular busca de transações
            await asyncio.sleep(3)
            
            # Simular transações importadas
            transactions_imported = 25
            
            return {
                "transactions_imported": transactions_imported,
                "accounts_synced": 1
            }
            
        except Exception as e:
            raise Exception(f"Erro na sincronização Itaú: {str(e)}")
    
    async def _sync_nubank_data(self, credentials: dict, days: int) -> dict:
        """Sincroniza dados do Nubank."""
        
        try:
            await asyncio.sleep(2)
            
            transactions_imported = 18
            
            return {
                "transactions_imported": transactions_imported,
                "accounts_synced": 1
            }
            
        except Exception as e:
            raise Exception(f"Erro na sincronização Nubank: {str(e)}")
    
    async def _sync_generic_data(self, credentials: dict, endpoints: dict, days: int) -> dict:
        """Sincronização genérica."""
        
        try:
            await asyncio.sleep(2.5)
            
            transactions_imported = 15
            
            return {
                "transactions_imported": transactions_imported,
                "accounts_synced": 1
            }
            
        except Exception as e:
            raise Exception(f"Erro na sincronização: {str(e)}")
    
    def get_sync_status(self, config_id: str) -> dict:
        """Busca status da sincronização."""
        
        status = self._sync_status.get(config_id, {})
        
        if not status:
            return {"status": "never_synced"}
        
        return status
    
    def get_sync_history(self, config_id: str, limit: int = 10) -> List[dict]:
        """Busca histórico de sincronizações."""
        
        # Em produção, buscaria do banco de dados
        # Por enquanto, retornar dados simulados
        
        history = [
            {
                "id": f"sync_{config_id}_1",
                "config_id": config_id,
                "started_at": datetime.now() - timedelta(hours=2),
                "completed_at": datetime.now() - timedelta(hours=2, minutes=-3),
                "status": "completed",
                "transactions_imported": 12,
                "duration_seconds": 180,
                "success": True
            },
            {
                "id": f"sync_{config_id}_2",
                "config_id": config_id,
                "started_at": datetime.now() - timedelta(days=1),
                "completed_at": datetime.now() - timedelta(days=1, minutes=-2),
                "status": "completed",
                "transactions_imported": 8,
                "duration_seconds": 120,
                "success": True
            }
        ]
        
        return history[:limit]
    
    def get_user_sync_summary(self, user_id: str) -> dict:
        """Busca resumo de sincronizações do usuário."""
        
        user_configs = self.get_user_bank_configs(user_id)
        
        total_configs = len(user_configs)
        active_configs = len([c for c in user_configs if c["status"] == "configured"])
        
        # Simular estatísticas
        total_syncs = total_configs * 5  # Média de 5 syncs por config
        successful_syncs = int(total_syncs * 0.9)  # 90% de sucesso
        total_transactions = successful_syncs * 15  # Média de 15 transações por sync
        
        return {
            "total_configs": total_configs,
            "active_configs": active_configs,
            "total_syncs": total_syncs,
            "successful_syncs": successful_syncs,
            "error_syncs": total_syncs - successful_syncs,
            "total_transactions_imported": total_transactions,
            "last_sync": datetime.now() - timedelta(hours=2) if total_configs > 0 else None
        }
    
    async def process_webhook(self, bank_id: str, payload: dict) -> dict:
        """Processa webhook de notificação do banco."""
        
        try:
            logger.info(f"Processando webhook do banco {bank_id}")
            
            # Processar payload específico do banco
            if bank_id == "itau":
                return await self._process_itau_webhook(payload)
            elif bank_id == "bradesco":
                return await self._process_bradesco_webhook(payload)
            else:
                return {"status": "ignored", "reason": "Banco não suportado"}
                
        except Exception as e:
            logger.error(f"Erro ao processar webhook: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _process_itau_webhook(self, payload: dict) -> dict:
        """Processa webhook do Itaú."""
        
        # Implementar lógica específica do Itaú
        return {"status": "processed", "bank": "itau"}
    
    async def _process_bradesco_webhook(self, payload: dict) -> dict:
        """Processa webhook do Bradesco."""
        
        # Implementar lógica específica do Bradesco
        return {"status": "processed", "bank": "bradesco"}

