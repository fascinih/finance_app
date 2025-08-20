#!/bin/bash

# Script simples para corrigir PostgreSQL
echo "🔧 Corrigindo PostgreSQL - Versão Simples..."

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[POSTGRES]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[POSTGRES]${NC} $1"
}

error() {
    echo -e "${RED}[POSTGRES]${NC} $1"
}

# Verificar se PostgreSQL está instalado
if ! command -v psql &> /dev/null; then
    error "PostgreSQL não instalado. Instalando..."
    sudo apt update
    sudo apt install -y postgresql postgresql-contrib
fi

# Iniciar serviço se não estiver rodando
if ! sudo systemctl is-active --quiet postgresql; then
    log "Iniciando PostgreSQL..."
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
fi

# Encontrar diretório real do PostgreSQL
log "Procurando diretório de configuração..."

POSTGRES_DIR=""
for dir in /etc/postgresql/*/main/; do
    if [ -d "$dir" ]; then
        POSTGRES_DIR="$dir"
        break
    fi
done

if [ -z "$POSTGRES_DIR" ]; then
    error "Diretório do PostgreSQL não encontrado"
    exit 1
fi

POSTGRES_CONF="${POSTGRES_DIR}postgresql.conf"
log "Encontrado: $POSTGRES_CONF"

# Verificar se arquivo existe
if [ ! -f "$POSTGRES_CONF" ]; then
    error "Arquivo de configuração não encontrado: $POSTGRES_CONF"
    exit 1
fi

# Fazer backup se não existe
if [ ! -f "$POSTGRES_CONF.backup" ]; then
    log "Criando backup..."
    sudo cp "$POSTGRES_CONF" "$POSTGRES_CONF.backup"
    log "Backup criado: $POSTGRES_CONF.backup"
else
    log "Backup já existe"
fi

# Verificar se já tem configurações da Finance App
if grep -q "Finance App" "$POSTGRES_CONF"; then
    log "Configurações já aplicadas"
else
    log "Aplicando configurações otimizadas..."
    
    # Adicionar configurações
    sudo tee -a "$POSTGRES_CONF" << 'EOF'

# ===========================================
# Otimizações para SSD - Finance App
# ===========================================

# Configurações de memória
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Configurações para SSD
random_page_cost = 1.1
seq_page_cost = 1.0
effective_io_concurrency = 200

# Configurações de checkpoint
checkpoint_completion_target = 0.9
wal_buffers = 16MB

# Configurações de conexão
max_connections = 100

EOF
fi

# Reiniciar PostgreSQL
log "Reiniciando PostgreSQL..."
sudo systemctl restart postgresql

# Verificar se funcionou
if sudo systemctl is-active --quiet postgresql; then
    log "PostgreSQL reiniciado com sucesso!"
else
    error "Falha ao reiniciar PostgreSQL"
    exit 1
fi

# Testar conexão
log "Testando conexão..."
if sudo -u postgres psql -c "SELECT 1;" > /dev/null 2>&1; then
    log "Conexão OK!"
else
    warn "Problema na conexão"
fi

# Mostrar informações
log "Informações do PostgreSQL:"
echo "• Versão: $(sudo -u postgres psql -t -c "SELECT version();" | head -1)"
echo "• Status: $(sudo systemctl is-active postgresql)"
echo "• Configuração: $POSTGRES_CONF"
echo "• Backup: $POSTGRES_CONF.backup"

echo ""
echo "=================================================="
echo -e "${GREEN}✅ PostgreSQL configurado com sucesso!${NC}"
echo ""
echo "Próximos passos:"
echo "1. ./scripts/setup_database.sh  # Configurar banco da Finance App"
echo "2. ./scripts/start_all.sh       # Iniciar aplicação completa"
echo "=================================================="

