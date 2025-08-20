#!/bin/bash

# Script para corrigir estrutura de arquivos da Finance App
# Execute este script no diretório onde estão todos os arquivos misturados

echo "🔧 Corrigindo estrutura de arquivos da Finance App..."

# Criar diretórios necessários
echo "📁 Criando diretórios..."
mkdir -p scripts
mkdir -p src/{api/{routes,middleware},models,services,config}
mkdir -p pages
mkdir -p tests
mkdir -p data
mkdir -p docs

# Mover scripts para pasta scripts/
echo "📜 Movendo scripts..."
[ -f "setup_ubuntu.sh" ] && mv setup_ubuntu.sh scripts/
[ -f "install_nvidia.sh" ] && mv install_nvidia.sh scripts/
[ -f "configure_ollama.sh" ] && mv configure_ollama.sh scripts/
[ -f "setup_database.sh" ] && mv setup_database.sh scripts/
[ -f "optimize_ssd.sh" ] && mv optimize_ssd.sh scripts/
[ -f "backup_database.sh" ] && mv backup_database.sh scripts/
[ -f "restore_database.sh" ] && mv restore_database.sh scripts/
[ -f "monitor_system.sh" ] && mv monitor_system.sh scripts/
[ -f "start_all.sh" ] && mv start_all.sh scripts/
[ -f "stop_all.sh" ] && mv stop_all.sh scripts/
[ -f "generate_sample_data.py" ] && mv generate_sample_data.py scripts/
[ -f "init_db.sql" ] && mv init_db.sql scripts/

# Mover páginas Streamlit
echo "📄 Movendo páginas..."
[ -f "1_📊_Analytics.py" ] && mv "1_📊_Analytics.py" pages/
[ -f "2_📤_Import.py" ] && mv "2_📤_Import.py" pages/
[ -f "3_🤖_LLM.py" ] && mv "3_🤖_LLM.py" pages/
[ -f "4_🏦_APIs.py" ] && mv "4_🏦_APIs.py" pages/

# Mover arquivos da API
echo "🔌 Movendo arquivos da API..."
[ -f "main.py" ] && mv main.py src/api/
[ -f "health.py" ] && mv health.py src/api/routes/
[ -f "transactions.py" ] && mv transactions.py src/api/routes/
[ -f "categories.py" ] && mv categories.py src/api/routes/
[ -f "analytics.py" ] && mv analytics.py src/api/routes/
[ -f "import_data.py" ] && mv import_data.py src/api/routes/
[ -f "banking_apis.py" ] && mv banking_apis.py src/api/routes/

# Mover middleware
echo "🛡️ Movendo middleware..."
[ -f "auth.py" ] && mv auth.py src/api/middleware/
[ -f "logging.py" ] && mv logging.py src/api/middleware/

# Mover modelos
echo "🗄️ Movendo modelos..."
[ -f "database.py" ] && mv database.py src/models/
[ -f "transactions.py" ] && [ ! -f "src/models/transactions.py" ] && cp transactions.py src/models/

# Mover serviços
echo "⚙️ Movendo serviços..."
[ -f "llm_service.py" ] && mv llm_service.py src/services/
[ -f "recurring_detector.py" ] && mv recurring_detector.py src/services/
[ -f "forecast_service.py" ] && mv forecast_service.py src/services/
[ -f "banking_service.py" ] && mv banking_service.py src/services/

# Mover configurações
echo "⚙️ Movendo configurações..."
[ -f "settings.py" ] && mv settings.py src/config/

# Mover testes
echo "🧪 Movendo testes..."
[ -f "test_api.py" ] && mv test_api.py tests/

# Criar arquivos __init__.py necessários
echo "📝 Criando arquivos __init__.py..."
touch src/__init__.py
touch src/api/__init__.py
touch src/api/routes/__init__.py
touch src/api/middleware/__init__.py
touch src/models/__init__.py
touch src/services/__init__.py
touch src/config/__init__.py
touch tests/__init__.py

# Tornar scripts executáveis
echo "🔐 Tornando scripts executáveis..."
chmod +x scripts/*.sh

# Verificar se arquivos principais existem
echo "✅ Verificando arquivos principais..."
if [ -f "streamlit_app.py" ]; then
    echo "✅ streamlit_app.py encontrado"
else
    echo "❌ streamlit_app.py não encontrado"
fi

if [ -f "requirements.txt" ]; then
    echo "✅ requirements.txt encontrado"
else
    echo "❌ requirements.txt não encontrado"
fi

if [ -f "docker-compose.yml" ]; then
    echo "✅ docker-compose.yml encontrado"
else
    echo "❌ docker-compose.yml não encontrado"
fi

if [ -f "scripts/setup_ubuntu.sh" ]; then
    echo "✅ scripts/setup_ubuntu.sh encontrado"
else
    echo "❌ scripts/setup_ubuntu.sh não encontrado"
fi

echo ""
echo "🎉 Estrutura corrigida com sucesso!"
echo ""
echo "📁 Estrutura final:"
echo "├── streamlit_app.py"
echo "├── requirements.txt"
echo "├── docker-compose.yml"
echo "├── scripts/"
echo "│   ├── setup_ubuntu.sh"
echo "│   ├── install_nvidia.sh"
echo "│   └── ..."
echo "├── src/"
echo "│   ├── api/"
echo "│   ├── models/"
echo "│   ├── services/"
echo "│   └── config/"
echo "├── pages/"
echo "│   ├── 1_📊_Analytics.py"
echo "│   └── ..."
echo "└── tests/"
echo ""
echo "🚀 Agora você pode executar:"
echo "   chmod +x scripts/setup_ubuntu.sh"
echo "   sudo ./scripts/setup_ubuntu.sh"

