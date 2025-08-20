# Finance App - Aplicação Financeira Inteligente

Uma aplicação completa de gestão financeira pessoal com análise inteligente usando LLM local (Ollama), interface moderna em Streamlit e backend robusto em FastAPI.

## 🚀 Características Principais

### 💡 Inteligência Artificial Local
- **LLM Local com Ollama**: Análise inteligente sem enviar dados para a nuvem
- **Categorização Automática**: IA categoriza transações automaticamente
- **Detecção de Padrões**: Identifica gastos recorrentes e tendências
- **Insights Personalizados**: Recomendações baseadas no seu perfil financeiro
- **Forecast Inteligente**: Previsões de gastos usando Prophet/ARIMA

### 📊 Análise Avançada
- **Dashboard Interativo**: Visualizações dinâmicas com Plotly
- **Análise de Tendências**: Gráficos de evolução temporal
- **Breakdown por Categorias**: Análise detalhada de gastos
- **Padrões de Comportamento**: Identificação de hábitos financeiros
- **Alertas Inteligentes**: Notificações sobre gastos anômalos

### 🔄 Importação Flexível
- **Múltiplos Formatos**: CSV, Excel (XLSX/XLS), OFX
- **🏦 APIs Bancárias**: Integração direta com Itaú, Bradesco, Santander, BB, Inter, Nubank
- **Sincronização Automática**: Importação automática de transações dos bancos
- **Processamento em Lote**: Upload e processamento assíncrono
- **Detecção de Duplicatas**: Evita importação de dados duplicados
- **Validação Inteligente**: Verificação automática de dados
- **Histórico de Importações**: Rastreamento completo de uploads

### 🏗️ Arquitetura Robusta
- **Backend FastAPI**: API REST moderna e performática
- **PostgreSQL**: Banco de dados robusto e escalável
- **Redis**: Cache e processamento assíncrono
- **Docker**: Containerização completa
- **Streamlit**: Interface web intuitiva e responsiva

## 📋 Pré-requisitos

### Sistema Operacional
- **Ubuntu 20.04+ (Recomendado)**
- Outras distribuições Linux (com adaptações)
- macOS (com Homebrew)
- Windows (com WSL2)

### Hardware Mínimo
- **CPU**: 4 cores (8 cores recomendado para LLM)
- **RAM**: 8GB (16GB+ recomendado para LLM)
- **Armazenamento**: 20GB livres (SSD recomendado)
- **GPU**: Opcional (NVIDIA para aceleração de LLM)

### Software Base
- Python 3.9+
- PostgreSQL 12+
- Redis 6+
- Docker & Docker Compose (opcional)
- Git

## 🛠️ Instalação

### Opção 1: Instalação Automática (Recomendada)

```bash
# 1. Clonar o repositório
git clone <repository-url>
cd finance_app

# 2. Executar setup automático
chmod +x scripts/setup_ubuntu.sh
sudo ./scripts/setup_ubuntu.sh

# 3. Configurar banco de dados
chmod +x scripts/setup_database.sh
./scripts/setup_database.sh

# 4. Configurar Ollama (opcional, para IA)
chmod +x scripts/configure_ollama.sh
./scripts/configure_ollama.sh

# 5. Iniciar aplicação
chmod +x scripts/start_all.sh
./scripts/start_all.sh
```

### Opção 2: Docker Compose

```bash
# 1. Clonar e configurar
git clone <repository-url>
cd finance_app

# 2. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações

# 3. Iniciar com Docker
docker-compose up -d

# 4. Aguardar inicialização
docker-compose logs -f
```

### Opção 3: Instalação Manual

```bash
# 1. Instalar dependências do sistema
sudo apt update
sudo apt install -y python3-pip python3-venv postgresql redis-server

# 2. Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependências Python
pip install -r requirements.txt

# 4. Configurar PostgreSQL
sudo -u postgres createuser -s finance_user
sudo -u postgres createdb finance_app -O finance_user

# 5. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env

# 6. Inicializar banco
python -c "from src.models.database import init_db; init_db()"

# 7. Iniciar serviços
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

## 🎯 Uso Rápido

### 1. Acessar a Aplicação
- **Interface Web**: http://localhost:8501
- **API Backend**: http://localhost:8000
- **Documentação da API**: http://localhost:8000/docs

### 2. Primeira Configuração
1. Acesse a interface web
2. Vá para a página "🤖 LLM" para configurar a IA
3. Importe suas transações na página "📤 Import"
4. Explore os analytics na página "📊 Analytics"

### 3. Importar Dados
```bash
# Gerar dados de exemplo
python scripts/generate_sample_data.py --transactions 1000

