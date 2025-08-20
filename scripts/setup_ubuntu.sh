#!/bin/bash

# Finance App - Ubuntu Setup Script
# Otimizado para Ubuntu 22.04/24.04 LTS em SSD externo via USB-C

set -e

echo "🚀 Configurando ambiente Ubuntu para aplicação financeira..."
echo "=================================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para log
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Verificar se está rodando no Ubuntu
if [[ ! -f /etc/lsb-release ]] || ! grep -q "Ubuntu" /etc/lsb-release; then
    error "Este script é otimizado para Ubuntu. Sistema atual não suportado."
fi

log "Detectado: $(lsb_release -d | cut -f2)"

# Atualizar sistema
log "Atualizando sistema..."
sudo apt update && sudo apt upgrade -y

# Instalar dependências básicas
log "Instalando dependências básicas..."
sudo apt install -y \
    curl \
    wget \
    git \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    libpq-dev \
    postgresql \
    postgresql-contrib \
    redis-server \
    docker.io \
    docker-compose \
    htop \
    tree \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Configurar Docker
log "Configurando Docker..."
sudo usermod -aG docker $USER
sudo systemctl enable docker
sudo systemctl start docker

# Instalar drivers NVIDIA se disponível
log "Verificando GPU NVIDIA..."
if lspci | grep -i nvidia > /dev/null; then
    log "GPU NVIDIA detectada. Instalando drivers..."
    ./scripts/install_nvidia.sh
else
    warn "GPU NVIDIA não detectada. Continuando sem drivers NVIDIA..."
fi

# Instalar e configurar Ollama
log "Instalando Ollama..."
./scripts/configure_ollama.sh

# Configurar PostgreSQL
log "Configurando PostgreSQL..."
./scripts/setup_database.sh

# Otimizações para SSD externo
log "Aplicando otimizações para SSD externo..."
./scripts/optimize_ssd.sh

# Criar ambiente virtual Python
log "Criando ambiente virtual Python..."
python3 -m venv venv
source venv/bin/activate

# Instalar dependências Python
log "Instalando dependências Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Configurar variáveis de ambiente
log "Configurando variáveis de ambiente..."
if [[ ! -f .env ]]; then
    cp .env.example .env
    log "Arquivo .env criado. Configure as variáveis necessárias."
fi

# Verificar instalação
log "Verificando instalação..."
python3 --version
docker --version
docker-compose --version

if command -v ollama &> /dev/null; then
    ollama --version
else
    warn "Ollama não encontrado no PATH"
fi

# Configurar serviços para inicialização automática
log "Configurando serviços..."
sudo systemctl enable postgresql
sudo systemctl enable redis-server
sudo systemctl enable docker

echo ""
echo "=================================================="
echo -e "${GREEN}✅ Setup completo!${NC}"
echo ""
echo "Próximos passos:"
echo "1. Configure o arquivo .env com suas credenciais"
echo "2. Execute: source venv/bin/activate"
echo "3. Execute: docker-compose up -d"
echo "4. Acesse: http://localhost:8501 (Frontend)"
echo "5. API: http://localhost:8000 (Backend)"
echo ""
echo "Para monitorar recursos: htop"
echo "Para monitorar GPU: nvidia-smi (se disponível)"
echo "=================================================="

