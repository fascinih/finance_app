# 🏦 APIs Bancárias - Finance App

## 📋 Visão Geral

A Finance App oferece integração completa com APIs bancárias para importação automática de transações. Esta funcionalidade permite sincronizar dados diretamente dos bancos, eliminando a necessidade de importação manual.

## 🏛️ Bancos Suportados

### ✅ Open Banking (APIs Oficiais)

#### 🏦 Itaú Unibanco
- **Status**: Disponível
- **Tipo**: Open Banking OAuth2
- **Documentação**: https://developer.itau.com.br/
- **Campos Obrigatórios**:
  - Client ID
  - Client Secret  
  - Redirect URI
- **Campos Opcionais**:
  - Modo Sandbox

#### 🏛️ Bradesco
- **Status**: Disponível
- **Tipo**: Open Banking OAuth2 + Certificado
- **Documentação**: https://developers.bradesco.com.br/
- **Campos Obrigatórios**:
  - Client ID
  - Client Secret
  - Certificado Digital (.p12/.pfx)
- **Campos Opcionais**:
  - Modo Sandbox

#### 🔴 Santander
- **Status**: Disponível
- **Tipo**: Open Banking OAuth2
- **Documentação**: https://developer.santander.com.br/
- **Campos Obrigatórios**:
  - Client ID
  - Client Secret
  - API Key
- **Campos Opcionais**:
  - Modo Sandbox

#### 🟡 Banco do Brasil
- **Status**: Disponível
- **Tipo**: Open Banking OAuth2
- **Documentação**: https://developers.bb.com.br/
- **Campos Obrigatórios**:
  - Client ID
  - Client Secret
  - Developer Key
- **Campos Opcionais**:
  - Modo Sandbox

#### 🧡 Banco Inter
- **Status**: Disponível
- **Tipo**: Open Banking OAuth2 + Certificado
- **Documentação**: https://developers.bancointer.com.br/
- **Campos Obrigatórios**:
  - Client ID
  - Client Secret
  - Certificado Digital
- **Campos Opcionais**:
  - Modo Sandbox

### ⚠️ APIs Não Oficiais

#### 🟣 Nubank
- **Status**: Experimental
- **Tipo**: API Não Oficial
- **Documentação**: https://github.com/andreroggeri/pynubank
- **Campos Obrigatórios**:
  - CPF
  - Senha
- **Campos Opcionais**:
  - UUID do Dispositivo
- **⚠️ Aviso**: API não oficial pode parar de funcionar a qualquer momento

## 🚀 Como Configurar

### 1. Registrar-se como Desenvolvedor

Para bancos com Open Banking:

1. **Acesse o Portal do Desenvolvedor** do banco escolhido
2. **Crie uma conta** de desenvolvedor
3. **Aceite os termos** de uso da API
4. **Registre uma aplicação** nova
5. **Configure URLs** de callback/redirect
6. **Obtenha credenciais** (Client ID, Client Secret)

### 2. Configurar na Finance App

1. **Acesse a página "🏦 APIs"** na interface web
2. **Selecione o banco** desejado
3. **Clique em "Configurar"**
4. **Preencha as credenciais** obtidas
5. **Configure sincronização** (frequência, período)
6. **Teste a conexão** antes de salvar
7. **Salve a configuração**

### 3. Sincronizar Dados

- **Manual**: Clique em "Sincronizar" quando desejar
- **Automática**: Configure frequência (diária, 6h, 2h)
- **Histórico**: Defina quantos dias importar (1-90)

## 🔐 Segurança

### Criptografia de Credenciais
- **Fernet Encryption**: Credenciais criptografadas com chave única
- **Armazenamento Local**: Dados ficam apenas na sua máquina
- **Tokens Temporários**: Tokens de acesso têm validade limitada
- **Logs Seguros**: Credenciais nunca aparecem nos logs

### Boas Práticas
- ✅ Use senhas fortes nas contas bancárias
- ✅ Monitore regularmente as sincronizações
- ✅ Remova configurações não utilizadas
- ✅ Mantenha o sistema atualizado
- ✅ Use modo sandbox para testes

## 📊 Funcionalidades

### Sincronização Automática
- **Frequências**: Manual, Diária, 6h, 2h
- **Período**: 1 a 90 dias no passado
- **Filtros**: Incluir/excluir transações pendentes
- **Duplicatas**: Detecção automática de duplicatas

### Monitoramento
- **Status em Tempo Real**: Acompanhe o progresso
- **Histórico Completo**: Todas as sincronizações registradas
- **Alertas**: Notificações sobre erros ou problemas
- **Métricas**: Estatísticas de importação

### Processamento Inteligente
- **Categorização**: IA categoriza transações automaticamente
- **Recorrências**: Detecta padrões recorrentes
- **Validação**: Verifica integridade dos dados
- **Analytics**: Atualiza análises automaticamente

## 🛠️ APIs Disponíveis

### Configurações
```http
GET    /api/v1/banking/configs              # Listar configurações
POST   /api/v1/banking/configs              # Criar configuração
GET    /api/v1/banking/configs/{id}         # Buscar configuração
PUT    /api/v1/banking/configs/{id}         # Atualizar configuração
DELETE /api/v1/banking/configs/{id}         # Remover configuração
```

