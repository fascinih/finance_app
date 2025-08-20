#!/bin/bash

# Script para iniciar o backend FastAPI
echo "🚀 Iniciando Backend FastAPI..."

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

# Verificar se venv existe
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Ambiente virtual não encontrado${NC}"
    echo "Execute: ./fix_dependencies.sh"
    exit 1
fi

# Ativar ambiente virtual
echo -e "${GREEN}🔧 Ativando ambiente virtual...${NC}"
source venv/bin/activate

# Verificar se uvicorn está instalado
if ! command -v uvicorn &> /dev/null; then
    echo -e "${YELLOW}📦 Instalando uvicorn...${NC}"
    pip install uvicorn[standard]
fi

# Verificar se FastAPI está instalado
python -c "import fastapi" 2>/dev/null || {
    echo -e "${YELLOW}📦 Instalando FastAPI...${NC}"
    pip install fastapi
}

# Verificar estrutura de arquivos
if [ ! -f "src/api/main.py" ]; then
    echo -e "${RED}❌ Arquivo src/api/main.py não encontrado${NC}"
    echo "Verifique se a estrutura de arquivos está correta"
    exit 1
fi

# Verificar PostgreSQL
if sudo systemctl is-active --quiet postgresql; then
    echo -e "${GREEN}✅ PostgreSQL: Rodando${NC}"
else
    echo -e "${YELLOW}⚠️  PostgreSQL: Não rodando${NC}"
    echo "Iniciando PostgreSQL..."
    sudo systemctl start postgresql
fi

echo ""
echo "=================================================="
echo -e "${GREEN}🚀 Iniciando Backend FastAPI${NC}"
echo ""
echo -e "${GREEN}🔗 API:${NC} http://localhost:8000"
echo -e "${GREEN}📚 Docs:${NC} http://localhost:8000/docs"
echo -e "${GREEN}🔍 Health:${NC} http://localhost:8000/health"
echo ""
echo -e "${YELLOW}Para parar: Ctrl+C${NC}"
echo "=================================================="
echo ""

# Iniciar FastAPI com uvicorn
cd "$(pwd)"
python -m uvicorn src.api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info

