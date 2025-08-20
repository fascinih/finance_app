#!/bin/bash

# PostgreSQL Setup Script for Finance App
# Otimizado para SSD externo via USB-C

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[POSTGRES]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[POSTGRES]${NC} $1"
}

error() {
    echo -e "${RED}[POSTGRES]${NC} $1"
    exit 1
}

log "Iniciando configuração do PostgreSQL..."

# Verificar se PostgreSQL está instalado
if ! command -v psql &> /dev/null; then
    error "PostgreSQL não está instalado. Execute setup_ubuntu.sh primeiro."
fi

# Iniciar serviço PostgreSQL
log "Iniciando serviço PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Aguardar serviço inicializar
sleep 3

# Configurar usuário e banco de dados
log "Configurando usuário e banco de dados..."

# Criar usuário finance_user
sudo -u postgres psql -c "DROP USER IF EXISTS finance_user;" || true
sudo -u postgres psql -c "CREATE USER finance_user WITH PASSWORD 'finance_password';"

# Criar banco de dados
sudo -u postgres psql -c "DROP DATABASE IF EXISTS finance_app;" || true
sudo -u postgres psql -c "CREATE DATABASE finance_app OWNER finance_user;"

# Conceder privilégios
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE finance_app TO finance_user;"
sudo -u postgres psql -c "ALTER USER finance_user CREATEDB;"

log "Usuário e banco criados com sucesso!"

# Configurar PostgreSQL para performance em SSD
log "Aplicando otimizações para SSD externo..."

# Backup da configuração original
sudo cp /etc/postgresql/*/main/postgresql.conf /etc/postgresql/*/main/postgresql.conf.backup

# Aplicar configurações otimizadas
POSTGRES_VERSION=$(sudo -u postgres psql -t -c "SELECT version();" | grep -oP '\d+\.\d+' | head -1)
POSTGRES_CONF="/etc/postgresql/$POSTGRES_VERSION/main/postgresql.conf"

log "Configurando PostgreSQL $POSTGRES_VERSION..."

# Configurações de memória (para 16GB RAM)
sudo tee -a $POSTGRES_CONF > /dev/null << 'EOF'

# Finance App Optimizations for SSD External Drive
# Memory Settings (16GB RAM)
shared_buffers = 4GB
effective_cache_size = 12GB
work_mem = 64MB
maintenance_work_mem = 1GB

# SSD Optimizations
random_page_cost = 1.1
seq_page_cost = 1.0
effective_io_concurrency = 200

# Checkpoint Settings
checkpoint_completion_target = 0.9
wal_buffers = 16MB
checkpoint_timeout = 10min
max_wal_size = 2GB
min_wal_size = 1GB

# Performance Settings
synchronous_commit = off
fsync = on
full_page_writes = on

# Connection Settings
max_connections = 100
shared_preload_libraries = 'pg_stat_statements'

# Logging
log_statement = 'mod'
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
EOF

# Configurar pg_hba.conf para permitir conexões locais
PG_HBA="/etc/postgresql/$POSTGRES_VERSION/main/pg_hba.conf"
sudo cp $PG_HBA $PG_HBA.backup

log "Configurando autenticação..."
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" $POSTGRES_CONF

# Adicionar regra para aplicação
sudo tee -a $PG_HBA > /dev/null << 'EOF'

# Finance App connections
local   finance_app     finance_user                     md5
host    finance_app     finance_user     127.0.0.1/32   md5
host    finance_app     finance_user     ::1/128        md5
EOF

# Reiniciar PostgreSQL para aplicar configurações
log "Reiniciando PostgreSQL..."
sudo systemctl restart postgresql

# Aguardar reinicialização
sleep 5

# Verificar se está rodando
if ! sudo systemctl is-active --quiet postgresql; then
    error "Falha ao reiniciar PostgreSQL"
fi

# Instalar extensões úteis
log "Instalando extensões PostgreSQL..."
sudo -u postgres psql -d finance_app -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"
sudo -u postgres psql -d finance_app -c "CREATE EXTENSION IF NOT EXISTS uuid-ossp;"
sudo -u postgres psql -d finance_app -c "CREATE EXTENSION IF NOT EXISTS btree_gin;"

# Criar script SQL de inicialização
log "Criando script de inicialização do banco..."
cat > init_db.sql << 'EOF'
-- Finance App Database Initialization
-- Criado automaticamente pelo setup

-- Configurar timezone
SET timezone = 'America/Sao_Paulo';

