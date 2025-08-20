#!/bin/bash

# Finance App - Script de Restore do Banco de Dados
# Restaura backup do PostgreSQL com verificações de segurança

set -e

# Configurações
BACKUP_DIR="/var/backups/finance_app"
DB_NAME="finance_app"
DB_USER="finance_user"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Finance App - Restore do Banco de Dados ===${NC}"

# Verificar parâmetros
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}Uso: $0 <arquivo_backup>${NC}"
    echo -e "${YELLOW}Ou: $0 --list (para listar backups disponíveis)${NC}"
    echo -e "${YELLOW}Ou: $0 --latest (para usar o backup mais recente)${NC}"
    exit 1
fi

# Listar backups disponíveis
if [ "$1" = "--list" ]; then
    echo -e "${BLUE}Backups disponíveis em $BACKUP_DIR:${NC}"
    ls -lht "$BACKUP_DIR"/finance_app_backup_*.sql.gz 2>/dev/null || echo "Nenhum backup encontrado"
    exit 0
fi

# Usar backup mais recente
if [ "$1" = "--latest" ]; then
    BACKUP_FILE=$(ls -t "$BACKUP_DIR"/finance_app_backup_*.sql.gz 2>/dev/null | head -1)
    if [ -z "$BACKUP_FILE" ]; then
        echo -e "${RED}Erro: Nenhum backup encontrado${NC}"
        exit 1
    fi
    echo -e "${BLUE}Usando backup mais recente: $(basename $BACKUP_FILE)${NC}"
else
    BACKUP_FILE="$1"
    
    # Verificar se o arquivo existe
    if [ ! -f "$BACKUP_FILE" ]; then
        # Tentar no diretório de backup
        if [ -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
            BACKUP_FILE="$BACKUP_DIR/$BACKUP_FILE"
        else
            echo -e "${RED}Erro: Arquivo de backup não encontrado: $BACKUP_FILE${NC}"
            exit 1
        fi
    fi
fi

echo -e "${YELLOW}Arquivo de backup: $BACKUP_FILE${NC}"

# Verificar se o arquivo é válido
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo -e "${YELLOW}Verificando integridade do backup comprimido...${NC}"
    if ! gzip -t "$BACKUP_FILE"; then
        echo -e "${RED}Erro: Arquivo de backup corrompido${NC}"
        exit 1
    fi
    echo -e "${GREEN}Backup íntegro${NC}"
else
    echo -e "${YELLOW}Backup não comprimido detectado${NC}"
fi

# Verificar se o PostgreSQL está rodando
if ! systemctl is-active --quiet postgresql; then
    echo -e "${RED}Erro: PostgreSQL não está rodando${NC}"
    exit 1
fi

# Confirmação de segurança
echo -e "${RED}ATENÇÃO: Esta operação irá SUBSTITUIR completamente o banco de dados atual!${NC}"
echo -e "${YELLOW}Banco de dados: $DB_NAME${NC}"
echo -e "${YELLOW}Backup: $(basename $BACKUP_FILE)${NC}"
echo ""
read -p "Tem certeza que deseja continuar? (digite 'CONFIRMO' para prosseguir): " CONFIRMATION

if [ "$CONFIRMATION" != "CONFIRMO" ]; then
    echo -e "${YELLOW}Operação cancelada pelo usuário${NC}"
    exit 0
fi

# Criar backup de segurança antes do restore
echo -e "${YELLOW}Criando backup de segurança antes do restore...${NC}"
SAFETY_BACKUP="/tmp/finance_app_safety_backup_$(date +%Y%m%d_%H%M%S).sql"

if pg_dump -U "$DB_USER" -d "$DB_NAME" -f "$SAFETY_BACKUP"; then
    echo -e "${GREEN}Backup de segurança criado: $SAFETY_BACKUP${NC}"
else
    echo -e "${RED}Erro ao criar backup de segurança${NC}"
    exit 1
fi

# Parar serviços que usam o banco
echo -e "${YELLOW}Parando serviços...${NC}"

# Parar FastAPI se estiver rodando
if pgrep -f "uvicorn.*finance_app" > /dev/null; then
    echo "Parando FastAPI..."
    pkill -f "uvicorn.*finance_app" || true
    sleep 2
fi

# Parar Streamlit se estiver rodando
if pgrep -f "streamlit.*finance_app" > /dev/null; then
    echo "Parando Streamlit..."
    pkill -f "streamlit.*finance_app" || true
    sleep 2
fi

# Desconectar todas as sessões do banco
echo -e "${YELLOW}Desconectando sessões ativas do banco...${NC}"
psql -U "$DB_USER" -d postgres -c "
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();" || true

# Dropar e recriar o banco
echo -e "${YELLOW}Recriando banco de dados...${NC}"

psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
psql -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

echo -e "${GREEN}Banco de dados recriado${NC}"

# Restaurar backup
echo -e "${YELLOW}Restaurando backup...${NC}"

if [[ "$BACKUP_FILE" == *.gz ]]; then
    # Backup comprimido
    if gunzip -c "$BACKUP_FILE" | psql -U "$DB_USER" -d "$DB_NAME"; then
        echo -e "${GREEN}Restore concluído com sucesso${NC}"
    else
        echo -e "${RED}Erro durante o restore${NC}"
        
        # Tentar restaurar backup de segurança
        echo -e "${YELLOW}Tentando restaurar backup de segurança...${NC}"
        psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
        psql -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
        
        if psql -U "$DB_USER" -d "$DB_NAME" -f "$SAFETY_BACKUP"; then
            echo -e "${GREEN}Backup de segurança restaurado${NC}"
        else
            echo -e "${RED}Erro crítico: Não foi possível restaurar backup de segurança${NC}"
        fi
        
        exit 1
    fi
else
    # Backup não comprimido
    if psql -U "$DB_USER" -d "$DB_NAME" -f "$BACKUP_FILE"; then
        echo -e "${GREEN}Restore concluído com sucesso${NC}"
    else
        echo -e "${RED}Erro durante o restore${NC}"
        exit 1
    fi
fi

# Verificar integridade do banco restaurado
echo -e "${YELLOW}Verificando integridade do banco restaurado...${NC}"

# Contar tabelas
TABLE_COUNT=$(psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)

if [ "$TABLE_COUNT" -gt 0 ]; then
    echo -e "${GREEN}Banco restaurado com $TABLE_COUNT tabelas${NC}"
else
    echo -e "${RED}Erro: Nenhuma tabela encontrada no banco restaurado${NC}"
    exit 1
fi

# Verificar algumas tabelas principais
TABLES=("transactions" "categories" "import_batches")
for table in "${TABLES[@]}"; do
    if psql -U "$DB_USER" -d "$DB_NAME" -c "\d $table" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Tabela $table encontrada${NC}"
    else
        echo -e "${YELLOW}⚠ Tabela $table não encontrada (pode ser normal)${NC}"
    fi
done

# Limpar backup de segurança
echo -e "${YELLOW}Limpando backup de segurança temporário...${NC}"
rm -f "$SAFETY_BACKUP"

echo -e "${GREEN}=== Restore concluído com sucesso ===${NC}"
echo -e "${BLUE}Você pode agora reiniciar os serviços da aplicação${NC}"

# Log do restore
LOG_FILE="/var/log/finance_app_restore.log"
echo "$(date): Restore realizado - $(basename $BACKUP_FILE)" >> "$LOG_FILE"

