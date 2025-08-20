#!/bin/bash

# Finance App - Inicialização Super Simples
echo "🚀 Iniciando Finance App (Versão Simples)..."

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Verificar se estamos no diretório correto
if [ ! -f "streamlit_app.py" ]; then
    echo -e "${RED}❌ Execute no diretório da Finance App${NC}"
    exit 1
fi

echo -e "${GREEN}📁 Diretório:${NC} $(pwd)"

# Verificar se venv existe
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Ambiente virtual não encontrado${NC}"
    echo "Execute primeiro: ./fix_dependencies.sh"
    exit 1
fi

# Ativar ambiente virtual
echo -e "${GREEN}🔧 Ativando ambiente virtual...${NC}"
source venv/bin/activate

# Verificar se streamlit está instalado
if ! command -v streamlit &> /dev/null; then
    echo -e "${RED}❌ Streamlit não instalado${NC}"
    echo "Execute: ./fix_dependencies.sh"
    exit 1
fi

# Verificar PostgreSQL (opcional)
if sudo systemctl is-active --quiet postgresql; then
    echo -e "${GREEN}✅ PostgreSQL:${NC} Rodando"
else
    echo -e "${YELLOW}⚠️  PostgreSQL:${NC} Não rodando (funcionalidade limitada)"
fi

# Verificar Ollama (opcional)
if command -v ollama &> /dev/null && pgrep -x "ollama" > /dev/null; then
    echo -e "${GREEN}✅ Ollama:${NC} Rodando"
else
    echo -e "${YELLOW}⚠️  Ollama:${NC} Não rodando (sem IA)"
fi

echo ""
echo "=================================================="
echo -e "${GREEN}🚀 Iniciando Finance App${NC}"
echo ""
echo -e "${GREEN}🌐 Interface:${NC} http://localhost:8501"
echo -e "${GREEN}📊 Dashboard:${NC} Análise financeira"
echo -e "${GREEN}📤 Import:${NC} Upload de dados"
echo -e "${GREEN}🤖 LLM:${NC} Inteligência artificial"
echo -e "${GREEN}🏦 APIs:${NC} Integração bancária"
echo ""
echo -e "${YELLOW}Para parar: Ctrl+C${NC}"
echo "=================================================="
echo ""

# Iniciar Streamlit
streamlit run streamlit_app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false

