#!/bin/bash

# Script para iniciar aplicação completa (Backend + Frontend)
echo "🚀 Iniciando Finance App Completa..."

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Verificar se estamos no diretório correto
if [ ! -f "streamlit_app.py" ]; then
    echo -e "${RED}❌ Execute no diretório da Finance App${NC}"
    exit 1
fi

# Verificar se venv existe
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Ambiente virtual não encontrado${NC}"
    echo "Execute: ./fix_dependencies.sh"
    exit 1
fi

# Função para cleanup ao sair
cleanup() {
    echo -e "\n${YELLOW}🛑 Parando serviços...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Capturar Ctrl+C
trap cleanup SIGINT SIGTERM

# Ativar ambiente virtual
source venv/bin/activate

# Verificar dependências essenciais
echo -e "${BLUE}🔍 Verificando dependências...${NC}"
python -c "import fastapi, uvicorn, streamlit" 2>/dev/null || {
    echo -e "${YELLOW}📦 Instalando dependências essenciais...${NC}"
    pip install fastapi uvicorn[standard] streamlit
}

# Verificar PostgreSQL
if sudo systemctl is-active --quiet postgresql; then
    echo -e "${GREEN}✅ PostgreSQL: Rodando${NC}"
else
    echo -e "${YELLOW}⚠️  Iniciando PostgreSQL...${NC}"
    sudo systemctl start postgresql
fi

# Verificar Ollama
if command -v ollama &> /dev/null && pgrep -x "ollama" > /dev/null; then
    echo -e "${GREEN}✅ Ollama: Rodando${NC}"
else
    echo -e "${YELLOW}⚠️  Ollama: Não rodando (IA desabilitada)${NC}"
fi

echo ""
echo "=================================================="
echo -e "${GREEN}🚀 Iniciando Finance App Completa${NC}"
echo ""
echo -e "${GREEN}🔗 Backend API:${NC} http://localhost:8000"
echo -e "${GREEN}📚 API Docs:${NC} http://localhost:8000/docs"
echo -e "${GREEN}🌐 Frontend:${NC} http://localhost:8501"
echo ""
echo -e "${YELLOW}Para parar: Ctrl+C${NC}"
echo "=================================================="
echo ""

# Iniciar Backend em background
echo -e "${BLUE}🔧 Iniciando Backend FastAPI...${NC}"
python -m uvicorn src.api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level warning &
BACKEND_PID=$!

# Aguardar backend iniciar
sleep 3

# Verificar se backend iniciou
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend iniciado com sucesso${NC}"
else
    echo -e "${YELLOW}⚠️  Backend pode estar iniciando...${NC}"
fi

# Iniciar Frontend
echo -e "${BLUE}🔧 Iniciando Frontend Streamlit...${NC}"
streamlit run streamlit_app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false &
FRONTEND_PID=$!

# Aguardar frontend iniciar
sleep 2

echo ""
echo -e "${GREEN}🎉 Finance App iniciada com sucesso!${NC}"
echo ""
echo -e "${GREEN}📊 Acesse:${NC} http://localhost:8501"
echo -e "${GREEN}🔗 API:${NC} http://localhost:8000/docs"
echo ""

# Manter script rodando
wait