-- Criar schema principal
CREATE SCHEMA IF NOT EXISTS finance;

-- Configurar search_path
ALTER DATABASE finance_app SET search_path TO finance, public;

-- Criar tabelas principais (serão criadas pelo SQLAlchemy)
-- Este arquivo serve como referência e configuração inicial

-- Configurações de performance
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET track_activity_query_size = 2048;
ALTER SYSTEM SET track_io_timing = on;

-- Recarregar configuração
SELECT pg_reload_conf();

-- Criar usuário de backup
CREATE USER backup_user WITH PASSWORD 'backup_password';
GRANT CONNECT ON DATABASE finance_app TO backup_user;
GRANT USAGE ON SCHEMA finance TO backup_user;
GRANT SELECT ON ALL TABLES IN SCHEMA finance TO backup_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA finance GRANT SELECT ON TABLES TO backup_user;

-- Log de inicialização
INSERT INTO pg_stat_statements_reset();
EOF

# Executar script de inicialização
log "Executando inicialização do banco..."
sudo -u postgres psql -d finance_app -f init_db.sql

# Testar conexão
log "Testando conexão com o banco..."
PGPASSWORD=finance_password psql -h localhost -U finance_user -d finance_app -c "SELECT version();" > /dev/null

if [ $? -eq 0 ]; then
    log "✅ Conexão com banco testada com sucesso!"
else
    error "❌ Falha na conexão com o banco"
fi

# Criar script de backup
log "Criando script de backup..."
cat > ~/.local/bin/backup_finance_db.sh << 'EOF'
#!/bin/bash

# Finance App Database Backup Script

BACKUP_DIR="$HOME/finance_backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/finance_app_$DATE.sql"

# Criar diretório de backup
mkdir -p $BACKUP_DIR

# Fazer backup
echo "Iniciando backup do banco finance_app..."
PGPASSWORD=finance_password pg_dump -h localhost -U finance_user -d finance_app > $BACKUP_FILE

# Comprimir backup
gzip $BACKUP_FILE

echo "Backup concluído: ${BACKUP_FILE}.gz"

# Manter apenas os últimos 7 backups
find $BACKUP_DIR -name "finance_app_*.sql.gz" -mtime +7 -delete

echo "Backups antigos removidos (>7 dias)"
EOF

chmod +x ~/.local/bin/backup_finance_db.sh

# Criar script de monitoramento
cat > ~/.local/bin/postgres_monitor.sh << 'EOF'
#!/bin/bash

echo "=== PostgreSQL Status Monitor ==="
echo "Data: $(date)"
echo ""

echo "Serviço Status:"
sudo systemctl status postgresql --no-pager -l

echo ""
echo "Conexões Ativas:"
sudo -u postgres psql -d finance_app -c "
SELECT 
    datname,
    usename,
    client_addr,
    state,
    query_start,
    LEFT(query, 50) as query_preview
FROM pg_stat_activity 
WHERE datname = 'finance_app';"

echo ""
echo "Estatísticas de Performance:"
sudo -u postgres psql -d finance_app -c "
SELECT 
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    idx_tup_fetch
FROM pg_stat_user_tables 
ORDER BY seq_scan DESC 
LIMIT 10;"

echo ""
echo "Tamanho do Banco:"
sudo -u postgres psql -d finance_app -c "
SELECT 
    pg_size_pretty(pg_database_size('finance_app')) as database_size;"
EOF

chmod +x ~/.local/bin/postgres_monitor.sh

log "Scripts de monitoramento criados!"

echo ""
echo "=================================================="
echo -e "${GREEN}✅ PostgreSQL configurado com sucesso!${NC}"
echo ""
echo "Informações de conexão:"
echo "• Host: localhost"
echo "• Porta: 5432"
echo "• Banco: finance_app"
echo "• Usuário: finance_user"
echo "• Senha: finance_password"
echo ""
echo "Comandos úteis:"
echo "• Status: sudo systemctl status postgresql"
echo "• Monitor: postgres_monitor.sh"
echo "• Backup: backup_finance_db.sh"
echo "• Conectar: psql -h localhost -U finance_user -d finance_app"
echo ""
echo "Configurações aplicadas:"
echo "• Otimizado para SSD externo"
echo "• 4GB shared_buffers"
echo "• 12GB effective_cache_size"
echo "• Extensões: pg_stat_statements, uuid-ossp, btree_gin"
echo "=================================================="

