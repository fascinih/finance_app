#!/bin/bash

# NVIDIA Drivers Installation Script for Ubuntu
# Otimizado para GTX 1660 TI com 6GB VRAM

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[NVIDIA]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[NVIDIA]${NC} $1"
}

error() {
    echo -e "${RED}[NVIDIA]${NC} $1"
    exit 1
}

log "Iniciando instalação dos drivers NVIDIA..."

# Verificar se há GPU NVIDIA
if ! lspci | grep -i nvidia > /dev/null; then
    error "GPU NVIDIA não detectada. Abortando instalação."
fi

# Mostrar informações da GPU
log "GPU detectada:"
lspci | grep -i nvidia

# Remover drivers antigos se existirem
log "Removendo drivers antigos..."
sudo apt purge -y nvidia* libnvidia* || true
sudo apt autoremove -y || true

# Adicionar repositório oficial NVIDIA
log "Adicionando repositório NVIDIA..."
sudo add-apt-repository ppa:graphics-drivers/ppa -y
sudo apt update

# Detectar driver recomendado
log "Detectando driver recomendado..."
RECOMMENDED_DRIVER=$(ubuntu-drivers devices | grep recommended | awk '{print $3}' | head -1)

if [[ -z "$RECOMMENDED_DRIVER" ]]; then
    warn "Driver recomendado não detectado. Usando nvidia-driver-535..."
    RECOMMENDED_DRIVER="nvidia-driver-535"
fi

log "Driver recomendado: $RECOMMENDED_DRIVER"

# Instalar driver NVIDIA
log "Instalando driver NVIDIA: $RECOMMENDED_DRIVER"
sudo apt install -y $RECOMMENDED_DRIVER

# Instalar CUDA Toolkit (versão compatível)
log "Instalando CUDA Toolkit..."
sudo apt install -y nvidia-cuda-toolkit

# Instalar utilitários adicionais
log "Instalando utilitários NVIDIA..."
sudo apt install -y \
    nvidia-settings \
    nvidia-prime \
    libnvidia-compute-535 \
    libnvidia-decode-535 \
    libnvidia-encode-535

# Configurar variáveis de ambiente CUDA
log "Configurando variáveis de ambiente CUDA..."
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc

# Configurar otimizações para Ollama
log "Configurando otimizações para Ollama..."
cat >> ~/.bashrc << 'EOF'

# Ollama GPU Optimizations
export OLLAMA_GPU_OVERHEAD=0
export OLLAMA_NUM_PARALLEL=4
export OLLAMA_FLASH_ATTENTION=true
export CUDA_VISIBLE_DEVICES=0
EOF

# Criar arquivo de configuração X11 para NVIDIA
log "Configurando X11 para NVIDIA..."
sudo tee /etc/X11/xorg.conf.d/20-nvidia.conf > /dev/null << 'EOF'
Section "Device"
    Identifier "NVIDIA Card"
    Driver "nvidia"
    VendorName "NVIDIA Corporation"
    Option "NoLogo" "true"
    Option "UseEDID" "false"
    Option "ConnectedMonitor" "DFP"
EndSection
EOF

# Configurar módulos do kernel
log "Configurando módulos do kernel..."
echo 'nvidia' | sudo tee -a /etc/modules
echo 'nvidia-drm' | sudo tee -a /etc/modules

# Atualizar initramfs
log "Atualizando initramfs..."
sudo update-initramfs -u

log "Instalação dos drivers NVIDIA concluída!"
warn "REINICIALIZAÇÃO NECESSÁRIA para ativar os drivers."
log "Após reiniciar, execute 'nvidia-smi' para verificar a instalação."

# Criar script de verificação
cat > /tmp/verify_nvidia.sh << 'EOF'
#!/bin/bash
echo "Verificando instalação NVIDIA..."
echo "================================"

if command -v nvidia-smi &> /dev/null; then
    echo "✅ nvidia-smi encontrado"
    nvidia-smi
else
    echo "❌ nvidia-smi não encontrado"
fi

if command -v nvcc &> /dev/null; then
    echo "✅ CUDA Compiler encontrado"
    nvcc --version
else
    echo "❌ CUDA Compiler não encontrado"
fi

echo ""
echo "Variáveis de ambiente CUDA:"
echo "PATH: $PATH"
echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
EOF

chmod +x /tmp/verify_nvidia.sh

log "Script de verificação criado em /tmp/verify_nvidia.sh"
log "Execute após reiniciar: bash /tmp/verify_nvidia.sh"

