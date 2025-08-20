#!/bin/bash

# Script para corrigir instalação de dependências Python
echo "🔧 Corrigindo instalação de dependências Python..."

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[DEPS-FIX]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[DEPS-FIX]${NC} $1"
}

error() {
    echo -e "${RED}[DEPS-FIX]${NC} $1"
}

info() {
    echo -e "${BLUE}[DEPS-FIX]${NC} $1"
}

# Verificar se estamos no diretório correto
if [ ! -f "streamlit_app.py" ]; then
    error "Execute este script no diretório da Finance App"
    exit 1
fi

# Remover ambiente virtual problemático
if [ -d "venv" ]; then
    warn "Removendo ambiente virtual problemático..."
    rm -rf venv
fi

# Atualizar sistema
log "Atualizando sistema..."
sudo apt update

# Instalar dependências do sistema necessárias
log "Instalando dependências do sistema..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    pkg-config \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    python3-setuptools \
    python3-wheel

# Atualizar pip do sistema
log "Atualizando pip..."
python3 -m pip install --upgrade pip setuptools wheel

# Criar novo ambiente virtual
log "Criando novo ambiente virtual..."
python3 -m venv venv

# Ativar ambiente virtual
log "Ativando ambiente virtual..."
source venv/bin/activate

# Atualizar pip no venv
log "Atualizando pip no ambiente virtual..."
pip install --upgrade pip setuptools wheel

# Criar requirements simplificado
log "Criando requirements simplificado..."
cat > requirements_minimal.txt << 'EOF'
# Core essencial
streamlit==1.28.1
fastapi==0.104.1
uvicorn[standard]==0.24.0

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9

# Data processing
pandas==2.1.3
numpy==1.25.2
plotly==5.17.0

# Utilities
requests==2.31.0
python-dotenv==1.0.0
pydantic==2.5.0

# Development
pytest==7.4.3
EOF

# Instalar dependências essenciais primeiro
log "Instalando dependências essenciais..."
pip install streamlit fastapi uvicorn

# Instalar dependências de dados
log "Instalando dependências de dados..."
pip install pandas numpy plotly

# Instalar dependências de banco
log "Instalando dependências de banco..."
pip install sqlalchemy psycopg2-binary

# Instalar utilitários
log "Instalando utilitários..."
pip install requests python-dotenv pydantic

# Verificar instalações
log "Verificando instalações..."
python -c "import streamlit; print('✅ Streamlit:', streamlit.__version__)"
python -c "import fastapi; print('✅ FastAPI:', fastapi.__version__)"
python -c "import pandas; print('✅ Pandas:', pandas.__version__)"
python -c "import numpy; print('✅ Numpy:', numpy.__version__)"
python -c "import plotly; print('✅ Plotly:', plotly.__version__)"

# Desativar venv
deactivate

echo ""
echo "=================================================="
echo -e "${GREEN}✅ Dependências corrigidas com sucesso!${NC}"
echo ""
echo "Dependências instaladas:"
echo "• Streamlit (interface web)"
echo "• FastAPI (backend)"
echo "• Pandas/Numpy (processamento de dados)"
echo "• Plotly (gráficos)"
echo "• SQLAlchemy/psycopg2 (banco de dados)"
echo ""
echo "Para iniciar a aplicação:"
echo "• ./start_simple.sh"
echo "=================================================="

