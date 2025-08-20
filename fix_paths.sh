#!/bin/bash

# Script para corrigir caminhos hardcoded nos scripts
echo "🔧 Corrigindo caminhos nos scripts da Finance App..."

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[FIX-PATHS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[FIX-PATHS]${NC} $1"
}

# Detectar diretório atual
CURRENT_DIR=$(pwd)
log "Diretório atual: $CURRENT_DIR"

# Verificar se estamos no diretório correto
if [ ! -f "streamlit_app.py" ] || [ ! -d "scripts" ]; then
    echo "❌ Execute este script no diretório raiz da Finance App"
    echo "   (onde estão os arquivos streamlit_app.py e pasta scripts/)"
    exit 1
fi

# Lista de scripts para corrigir
SCRIPTS_TO_FIX=(
    "scripts/start_all.sh"
    "scripts/stop_all.sh"
    "scripts/setup_database.sh"
    "scripts/backup_database.sh"
    "scripts/restore_database.sh"
    "scripts/monitor_system.sh"
)

# Corrigir cada script
for script in "${SCRIPTS_TO_FIX[@]}"; do
    if [ -f "$script" ]; then
        log "Corrigindo: $script"
        
        # Fazer backup
        cp "$script" "$script.backup"
        
        # Substituir caminho hardcoded pelo atual
        sed -i "s|/home/ubuntu/finance_app|$CURRENT_DIR|g" "$script"
        
        # Verificar se mudou
        if ! cmp -s "$script" "$script.backup"; then
            log "✅ $script corrigido"
        else
            log "ℹ️  $script não precisava de correção"
        fi
    else
        warn "❌ $script não encontrado"
    fi
done

# Corrigir também arquivos de configuração se existirem
CONFIG_FILES=(
    ".env"
    ".env.example"
    "docker-compose.yml"
)

for config in "${CONFIG_FILES[@]}"; do
    if [ -f "$config" ]; then
        log "Verificando: $config"
        
        # Fazer backup
        cp "$config" "$config.backup"
        
        # Substituir caminhos
        sed -i "s|/home/ubuntu/finance_app|$CURRENT_DIR|g" "$config"
        
        if ! cmp -s "$config" "$config.backup"; then
            log "✅ $config corrigido"
        else
            log "ℹ️  $config não precisava de correção"
        fi
    fi
done

# Criar arquivo .env se não existir
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    log "Criando arquivo .env..."
    cp .env.example .env
    
    # Ajustar caminhos no .env
    sed -i "s|/home/ubuntu/finance_app|$CURRENT_DIR|g" .env
    log "✅ Arquivo .env criado"
fi

# Verificar se Python virtual environment existe
if [ ! -d "venv" ]; then
    log "Criando ambiente virtual Python..."
    python3 -m venv venv
    log "✅ Ambiente virtual criado"
fi

# Ativar venv e instalar dependências se necessário
if [ -f "requirements.txt" ]; then
    log "Verificando dependências Python..."
    source venv/bin/activate
    
    # Verificar se precisa instalar
    if ! pip list | grep -q "streamlit"; then
        log "Instalando dependências..."
        pip install -r requirements.txt
        log "✅ Dependências instaladas"
    else
        log "ℹ️  Dependências já instaladas"
    fi
    
    deactivate
fi

# Tornar scripts executáveis
log "Ajustando permissões..."
chmod +x scripts/*.sh
chmod +x *.sh 2>/dev/null || true

echo ""
echo "=================================================="
echo -e "${GREEN}✅ Caminhos corrigidos com sucesso!${NC}"
echo ""
echo "Configurações atualizadas:"
echo "• Diretório base: $CURRENT_DIR"
echo "• Scripts corrigidos: ${#SCRIPTS_TO_FIX[@]}"
echo "• Ambiente virtual: $([ -d "venv" ] && echo "✅ Criado" || echo "❌ Não encontrado")"
echo "• Dependências: $([ -f "venv/bin/activate" ] && echo "✅ Instaladas" || echo "❌ Não instaladas")"
echo ""
echo "Agora você pode executar:"
echo "• ./scripts/start_all.sh     # Iniciar aplicação"
echo "• ./scripts/setup_database.sh # Configurar banco"
echo "• ./scripts/monitor_system.sh # Monitorar sistema"
echo "=================================================="

