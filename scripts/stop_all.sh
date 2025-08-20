#!/bin/bash

# Finance App - Script para Parar Todos os Serviços
# Para todos os componentes da aplicação financeira

set -e

# Configurações
LOG_DIR="/var/log/finance_app"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Finance App - Parando Todos os Serviços ===${NC}"
echo "Iniciado em: $(date)"

# Função para log
log_message() {
    echo -e "$1"
    if [ -d "$LOG_DIR" ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_DIR/shutdown.log"
    fi
}

log_message "${YELLOW}Parando serviços da aplicação...${NC}"

# Parar Streamlit
log_message "${YELLOW}Parando Streamlit...${NC}"

if pgrep -f "streamlit.*finance_app" > /dev/null; then
    # Tentar parar graciosamente primeiro
    pkill -TERM -f "streamlit.*finance_app"
    sleep 3
    
    # Forçar se ainda estiver rodando
    if pgrep -f "streamlit.*finance_app" > /dev/null; then
        pkill -KILL -f "streamlit.*finance_app"
        sleep 1
    fi
    
    log_message "${GREEN}✓ Streamlit parado${NC}"
else
    log_message "${BLUE}Streamlit não estava rodando${NC}"
fi

# Parar FastAPI
log_message "${YELLOW}Parando FastAPI...${NC}"

if pgrep -f "uvicorn.*finance_app" > /dev/null; then
    # Tentar parar graciosamente primeiro
    pkill -TERM -f "uvicorn.*finance_app"
    sleep 3
    
    # Forçar se ainda estiver rodando
    if pgrep -f "uvicorn.*finance_app" > /dev/null; then
        pkill -KILL -f "uvicorn.*finance_app"
        sleep 1
    fi
    
    log_message "${GREEN}✓ FastAPI parado${NC}"
else
    log_message "${BLUE}FastAPI não estava rodando${NC}"
fi

# Parar Ollama (opcional)
log_message "${YELLOW}Verificando Ollama...${NC}"

if pgrep -x "ollama" > /dev/null; then
    read -p "Parar Ollama também? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_message "${YELLOW}Parando Ollama...${NC}"
        
        # Tentar parar graciosamente
        pkill -TERM -x "ollama"
        sleep 5
        
        # Forçar se ainda estiver rodando
        if pgrep -x "ollama" > /dev/null; then
            pkill -KILL -x "ollama"
            sleep 1
        fi
        
        log_message "${GREEN}✓ Ollama parado${NC}"
    else
        log_message "${BLUE}Ollama mantido em execução${NC}"
    fi
else
    log_message "${BLUE}Ollama não estava rodando${NC}"
fi

# Verificar se há processos Python relacionados ainda rodando
log_message "${YELLOW}Verificando processos Python relacionados...${NC}"

PYTHON_PROCS=$(pgrep -f "python.*finance" || true)
if [ -n "$PYTHON_PROCS" ]; then
    log_message "${YELLOW}Encontrados processos Python relacionados:${NC}"
    ps -p $PYTHON_PROCS -o pid,cmd || true
    
    read -p "Parar estes processos? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo $PYTHON_PROCS | xargs kill -TERM 2>/dev/null || true
        sleep 2
        
        # Verificar se ainda estão rodando
        REMAINING=$(pgrep -f "python.*finance" || true)
        if [ -n "$REMAINING" ]; then
            echo $REMAINING | xargs kill -KILL 2>/dev/null || true
        fi
        
        log_message "${GREEN}✓ Processos Python parados${NC}"
    fi
fi

# Limpar arquivos PID se existirem
log_message "${YELLOW}Limpando arquivos PID...${NC}"

if [ -f "$LOG_DIR/fastapi.pid" ]; then
    rm -f "$LOG_DIR/fastapi.pid"
    log_message "${BLUE}Arquivo PID do FastAPI removido${NC}"
fi

if [ -f "$LOG_DIR/streamlit.pid" ]; then
    rm -f "$LOG_DIR/streamlit.pid"
    log_message "${BLUE}Arquivo PID do Streamlit removido${NC}"
fi

# Verificar portas
log_message "${YELLOW}Verificando portas...${NC}"

# Porta 8000 (FastAPI)
if netstat -tuln | grep -q ":8000"; then
    log_message "${YELLOW}⚠ Porta 8000 ainda está em uso${NC}"
    netstat -tuln | grep ":8000"
else
    log_message "${GREEN}✓ Porta 8000 liberada${NC}"
fi

# Porta 8501 (Streamlit)
if netstat -tuln | grep -q ":8501"; then
    log_message "${YELLOW}⚠ Porta 8501 ainda está em uso${NC}"
    netstat -tuln | grep ":8501"
else
    log_message "${GREEN}✓ Porta 8501 liberada${NC}"
fi

# Opção para parar serviços do sistema
echo ""
read -p "Parar também PostgreSQL e Redis? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_message "${YELLOW}Parando serviços do sistema...${NC}"
    
    # Parar PostgreSQL
    if systemctl is-active --quiet postgresql; then
        log_message "${YELLOW}Parando PostgreSQL...${NC}"
        sudo systemctl stop postgresql
        log_message "${GREEN}✓ PostgreSQL parado${NC}"
    else
        log_message "${BLUE}PostgreSQL não estava rodando${NC}"
    fi
    
    # Parar Redis
    if systemctl is-active --quiet redis-server; then
        log_message "${YELLOW}Parando Redis...${NC}"
        sudo systemctl stop redis-server
        log_message "${GREEN}✓ Redis parado${NC}"
    else
        log_message "${BLUE}Redis não estava rodando${NC}"
    fi
else
    log_message "${BLUE}Serviços do sistema mantidos em execução${NC}"
fi

# Mostrar resumo final
log_message "${BLUE}=== Resumo do Shutdown ===${NC}"

# Verificar status final dos serviços
SERVICES_STATUS=""

if pgrep -f "streamlit.*finance_app" > /dev/null; then
    SERVICES_STATUS="${SERVICES_STATUS}${RED}✗ Streamlit ainda rodando${NC}\n"
else
    SERVICES_STATUS="${SERVICES_STATUS}${GREEN}✓ Streamlit parado${NC}\n"
fi

if pgrep -f "uvicorn.*finance_app" > /dev/null; then
    SERVICES_STATUS="${SERVICES_STATUS}${RED}✗ FastAPI ainda rodando${NC}\n"
else
    SERVICES_STATUS="${SERVICES_STATUS}${GREEN}✓ FastAPI parado${NC}\n"
fi

if pgrep -x "ollama" > /dev/null; then
    SERVICES_STATUS="${SERVICES_STATUS}${BLUE}ℹ Ollama ainda rodando${NC}\n"
else
    SERVICES_STATUS="${SERVICES_STATUS}${GREEN}✓ Ollama parado${NC}\n"
fi

if systemctl is-active --quiet postgresql; then
    SERVICES_STATUS="${SERVICES_STATUS}${BLUE}ℹ PostgreSQL ainda rodando${NC}\n"
else
    SERVICES_STATUS="${SERVICES_STATUS}${GREEN}✓ PostgreSQL parado${NC}\n"
fi

if systemctl is-active --quiet redis-server; then
    SERVICES_STATUS="${SERVICES_STATUS}${BLUE}ℹ Redis ainda rodando${NC}\n"
else
    SERVICES_STATUS="${SERVICES_STATUS}${GREEN}✓ Redis parado${NC}\n"
fi

echo -e "$SERVICES_STATUS"

# Mostrar comandos para reiniciar
echo ""
log_message "${BLUE}=== Para Reiniciar ===${NC}"
log_message "${YELLOW}Iniciar todos os serviços: bash scripts/start_all.sh${NC}"
log_message "${YELLOW}Iniciar apenas PostgreSQL: sudo systemctl start postgresql${NC}"
log_message "${YELLOW}Iniciar apenas Redis: sudo systemctl start redis-server${NC}"

log_message "${GREEN}=== Shutdown Concluído ===${NC}"
log_message "Finalizado em: $(date)"

echo ""
echo -e "${GREEN}🛑 Serviços da Finance App parados com sucesso!${NC}"