### Testes e Sincronização
```http
POST   /api/v1/banking/configs/{id}/test    # Testar conexão
POST   /api/v1/banking/configs/{id}/sync    # Sincronizar dados
GET    /api/v1/banking/configs/{id}/sync/status   # Status da sincronização
GET    /api/v1/banking/configs/{id}/sync/history  # Histórico de sincronizações
```

### Utilitários
```http
GET    /api/v1/banking/supported-banks      # Bancos suportados
GET    /api/v1/banking/sync/summary         # Resumo de sincronizações
POST   /api/v1/banking/sync/all             # Sincronizar todos os bancos
```

## 📝 Exemplos de Uso

### Configurar Itaú
```json
{
  "bank_id": "itau",
  "bank_name": "Itaú Unibanco",
  "api_type": "open_banking",
  "auth_type": "oauth2",
  "credentials": {
    "client_id": "seu_client_id",
    "client_secret": "seu_client_secret",
    "redirect_uri": "http://localhost:8501/callback",
    "sandbox": true
  },
  "sync_settings": {
    "auto_sync": true,
    "frequency": "Diária",
    "days": 30,
    "include_pending": false
  }
}
```

### Testar Conexão
```bash
curl -X POST "http://localhost:8000/api/v1/banking/configs/{config_id}/test" \
  -H "Authorization: Bearer {token}"
```

### Sincronizar Dados
```bash
curl -X POST "http://localhost:8000/api/v1/banking/configs/{config_id}/sync" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{"days": 30, "force": false}'
```

## 🔧 Configuração Avançada

### Variáveis de Ambiente
```bash
# Criptografia
ENCRYPTION_KEY=sua_chave_de_criptografia_base64

# Timeouts
BANKING_API_TIMEOUT=30
BANKING_SYNC_TIMEOUT=300

# Retry
BANKING_MAX_RETRIES=3
BANKING_RETRY_DELAY=5

# Cache
BANKING_CACHE_TTL=3600
```

### Certificados Digitais
Para bancos que exigem certificados:

1. **Obtenha o certificado** no portal do banco
2. **Converta para base64** se necessário
3. **Faça upload** na configuração
4. **Teste a conexão** para validar

### Webhooks (Futuro)
```http
POST /api/v1/banking/webhook/{bank_id}     # Receber notificações
```

## 🚨 Solução de Problemas

### Erros Comuns

#### "Credenciais inválidas"
- ✅ Verifique Client ID e Client Secret
- ✅ Confirme se está usando sandbox/produção correto
- ✅ Valide URLs de redirect
- ✅ Verifique se aplicação está ativa no banco

#### "Certificado inválido"
- ✅ Confirme formato do certificado (.p12/.pfx)
- ✅ Verifique se certificado não expirou
- ✅ Valide senha do certificado
- ✅ Teste certificado em outras ferramentas

#### "Timeout na conexão"
- ✅ Verifique conectividade com internet
- ✅ Confirme se API do banco está online
- ✅ Aumente timeout se necessário
- ✅ Tente novamente mais tarde

#### "Token expirado"
- ✅ Tokens são renovados automaticamente
- ✅ Verifique se credenciais ainda são válidas
- ✅ Reconfigure se necessário
- ✅ Contate suporte do banco se persistir

### Logs e Debug
```bash
# Ver logs de sincronização
tail -f /var/log/finance_app/banking.log

# Debug mode
export LOG_LEVEL=DEBUG
./scripts/start_all.sh

# Testar conexão manual
python -c "
from src.services.banking_service import BankingService
service = BankingService(db)
result = await service.test_connection('config_id')
print(result)
"
```

## 📈 Roadmap

### Próximas Funcionalidades
- ✅ **Webhooks**: Notificações em tempo real dos bancos
- ✅ **Mais Bancos**: Caixa, C6, Original, etc.
- ✅ **PIX**: Integração específica para transações PIX
- ✅ **Cartões**: Importação de faturas de cartão
- ✅ **Investimentos**: Dados de investimentos e rendimentos
- ✅ **Multi-conta**: Múltiplas contas do mesmo banco

### Melhorias Planejadas
- 🔄 **Sync Inteligente**: Apenas transações novas
- 📊 **Analytics Bancários**: Métricas específicas por banco
- 🔔 **Alertas Avançados**: Notificações personalizadas
- 🎯 **Categorização Bancária**: Usar categorias do próprio banco
- 🔐 **2FA**: Suporte a autenticação de dois fatores

## 📞 Suporte

### Documentação dos Bancos
- **Itaú**: https://developer.itau.com.br/
- **Bradesco**: https://developers.bradesco.com.br/
- **Santander**: https://developer.santander.com.br/
- **Banco do Brasil**: https://developers.bb.com.br/
- **Inter**: https://developers.bancointer.com.br/

### Comunidade
- **GitHub Issues**: Para reportar bugs
- **Discussions**: Para dúvidas e sugestões
- **Wiki**: Documentação detalhada
- **Email**: suporte@finance-app.com

---

**Nota**: Esta funcionalidade está em constante evolução. Novos bancos e recursos são adicionados regularmente. Mantenha a aplicação atualizada para ter acesso às últimas funcionalidades.

