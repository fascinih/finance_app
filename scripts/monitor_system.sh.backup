#!/bin/bash

# Finance App - Script de Monitoramento do Sistema
# Monitora saúde dos serviços e recursos do sistema

set -e

# Configurações
LOG_FILE="/var/log/finance_app_monitor.log"
ALERT_EMAIL=""  # Configurar email para alertas
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
DISK_THRESHOLD=90

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para log
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
    echo -e "$1"
}

# Função para alertas
send_alert() {
    local message="$1"
    log_message "ALERT: $message"
    
    # Enviar email se configurado
    if [ -n "$ALERT_EMAIL" ]; then
        echo "$message" | mail -s "Finance App Alert" "$ALERT_EMAIL" 2>/dev/null || true
    fi
}

echo -e "${BLUE}=== Finance App - Monitor do Sistema ===${NC}"
log_message "Iniciando monitoramento do sistema"

# Verificar recursos do sistema
echo -e "${YELLOW}Verificando recursos do sistema...${NC}"

# CPU
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
CPU_USAGE_INT=${CPU_USAGE%.*}

if [ "$CPU_USAGE_INT" -gt "$CPU_THRESHOLD" ]; then
    send_alert "CPU usage high: ${CPU_USAGE}%"
    echo -e "${RED}⚠ CPU: ${CPU_USAGE}% (ALTO)${NC}"
else
    echo -e "${GREEN}✓ CPU: ${CPU_USAGE}%${NC}"
fi

# Memória
MEMORY_INFO=$(free | grep Mem)
MEMORY_TOTAL=$(echo $MEMORY_INFO | awk '{print $2}')
MEMORY_USED=$(echo $MEMORY_INFO | awk '{print $3}')
MEMORY_USAGE=$((MEMORY_USED * 100 / MEMORY_TOTAL))

if [ "$MEMORY_USAGE" -gt "$MEMORY_THRESHOLD" ]; then
    send_alert "Memory usage high: ${MEMORY_USAGE}%"
    echo -e "${RED}⚠ Memória: ${MEMORY_USAGE}% (ALTO)${NC}"
else
    echo -e "${GREEN}✓ Memória: ${MEMORY_USAGE}%${NC}"
fi

# Disco
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')

if [ "$DISK_USAGE" -gt "$DISK_THRESHOLD" ]; then
    send_alert "Disk usage high: ${DISK_USAGE}%"
    echo -e "${RED}⚠ Disco: ${DISK_USAGE}% (ALTO)${NC}"
else
    echo -e "${GREEN}✓ Disco: ${DISK_USAGE}%${NC}"
fi

# Verificar serviços
echo -e "${YELLOW}Verificando serviços...${NC}"

# PostgreSQL
if systemctl is-active --quiet postgresql; then
    echo -e "${GREEN}✓ PostgreSQL: Ativo${NC}"
    
    # Verificar conexão ao banco
    if psql -U finance_user -d finance_app -c '\q' 2>/dev/null; then
        echo -e "${GREEN}✓ Banco de dados: Conectável${NC}"
    else
        send_alert "Database connection failed"
        echo -e "${RED}✗ Banco de dados: Erro de conexão${NC}"
    fi
else
    send_alert "PostgreSQL service is down"
    echo -e "${RED}✗ PostgreSQL: Inativo${NC}"
fi

# Redis
if systemctl is-active --quiet redis-server; then
    echo -e "${GREEN}✓ Redis: Ativo${NC}"
    
    # Verificar conexão ao Redis
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Redis: Conectável${NC}"
    else
        send_alert "Redis connection failed"
        echo -e "${RED}✗ Redis: Erro de conexão${NC}"
    fi
else
    send_alert "Redis service is down"
    echo -e "${RED}✗ Redis: Inativo${NC}"
fi

# Ollama
if pgrep -x "ollama" > /dev/null; then
    echo -e "${GREEN}✓ Ollama: Ativo${NC}"
    
    # Verificar API do Ollama
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ollama API: Respondendo${NC}"
    else
        send_alert "Ollama API not responding"
        echo -e "${RED}✗ Ollama API: Não responde${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Ollama: Não está rodando${NC}"
fi

