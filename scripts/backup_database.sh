#!/bin/bash

# Finance App - Script de Backup do Banco de Dados
# Cria backup completo do PostgreSQL com rotação automática

set -e

# Configurações
BACKUP_DIR="/var/backups/finance_app"
DB_NAME="finance_app"
DB_USER="finance_user"
RETENTION_DAYS=30
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="finance_app_backup_${TIMESTAMP}.sql"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Finance App - Backup do Banco de Dados ===${NC}"
echo "Iniciado em: $(date)"

# Verificar se o diretório de backup existe
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${YELLOW}Criando diretório de backup: $BACKUP_DIR${NC}"
    sudo mkdir -p "$BACKUP_DIR"
    sudo chown $USER:$USER "$BACKUP_DIR"
fi

# Verificar se o PostgreSQL está rodando
if ! systemctl is-active --quiet postgresql; then
    echo -e "${RED}Erro: PostgreSQL não está rodando${NC}"
    exit 1
fi

# Verificar se o banco existe
if ! psql -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; then
    echo -e "${RED}Erro: Não foi possível conectar ao banco $DB_NAME${NC}"
    exit 1
fi

echo -e "${YELLOW}Criando backup do banco $DB_NAME...${NC}"

# Criar backup
if pg_dump -U "$DB_USER" -d "$DB_NAME" -f "$BACKUP_DIR/$BACKUP_FILE" --verbose; then
    echo -e "${GREEN}Backup criado com sucesso: $BACKUP_DIR/$BACKUP_FILE${NC}"
    
    # Comprimir backup
    echo -e "${YELLOW}Comprimindo backup...${NC}"
    gzip "$BACKUP_DIR/$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Backup comprimido: $BACKUP_DIR/$BACKUP_FILE.gz${NC}"
        
        # Mostrar tamanho do arquivo
        BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE.gz" | cut -f1)
        echo -e "${BLUE}Tamanho do backup: $BACKUP_SIZE${NC}"
    else
        echo -e "${RED}Erro ao comprimir backup${NC}"
    fi
else
    echo -e "${RED}Erro ao criar backup${NC}"
    exit 1
fi

# Limpeza de backups antigos
echo -e "${YELLOW}Removendo backups antigos (mais de $RETENTION_DAYS dias)...${NC}"

DELETED_COUNT=$(find "$BACKUP_DIR" -name "finance_app_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)

if [ "$DELETED_COUNT" -gt 0 ]; then
    echo -e "${GREEN}Removidos $DELETED_COUNT backups antigos${NC}"
else
    echo -e "${BLUE}Nenhum backup antigo para remover${NC}"
fi

# Listar backups existentes
echo -e "${BLUE}Backups disponíveis:${NC}"
ls -lh "$BACKUP_DIR"/finance_app_backup_*.sql.gz 2>/dev/null | tail -10 || echo "Nenhum backup encontrado"

# Verificar integridade do backup (teste de descompressão)
echo -e "${YELLOW}Verificando integridade do backup...${NC}"
if gzip -t "$BACKUP_DIR/$BACKUP_FILE.gz"; then
    echo -e "${GREEN}Backup íntegro e válido${NC}"
else
    echo -e "${RED}Erro: Backup corrompido!${NC}"
    exit 1
fi

echo -e "${GREEN}=== Backup concluído com sucesso ===${NC}"
echo "Finalizado em: $(date)"

# Log do backup
LOG_FILE="/var/log/finance_app_backup.log"
echo "$(date): Backup criado - $BACKUP_FILE.gz ($BACKUP_SIZE)" >> "$LOG_FILE"