# Ou usar o template CSV
# Baixe o template na interface web e preencha com seus dados
```

## 📁 Estrutura do Projeto

```
finance_app/
├── src/                          # Código fonte principal
│   ├── api/                      # FastAPI backend
│   │   ├── main.py              # Aplicação principal
│   │   ├── routes/              # Rotas da API
│   │   └── middleware/          # Middlewares
│   ├── models/                   # Modelos de dados
│   │   ├── database.py          # Configuração do banco
│   │   ├── transactions.py      # Modelo de transações
│   │   └── categories.py        # Modelo de categorias
│   ├── services/                 # Serviços de negócio
│   │   ├── llm_service.py       # Integração com Ollama
│   │   ├── recurring_detector.py # Detecção de recorrências
│   │   └── forecast_service.py   # Previsões financeiras
│   └── config/                   # Configurações
│       └── settings.py          # Settings da aplicação
├── pages/                        # Páginas Streamlit
│   ├── 1_📊_Analytics.py        # Página de analytics
│   ├── 2_📤_Import.py           # Página de importação
│   └── 3_🤖_LLM.py             # Página de configuração IA
├── scripts/                      # Scripts de automação
│   ├── setup_ubuntu.sh         # Setup completo Ubuntu
│   ├── setup_database.sh       # Configuração do banco
│   ├── configure_ollama.sh     # Configuração Ollama
│   ├── start_all.sh            # Iniciar todos os serviços
│   ├── stop_all.sh             # Parar todos os serviços
│   ├── backup_database.sh      # Backup do banco
│   ├── restore_database.sh     # Restore do banco
│   ├── monitor_system.sh       # Monitoramento
│   └── generate_sample_data.py # Gerador de dados
├── tests/                        # Testes automatizados
│   ├── test_api.py              # Testes da API
│   └── test_services.py         # Testes dos serviços
├── streamlit_app.py             # Aplicação Streamlit principal
├── requirements.txt             # Dependências Python
├── docker-compose.yml           # Configuração Docker
├── Dockerfile                   # Imagem Docker
└── .env.example                 # Exemplo de variáveis de ambiente
```

## 🔧 Configuração

### Variáveis de Ambiente (.env)

```bash
# Banco de Dados
DATABASE_URL=postgresql://finance_user:password@localhost/finance_app
POSTGRES_USER=finance_user
POSTGRES_PASSWORD=password
POSTGRES_DB=finance_app

# Redis
REDIS_URL=redis://localhost:6379/0

# Ollama (IA)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama2

# API
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=your-secret-key-here

# Streamlit
STREAMLIT_HOST=0.0.0.0
STREAMLIT_PORT=8501

# Logs
LOG_LEVEL=INFO
LOG_FILE=/var/log/finance_app/app.log

# Backup
BACKUP_DIR=/var/backups/finance_app
BACKUP_RETENTION_DAYS=30
```

### Configuração do Ollama

```bash
# Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Iniciar serviço
ollama serve

# Baixar modelo (escolha um)
ollama pull llama2          # Modelo geral (7B)
ollama pull codellama       # Especializado em código
ollama pull mistral         # Alternativa eficiente
ollama pull llama2:13b      # Modelo maior (melhor qualidade)

# Verificar modelos instalados
ollama list
```

## 📊 Funcionalidades Detalhadas

### Dashboard Principal
- **Resumo Financeiro**: Saldo atual, receitas, despesas
- **Gráficos Interativos**: Evolução temporal, distribuição por categoria
- **Métricas Chave**: KPIs financeiros importantes
- **Alertas**: Notificações sobre gastos anômalos

### Análise de Transações
- **Filtros Avançados**: Por data, categoria, valor, tipo
- **Busca Inteligente**: Pesquisa por descrição ou estabelecimento
- **Edição em Lote**: Modificação de múltiplas transações
- **Exportação**: Download em CSV, Excel, PDF

### Categorização Inteligente
- **IA Automática**: Categorização usando LLM local
- **Aprendizado**: Melhora com feedback do usuário
- **Regras Customizadas**: Definição de regras específicas
- **Subcategorias**: Organização hierárquica detalhada

### Detecção de Recorrências
- **Padrões Automáticos**: Identifica gastos regulares
- **Previsões**: Antecipa próximas ocorrências
- **Alertas**: Notifica sobre variações nos padrões
- **Orçamento**: Planejamento baseado em recorrências

### Importação de Dados
- **Formatos Múltiplos**: CSV, Excel, OFX, QIF
- **Validação**: Verificação automática de dados
- **Mapeamento**: Configuração de campos personalizados
- **Histórico**: Rastreamento de todas as importações

### Analytics Avançados
- **Tendências**: Análise temporal de gastos e receitas
- **Comparações**: Períodos, categorias, estabelecimentos
- **Projeções**: Previsões usando modelos estatísticos
- **Insights**: Recomendações personalizadas da IA

## 🔒 Segurança e Privacidade

### Dados Locais
- **IA Local**: Processamento com Ollama, sem envio para nuvem
- **Banco Local**: PostgreSQL na sua máquina
- **Sem Telemetria**: Nenhum dado enviado para terceiros
- **Controle Total**: Você possui todos os seus dados

### Segurança Técnica
- **Validação de Entrada**: Sanitização de todos os inputs
- **SQL Injection**: Proteção com SQLAlchemy ORM
- **XSS Protection**: Escape de conteúdo dinâmico
- **Rate Limiting**: Proteção contra ataques de força bruta

### Backup e Recuperação
- **Backup Automático**: Scripts de backup regulares
- **Versionamento**: Múltiplas versões de backup
- **Restore Simples**: Recuperação com um comando
- **Integridade**: Verificação de dados nos backups

## 🚀 Performance e Otimização

### Banco de Dados
- **Índices Otimizados**: Consultas rápidas
- **Particionamento**: Tabelas grandes divididas por data
- **Cache Redis**: Consultas frequentes em cache
- **Connection Pooling**: Gerenciamento eficiente de conexões

### Interface Web
- **Lazy Loading**: Carregamento sob demanda
- **Paginação**: Listas grandes divididas
- **Cache Frontend**: Dados frequentes em cache
- **Compressão**: Assets otimizados

### IA e LLM
- **Modelos Locais**: Sem latência de rede
- **GPU Acceleration**: Suporte NVIDIA CUDA
- **Batch Processing**: Processamento em lote eficiente
- **Model Caching**: Modelos carregados em memória

## 🔧 Manutenção

### Comandos Úteis

```bash
# Iniciar todos os serviços
./scripts/start_all.sh

