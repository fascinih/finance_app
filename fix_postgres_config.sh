#!/bin/bash

# Script para corrigir configuração do PostgreSQL
echo "🔧 Corrigindo configuração do PostgreSQL..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[POSTGRES-FIX]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[POSTGRES-FIX]${NC} $1"
}

error() {
    echo -e "${RED}[POSTGRES-FIX]${NC} $1"
    exit 1
}

# Verificar se PostgreSQL está instalado
if ! command -v psql &> /dev/null; then
    error "PostgreSQL não está instalado. Execute primeiro: sudo apt install postgresql postgresql-contrib"
fi

# Verificar se serviço está rodando
if ! sudo systemctl is-active --quiet postgresql; then
    log "Iniciando serviço PostgreSQL..."
    sudo systemctl start postgresql
fi

# Detectar versão do PostgreSQL
log "Detectando versão do PostgreSQL..."
POSTGRES_VERSION=$(sudo -u postgres psql -t -c "SELECT version();" 2>/dev/null | grep -oP '\d+\.\d+' | head -1)

if [ -z "$POSTGRES_VERSION" ]; then
    # Tentar detectar pela instalação
    POSTGRES_VERSION=$(ls /etc/postgresql/ 2>/dev/null | head -1)
fi

if [ -z "$POSTGRES_VERSION" ]; then
    error "Não foi possível detectar a versão do PostgreSQL"
fi

log "Versão detectada: $POSTGRES_VERSION"

# Definir caminho do arquivo de configuração
POSTGRES_CONF="/etc/postgresql/$POSTGRES_VERSION/main/postgresql.conf"

if [ ! -f "$POSTGRES_CONF" ]; then
    error "Arquivo de configuração não encontrado: $POSTGRES_CONF"
fi

log "Arquivo de configuração: $POSTGRES_CONF"

# Fazer backup se ainda não existe
if [ ! -f "$POSTGRES_CONF.backup" ]; then
    log "Criando backup da configuração original..."
    sudo cp "$POSTGRES_CONF" "$POSTGRES_CONF.backup"
    log "Backup criado: $POSTGRES_CONF.backup"
else
    log "Backup já existe: $POSTGRES_CONF.backup"
fi

# Aplicar otimizações para SSD
log "Aplicando otimizações para SSD..."

# Criar arquivo temporário com configurações
cat > /tmp/postgres_ssd_config << 'EOF'

# ===========================================
# Otimizações para SSD - Finance App
# ===========================================

# Configurações de memória (ajuste conforme sua RAM)
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Configurações para SSD
random_page_cost = 1.1
seq_page_cost = 1.0
effective_io_concurrency = 200

# Configurações de checkpoint (reduz escritas)
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100

# Configurações de logging (reduz I/O)
log_statement = 'none'
log_min_duration_statement = 1000
log_checkpoints = off
log_connections = off
log_disconnections = off

# Configurações de autovacuum
autovacuum = on
autovacuum_max_workers = 3
autovacuum_naptime = 1min

# Configurações de conexão
max_connections = 100
EOF

# Adicionar configurações ao arquivo principal
sudo tee -a "$POSTGRES_CONF" < /tmp/postgres_ssd_config > /dev/null

# Limpar arquivo temporário
rm -f /tmp/postgres_ssd_config

# Reiniciar PostgreSQL para aplicar configurações
log "Reiniciando PostgreSQL para aplicar configurações..."
sudo systemctl restart postgresql

# Verificar se reiniciou corretamente
if sudo systemctl is-active --quiet postgresql; then
    log "PostgreSQL reiniciado com sucesso!"
else
    error "Falha ao reiniciar PostgreSQL. Verifique os logs: sudo journalctl -u postgresql"
fi

# Testar conexão
log "Testando conexão..."
if sudo -u postgres psql -c "SELECT version();" > /dev/null 2>&1; then
    log "Conexão testada com sucesso!"
else
    warn "Problema na conexão. Verifique configurações."
fi

# Mostrar status
log "Status do PostgreSQL:"
sudo systemctl status postgresql --no-pager -l | head -10

echo ""
echo "=================================================="
echo -e "${GREEN}✅ PostgreSQL configurado com sucesso!${NC}"
echo ""
echo "Configurações aplicadas:"
echo "• Otimizações para SSD"
echo "• Configurações de memória ajustadas"
echo "• Logging otimizado"
echo "• Autovacuum configurado"
echo ""
echo "Arquivos:"
echo "• Configuração: $POSTGRES_CONF"
echo "• Backup: $POSTGRES_CONF.backup"
echo ""
echo "Comandos úteis:"
echo "• Status: sudo systemctl status postgresql"
echo "• Logs: sudo journalctl -u postgresql -f"
echo "• Conectar: sudo -u postgres psql"
echo "• Restaurar backup: sudo cp $POSTGRES_CONF.backup $POSTGRES_CONF"
echo "=================================================="

