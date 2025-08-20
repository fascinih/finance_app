#!/bin/bash

# Script para iniciar todos os serviços da Finance App após reinicialização
echo "🚀 Iniciando todos os serviços da Finance App..."

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[START-SERVICES]${NC} $1"
}

info() {
    echo -e "${BLUE}[START-SERVICES]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[START-SERVICES]${NC} $1"
}

error() {
    echo -e "${RED}[START-SERVICES]${NC} $1"
}

# Função para verificar se serviço está rodando
check_service() {
    if systemctl is-active --quiet $1; then
        log "✅ $1 já está rodando"
        return 0
    else
        warn "⚠️ $1 não está rodando"
        return 1
    fi
}

echo "=================================================="
echo -e "${BLUE}🔧 INICIANDO SERVIÇOS DA FINANCE APP${NC}"
echo "=================================================="

# 1. PostgreSQL
info "1️⃣ Verificando PostgreSQL..."
if ! check_service postgresql; then
    log "Iniciando PostgreSQL..."
    sudo systemctl start postgresql
    sleep 2
    if check_service postgresql; then
        log "✅ PostgreSQL iniciado com sucesso!"
    else
        error "❌ Falha ao iniciar PostgreSQL"
        exit 1
    fi
fi

# Verificar se banco finance_app existe
log "Verificando banco de dados finance_app..."
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw finance_app; then
    log "✅ Banco finance_app existe"
else
    warn "⚠️ Banco finance_app não existe, criando..."
    sudo -u postgres createdb finance_app
    log "✅ Banco finance_app criado"
fi

# 2. Redis (se instalado)
info "2️⃣ Verificando Redis..."
if command -v redis-server >/dev/null 2>&1; then
    if ! check_service redis-server; then
        log "Iniciando Redis..."
        sudo systemctl start redis-server
        sleep 1
        check_service redis-server && log "✅ Redis iniciado!" || warn "⚠️ Redis não iniciou (não crítico)"
    fi
else
    warn "⚠️ Redis não instalado (não crítico)"
fi

# 3. Ollama
info "3️⃣ Verificando Ollama..."
if command -v ollama >/dev/null 2>&1; then
    if ! pgrep -f "ollama serve" > /dev/null; then
        log "Iniciando Ollama..."
        nohup ollama serve > /dev/null 2>&1 &
        sleep 3
        if pgrep -f "ollama serve" > /dev/null; then
            log "✅ Ollama iniciado!"
            
            # Verificar modelos disponíveis
            log "Verificando modelos disponíveis..."
            ollama list | grep -v "NAME" | while read line; do
                if [ ! -z "$line" ]; then
                    model_name=$(echo $line | awk '{print $1}')
                    log "📦 Modelo disponível: $model_name"
                fi
            done
        else
            warn "⚠️ Ollama não iniciou corretamente"
        fi
    else
        log "✅ Ollama já está rodando"
    fi
else
    warn "⚠️ Ollama não instalado"
fi

echo ""
echo "=================================================="
echo -e "${GREEN}📊 RESUMO DOS SERVIÇOS${NC}"
echo "=================================================="

# Status final
info "Verificando status final dos serviços..."

# PostgreSQL
if systemctl is-active --quiet postgresql; then
    echo -e "🟢 PostgreSQL: ${GREEN}Rodando${NC}"
else
    echo -e "🔴 PostgreSQL: ${RED}Parado${NC}"
fi

# Redis
if command -v redis-server >/dev/null 2>&1 && systemctl is-active --quiet redis-server; then
    echo -e "🟢 Redis: ${GREEN}Rodando${NC}"
elif command -v redis-server >/dev/null 2>&1; then
    echo -e "🔴 Redis: ${RED}Parado${NC}"
else
    echo -e "⚪ Redis: ${YELLOW}Não instalado${NC}"
fi

# Ollama
if pgrep -f "ollama serve" > /dev/null; then
    echo -e "🟢 Ollama: ${GREEN}Rodando${NC}"
elif command -v ollama >/dev/null 2>&1; then
    echo -e "🔴 Ollama: ${RED}Parado${NC}"
else
    echo -e "⚪ Ollama: ${YELLOW}Não instalado${NC}"
fi

echo ""
echo "=================================================="
echo -e "${GREEN}🚀 PRÓXIMOS PASSOS${NC}"
echo "=================================================="

echo "1️⃣ Iniciar Backend FastAPI:"
echo "   ./start_backend.sh"
echo ""
echo "2️⃣ Iniciar Frontend Streamlit:"
echo "   ./start_simple.sh"
echo ""
echo "3️⃣ Ou iniciar tudo junto:"
echo "   ./start_full_app.sh"
echo ""
echo "🌐 Acessos:"
echo "   • Frontend: http://localhost:8501"
echo "   • Backend:  http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo ""
echo "✅ Serviços básicos iniciados com sucesso!"