# FastAPI
if pgrep -f "uvicorn.*finance_app" > /dev/null; then
    echo -e "${GREEN}✓ FastAPI: Ativo${NC}"
    
    # Verificar health endpoint
    if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ FastAPI Health: OK${NC}"
    else
        send_alert "FastAPI health check failed"
        echo -e "${RED}✗ FastAPI Health: Falhou${NC}"
    fi
else
    echo -e "${YELLOW}⚠ FastAPI: Não está rodando${NC}"
fi

# Streamlit
if pgrep -f "streamlit.*finance_app" > /dev/null; then
    echo -e "${GREEN}✓ Streamlit: Ativo${NC}"
    
    # Verificar se a porta está aberta
    if netstat -tuln | grep -q ":8501"; then
        echo -e "${GREEN}✓ Streamlit Port: Aberta${NC}"
    else
        send_alert "Streamlit port not accessible"
        echo -e "${RED}✗ Streamlit Port: Fechada${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Streamlit: Não está rodando${NC}"
fi

# Verificar logs de erro
echo -e "${YELLOW}Verificando logs de erro...${NC}"

# Verificar logs do sistema
ERROR_COUNT=$(journalctl --since "1 hour ago" --priority=err | wc -l)
if [ "$ERROR_COUNT" -gt 10 ]; then
    send_alert "High error count in system logs: $ERROR_COUNT errors in last hour"
    echo -e "${RED}⚠ Logs do sistema: $ERROR_COUNT erros na última hora${NC}"
else
    echo -e "${GREEN}✓ Logs do sistema: $ERROR_COUNT erros na última hora${NC}"
fi

# Verificar espaço em diretórios importantes
echo -e "${YELLOW}Verificando espaço em diretórios...${NC}"

# Diretório de backups
BACKUP_DIR="/var/backups/finance_app"
if [ -d "$BACKUP_DIR" ]; then
    BACKUP_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
    BACKUP_COUNT=$(ls "$BACKUP_DIR"/*.gz 2>/dev/null | wc -l)
    echo -e "${BLUE}Backups: $BACKUP_COUNT arquivos, $BACKUP_SIZE${NC}"
else
    echo -e "${YELLOW}⚠ Diretório de backup não existe${NC}"
fi

# Diretório de logs
LOG_DIR="/var/log"
LOG_SIZE=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1)
echo -e "${BLUE}Logs: $LOG_SIZE${NC}"

# Verificar conectividade de rede
echo -e "${YELLOW}Verificando conectividade...${NC}"

# Teste de DNS
if nslookup google.com > /dev/null 2>&1; then
    echo -e "${GREEN}✓ DNS: Funcionando${NC}"
else
    send_alert "DNS resolution failed"
    echo -e "${RED}✗ DNS: Falhou${NC}"
fi

# Teste de conectividade externa
if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Internet: Conectado${NC}"
else
    send_alert "Internet connectivity failed"
    echo -e "${RED}✗ Internet: Desconectado${NC}"
fi

# Verificar atualizações de segurança
echo -e "${YELLOW}Verificando atualizações de segurança...${NC}"

SECURITY_UPDATES=$(apt list --upgradable 2>/dev/null | grep -i security | wc -l)
if [ "$SECURITY_UPDATES" -gt 0 ]; then
    send_alert "$SECURITY_UPDATES security updates available"
    echo -e "${YELLOW}⚠ $SECURITY_UPDATES atualizações de segurança disponíveis${NC}"
else
    echo -e "${GREEN}✓ Sistema atualizado${NC}"
fi

# Resumo final
echo -e "${BLUE}=== Resumo do Monitoramento ===${NC}"
echo -e "CPU: ${CPU_USAGE}% | Memória: ${MEMORY_USAGE}% | Disco: ${DISK_USAGE}%"
echo -e "Logs de erro: $ERROR_COUNT | Atualizações: $SECURITY_UPDATES"

# Salvar métricas para histórico
METRICS_FILE="/var/log/finance_app_metrics.csv"
if [ ! -f "$METRICS_FILE" ]; then
    echo "timestamp,cpu_usage,memory_usage,disk_usage,error_count" > "$METRICS_FILE"
fi

echo "$(date '+%Y-%m-%d %H:%M:%S'),$CPU_USAGE,$MEMORY_USAGE,$DISK_USAGE,$ERROR_COUNT" >> "$METRICS_FILE"

log_message "Monitoramento concluído"
echo -e "${GREEN}Monitoramento concluído. Logs salvos em: $LOG_FILE${NC}"

