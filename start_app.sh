#!/bin/bash

# Finance App - Inicialização Simples
# Funciona no diretório atual

echo "🚀 Iniciando Finance App..."

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[FINANCE-APP]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[FINANCE-APP]${NC} $1"
}

error() {
    echo -e "${RED}[FINANCE-APP]${NC} $1"
}

info() {
    echo -e "${BLUE}[FINANCE-APP]${NC} $1"
}

# Verificar se estamos no diretório correto
if [ ! -f "streamlit_app.py" ]; then
    error "Execute este script no diretório da Finance App"
    error "(onde está o arquivo streamlit_app.py)"
    exit 1
fi

CURRENT_DIR=$(pwd)
log "Diretório: $CURRENT_DIR"

# Verificar Python
if ! command -v python3 &> /dev/null; then
    error "Python3 não encontrado. Instale com: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

# Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    log "Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativar ambiente virtual
log "Ativando ambiente virtual..."
source venv/bin/activate

# Instalar dependências se necessário
if [ -f "requirements.txt" ]; then
    if ! pip list | grep -q "streamlit"; then
        log "Instalando dependências..."
        pip install -r requirements.txt
    else
        log "Dependências já instaladas"
    fi
fi

# Verificar PostgreSQL
log "Verificando PostgreSQL..."
if ! sudo systemctl is-active --quiet postgresql; then
    warn "PostgreSQL não está rodando. Tentando iniciar..."
    sudo systemctl start postgresql
    
    if sudo systemctl is-active --quiet postgresql; then
        log "PostgreSQL iniciado"
    else
        error "Falha ao iniciar PostgreSQL"
        error "Execute: sudo systemctl start postgresql"
    fi
else
    log "PostgreSQL rodando"
fi

# Verificar se banco existe
log "Verificando banco de dados..."
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw finance_app; then
    log "Banco 'finance_app' encontrado"
else
    warn "Banco 'finance_app' não encontrado"
    log "Criando banco..."
    
    # Criar usuário e banco
    sudo -u postgres createuser -s finance_user 2>/dev/null || true
    sudo -u postgres createdb finance_app -O finance_user 2>/dev/null || true
    
    log "Banco criado"
fi

# Verificar Ollama (opcional)
if command -v ollama &> /dev/null; then
    if pgrep -x "ollama" > /dev/null; then
        log "Ollama rodando"
    else
        warn "Ollama instalado mas não rodando"
        info "Para iniciar: ollama serve"
    fi
else
    warn "Ollama não instalado (opcional para IA)"
fi

# Iniciar aplicação Streamlit
log "Iniciando aplicação Streamlit..."
info "Acesse: http://localhost:8501"

echo ""
echo "=================================================="
echo -e "${GREEN}🚀 Finance App Iniciando...${NC}"
echo ""
echo "• Diretório: $CURRENT_DIR"
echo "• PostgreSQL: $(sudo systemctl is-active postgresql)"
echo "• Ollama: $(command -v ollama &> /dev/null && echo "Instalado" || echo "Não instalado")"
echo "• Interface: http://localhost:8501"
echo ""
echo "Para parar: Ctrl+C"
echo "=================================================="
echo ""

# Iniciar Streamlit
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0