# Parar todos os serviços
./scripts/stop_all.sh

# Monitorar sistema
./scripts/monitor_system.sh

# Backup do banco
./scripts/backup_database.sh

# Restore do banco
./scripts/restore_database.sh --latest

# Gerar dados de teste
python scripts/generate_sample_data.py --transactions 1000

# Executar testes
pytest tests/ -v

# Ver logs
tail -f /var/log/finance_app/*.log
```

### Monitoramento
- **Health Checks**: Verificação automática de serviços
- **Métricas**: CPU, memória, disco, rede
- **Logs Centralizados**: Todos os logs em um local
- **Alertas**: Notificações sobre problemas

### Atualizações
```bash
# Atualizar código
git pull origin main

# Atualizar dependências
pip install -r requirements.txt --upgrade

# Migrar banco (se necessário)
alembic upgrade head

# Reiniciar serviços
./scripts/stop_all.sh && ./scripts/start_all.sh
```

## 🐛 Solução de Problemas

### Problemas Comuns

#### Ollama não inicia
```bash
# Verificar se está instalado
ollama --version

# Reinstalar se necessário
curl -fsSL https://ollama.ai/install.sh | sh

# Iniciar manualmente
ollama serve

# Verificar logs
journalctl -u ollama -f
```

#### PostgreSQL não conecta
```bash
# Verificar status
sudo systemctl status postgresql

# Reiniciar serviço
sudo systemctl restart postgresql

# Verificar configuração
sudo -u postgres psql -c "\l"

# Recriar usuário se necessário
sudo -u postgres createuser -s finance_user
```

#### Streamlit não carrega
```bash
# Verificar porta
netstat -tuln | grep 8501

# Verificar logs
tail -f /var/log/finance_app/streamlit.log

# Reiniciar manualmente
pkill -f streamlit
streamlit run streamlit_app.py --server.port 8501
```

#### FastAPI com erro 500
```bash
# Verificar logs
tail -f /var/log/finance_app/fastapi.log

# Testar conexão com banco
python -c "from src.models.database import engine; print(engine.execute('SELECT 1').scalar())"

# Reiniciar API
pkill -f uvicorn
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### Logs e Debugging
```bash
# Logs principais
tail -f /var/log/finance_app/app.log

# Logs do sistema
journalctl -f

# Logs específicos
tail -f /var/log/finance_app/fastapi.log
tail -f /var/log/finance_app/streamlit.log
tail -f /var/log/finance_app/ollama.log

# Debug mode
export LOG_LEVEL=DEBUG
./scripts/start_all.sh
```

## 🤝 Contribuição

### Como Contribuir
1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Padrões de Código
- **Python**: PEP 8, type hints, docstrings
- **SQL**: Nomes em snake_case, comentários
- **JavaScript**: ES6+, JSDoc para funções
- **Commits**: Conventional Commits

### Testes
```bash
# Executar todos os testes
pytest tests/ -v

# Testes com cobertura
pytest tests/ --cov=src --cov-report=html

# Testes específicos
pytest tests/test_api.py::TestTransactionsAPI -v
```

## 📄 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- **Ollama**: Por tornar LLMs locais acessíveis
- **Streamlit**: Interface web simples e poderosa
- **FastAPI**: Framework moderno e performático
- **PostgreSQL**: Banco de dados robusto e confiável
- **Plotly**: Visualizações interativas incríveis

## 📞 Suporte

- **Documentação**: [Wiki do projeto](wiki-url)
- **Issues**: [GitHub Issues](issues-url)
- **Discussões**: [GitHub Discussions](discussions-url)
- **Email**: support@finance-app.com

---

**Finance App** - Sua gestão financeira inteligente e privada 🚀

