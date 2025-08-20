#!/bin/bash

# Script para corrigir o monitoramento do Ollama
echo "🔧 Corrigindo script de monitoramento do Ollama..."

# Criar diretório se não existir
mkdir -p ~/.local/bin

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
    echo "GPU NVIDIA não detectada"
fi

echo ""
echo "Uso de Memória:"
free -h

echo ""
echo "Processos Ollama:"
ps aux | grep ollama | grep -v grep
EOF

# Tornar executável
chmod +x ~/.local/bin/ollama-monitor.sh

# Adicionar ao PATH se necessário
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    echo "✅ Adicionado ~/.local/bin ao PATH"
fi

echo "✅ Script de monitoramento criado com sucesso!"
echo ""
echo "Para usar:"
echo "  source ~/.bashrc  # Recarregar PATH"
echo "  ollama-monitor.sh # Executar monitoramento"
echo ""
echo "Ou execute diretamente:"
echo "  ~/.local/bin/ollama-monitor.sh"

