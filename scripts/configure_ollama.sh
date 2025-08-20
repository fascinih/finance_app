#!/bin/bash

# Ollama Installation and Configuration Script
# Otimizado para GTX 1660 TI com 6GB VRAM

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[OLLAMA]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[OLLAMA]${NC} $1"
}

error() {
    echo -e "${RED}[OLLAMA]${NC} $1"
    exit 1
}

log "Iniciando instalação e configuração do Ollama..."

# Verificar se já está instalado
if command -v ollama &> /dev/null; then
    warn "Ollama já está instalado. Atualizando..."
fi

# Instalar Ollama
log "Baixando e instalando Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

# Verificar instalação
if ! command -v ollama &> /dev/null; then
    error "Falha na instalação do Ollama"
fi

log "Ollama instalado com sucesso: $(ollama --version)"

# Configurar serviço systemd
log "Configurando serviço systemd..."
sudo tee /etc/systemd/system/ollama.service > /dev/null << 'EOF'
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
ExecStart=/usr/local/bin/ollama serve
User=ollama
Group=ollama
Restart=always
RestartSec=3
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_GPU_OVERHEAD=0"
Environment="OLLAMA_NUM_PARALLEL=4"
Environment="OLLAMA_FLASH_ATTENTION=true"

[Install]
WantedBy=default.target
EOF

# Criar usuário ollama se não existir
if ! id "ollama" &>/dev/null; then
    log "Criando usuário ollama..."
    sudo useradd -r -s /bin/false -m -d /usr/share/ollama ollama
fi

# Configurar permissões
sudo mkdir -p /usr/share/ollama
sudo chown ollama:ollama /usr/share/ollama

# Habilitar e iniciar serviço
log "Habilitando serviço Ollama..."
sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl start ollama

# Aguardar serviço inicializar
log "Aguardando Ollama inicializar..."
sleep 5

# Verificar se o serviço está rodando
if ! sudo systemctl is-active --quiet ollama; then
    error "Falha ao iniciar serviço Ollama"
fi

log "Serviço Ollama iniciado com sucesso!"

# Baixar modelos recomendados para análise financeira
log "Baixando modelos recomendados..."

# DeepSeek R1 7B - Melhor para análise financeira
log "Baixando DeepSeek R1 7B (4.7GB VRAM)..."
ollama pull deepseek-r1:7b || warn "Falha ao baixar deepseek-r1:7b"

# Llama 3.2 3B - Modelo mais leve
log "Baixando Llama 3.2 3B (2.0GB VRAM)..."
ollama pull llama3.2:3b || warn "Falha ao baixar llama3.2:3b"

# Mistral 7B - Alternativa robusta
log "Baixando Mistral 7B (4.1GB VRAM)..."
ollama pull mistral:7b || warn "Falha ao baixar mistral:7b"

# Criar arquivo de configuração personalizado
log "Criando configuração personalizada..."
mkdir -p ~/.config/ollama

cat > ~/.config/ollama/config.json << 'EOF'
{
  "gpu_memory_utilization": 0.8,
  "max_concurrent_requests": 4,
  "default_model": "deepseek-r1:7b",
  "models": {
    "deepseek-r1:7b": {
      "context_length": 4096,
      "temperature": 0.1,
      "top_p": 0.9,
      "use_case": "financial_analysis"
    },
    "llama3.2:3b": {
      "context_length": 2048,
      "temperature": 0.2,
      "top_p": 0.8,
      "use_case": "categorization"
    },
    "mistral:7b": {
      "context_length": 4096,
      "temperature": 0.15,
      "top_p": 0.85,
      "use_case": "general_analysis"
    }
  }
}
EOF

# Testar modelos
log "Testando modelos instalados..."
echo "Modelos disponíveis:"
ollama list

# Teste básico com o modelo principal
log "Testando DeepSeek R1 7B..."
echo "Teste: Categorize esta transação: PIX TRANSFERENCIA SUPERMERCADO ABC 150.00" | \
ollama run deepseek-r1:7b "Categorize esta transação financeira em uma palavra: " || \
warn "Teste do modelo falhou - verifique GPU e VRAM"

# Criar script de monitoramento
cat > ~/.local/bin/ollama-monitor.sh << 'EOF'
#!/bin/bash

echo "=== Ollama Status Monitor ==="
echo "Data: $(date)"
echo ""

echo "Serviço Status:"
sudo systemctl status ollama --no-pager -l

echo ""
echo "Modelos Instalados:"
ollama list

echo ""
echo "Uso de GPU (se disponível):"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits
else
    echo "nvidia-smi não disponível"
fi

echo ""
echo "Uso de Memória:"
free -h

echo ""
echo "Processos Ollama:"
ps aux | grep ollama | grep -v grep
EOF

chmod +x ~/.local/bin/ollama-monitor.sh

# Adicionar ao PATH se necessário
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
fi

log "Configuração do Ollama concluída!"
log "Modelos instalados:"
ollama list

echo ""
echo "=================================================="
echo -e "${GREEN}✅ Ollama configurado com sucesso!${NC}"
echo ""
echo "Comandos úteis:"
echo "• Status do serviço: sudo systemctl status ollama"
echo "• Listar modelos: ollama list"
echo "• Testar modelo: ollama run deepseek-r1:7b"
echo "• Monitor: ollama-monitor.sh"
echo "• Logs: sudo journalctl -u ollama -f"
echo ""
echo "API disponível em: http://localhost:11434"
echo "=================================================="

