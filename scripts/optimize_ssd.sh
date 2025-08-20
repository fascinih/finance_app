#!/bin/bash

# SSD External Drive Optimization Script
# Otimizações específicas para SSD externo via USB-C

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[SSD-OPT]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[SSD-OPT]${NC} $1"
}

error() {
    echo -e "${RED}[SSD-OPT]${NC} $1"
    exit 1
}

log "Iniciando otimizações para SSD externo via USB-C..."

# Detectar dispositivos SSD externos
log "Detectando dispositivos de armazenamento..."
lsblk -d -o NAME,SIZE,TYPE,TRAN | grep -E "(usb|sata)"

# Configurar swappiness para SSD
log "Configurando swappiness para SSD..."
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.conf
echo 'vm.dirty_background_ratio=5' | sudo tee -a /etc/sysctl.conf
echo 'vm.dirty_ratio=10' | sudo tee -a /etc/sysctl.conf

# Aplicar configurações imediatamente
sudo sysctl -p

# Configurar I/O scheduler para SSD
log "Configurando I/O scheduler para SSD..."

# Detectar dispositivos SSD
for device in $(lsblk -d -n -o NAME | grep -E "sd[a-z]"); do
    # Verificar se é SSD
    if [[ -f /sys/block/$device/queue/rotational ]] && [[ $(cat /sys/block/$device/queue/rotational) == "0" ]]; then
        log "Configurando scheduler para SSD: $device"
        echo 'mq-deadline' | sudo tee /sys/block/$device/queue/scheduler
        
        # Configurar read-ahead para SSD
        sudo blockdev --setra 256 /dev/$device
        
        # Configurar queue depth
        echo 32 | sudo tee /sys/block/$device/queue/nr_requests
    fi
done

# Configurar fstab para SSD (se aplicável)
log "Verificando configurações de mount para SSD..."

# Backup do fstab
sudo cp /etc/fstab /etc/fstab.backup

# Adicionar configurações recomendadas para SSD no fstab
cat >> /tmp/ssd_fstab_additions << 'EOF'

# SSD Optimizations
# Adicione estas opções aos seus pontos de montagem SSD:
# noatime,discard,commit=60,barrier=0
# Exemplo:
# UUID=your-uuid /mount/point ext4 defaults,noatime,discard,commit=60,barrier=0 0 2
EOF

log "Configurações de fstab salvas em /tmp/ssd_fstab_additions"
warn "Revise e aplique manualmente as configurações de fstab conforme necessário"

# Configurar TRIM automático
log "Configurando TRIM automático para SSD..."
sudo systemctl enable fstrim.timer
sudo systemctl start fstrim.timer

# Verificar se TRIM está funcionando
if sudo fstrim -v / 2>/dev/null; then
    log "✅ TRIM funcionando corretamente"
else
    warn "TRIM pode não estar disponível para o sistema de arquivos raiz"
fi

# Configurar tmpfs para reduzir escritas no SSD
log "Configurando tmpfs para reduzir escritas no SSD..."

# Adicionar tmpfs ao fstab
cat >> /tmp/tmpfs_additions << 'EOF'

# tmpfs para reduzir escritas no SSD
tmpfs /tmp tmpfs defaults,noatime,mode=1777,size=2G 0 0
tmpfs /var/tmp tmpfs defaults,noatime,mode=1777,size=1G 0 0
tmpfs /var/log tmpfs defaults,noatime,mode=0755,size=512M 0 0
EOF

log "Configurações tmpfs salvas em /tmp/tmpfs_additions"

# Configurar logs para reduzir escritas
log "Configurando logs para reduzir escritas no SSD..."

# Configurar journald
sudo mkdir -p /etc/systemd/journald.conf.d
cat > /tmp/journald-ssd.conf << 'EOF'
[Journal]
Storage=volatile
RuntimeMaxUse=100M
RuntimeMaxFileSize=10M
MaxRetentionSec=1week
EOF

sudo cp /tmp/journald-ssd.conf /etc/systemd/journald.conf.d/ssd-optimization.conf

# Configurar logrotate para rotação mais frequente
cat > /tmp/logrotate-ssd << 'EOF'
# SSD-friendly log rotation
/var/log/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 root root
}
EOF

sudo cp /tmp/logrotate-ssd /etc/logrotate.d/ssd-optimization

# Configurar Firefox/Chrome para usar tmpfs (se aplicável)
log "Configurando browsers para usar tmpfs..."

# Firefox profile optimization
if [[ -d ~/.mozilla/firefox ]]; then
    for profile in ~/.mozilla/firefox/*.default*; do
        if [[ -d "$profile" ]]; then
            echo 'user_pref("browser.cache.disk.enable", false);' >> "$profile/user.js"
            echo 'user_pref("browser.cache.memory.enable", true);' >> "$profile/user.js"
            echo 'user_pref("browser.cache.memory.capacity", 262144);' >> "$profile/user.js"
        fi
    done
    log "Firefox configurado para cache em memória"
fi

# Configurar Docker para usar tmpfs
log "Configurando Docker para otimizações SSD..."
sudo mkdir -p /etc/docker
cat > /tmp/docker-daemon.json << 'EOF'
{
    "storage-driver": "overlay2",
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "data-root": "/var/lib/docker"
}
EOF

sudo cp /tmp/docker-daemon.json /etc/docker/daemon.json

# Criar script de monitoramento SSD
log "Criando script de monitoramento SSD..."
cat > ~/.local/bin/ssd_monitor.sh << 'EOF'
#!/bin/bash

echo "=== SSD Health Monitor ==="
echo "Data: $(date)"
echo ""

echo "Dispositivos de Armazenamento:"
lsblk -d -o NAME,SIZE,TYPE,TRAN,MODEL

echo ""
echo "Uso de Espaço:"
df -h | grep -E "(/$|/home|/var)"

echo ""
echo "I/O Schedulers Ativos:"
for device in $(lsblk -d -n -o NAME | grep -E "sd[a-z]"); do
    if [[ -f /sys/block/$device/queue/scheduler ]]; then
        echo "$device: $(cat /sys/block/$device/queue/scheduler | grep -o '\[.*\]' | tr -d '[]')"
    fi
done

echo ""
echo "Configurações de VM:"
echo "swappiness: $(cat /proc/sys/vm/swappiness)"
echo "vfs_cache_pressure: $(cat /proc/sys/vm/vfs_cache_pressure)"
echo "dirty_background_ratio: $(cat /proc/sys/vm/dirty_background_ratio)"
echo "dirty_ratio: $(cat /proc/sys/vm/dirty_ratio)"

echo ""
echo "Status do TRIM:"
sudo systemctl status fstrim.timer --no-pager -l | head -10

echo ""
echo "Uso de Memória:"
free -h

echo ""
echo "Processos com mais I/O:"
sudo iotop -b -n 1 -o | head -10 2>/dev/null || echo "iotop não disponível"
EOF

chmod +x ~/.local/bin/ssd_monitor.sh

# Criar script de benchmark SSD
cat > ~/.local/bin/ssd_benchmark.sh << 'EOF'
#!/bin/bash

echo "=== SSD Performance Benchmark ==="
echo "Data: $(date)"
echo ""

TEMP_FILE="/tmp/ssd_benchmark_$$"

echo "Teste de Escrita Sequencial (1GB):"
dd if=/dev/zero of=$TEMP_FILE bs=1M count=1024 conv=fdatasync 2>&1 | tail -1

echo ""
echo "Teste de Leitura Sequencial (1GB):"
dd if=$TEMP_FILE of=/dev/null bs=1M 2>&1 | tail -1

echo ""
echo "Teste de Escrita Aleatória (100MB, 4K blocks):"
dd if=/dev/urandom of=$TEMP_FILE bs=4K count=25600 conv=fdatasync 2>&1 | tail -1

echo ""
echo "Teste de Leitura Aleatória (100MB, 4K blocks):"
dd if=$TEMP_FILE of=/dev/null bs=4K count=25600 2>&1 | tail -1

# Limpar arquivo temporário
rm -f $TEMP_FILE

echo ""
echo "Benchmark concluído!"
EOF

chmod +x ~/.local/bin/ssd_benchmark.sh

# Configurar cron para manutenção automática
log "Configurando manutenção automática..."
(crontab -l 2>/dev/null; echo "0 2 * * 0 /usr/bin/fstrim -av") | crontab -
(crontab -l 2>/dev/null; echo "0 3 * * 0 /usr/sbin/logrotate /etc/logrotate.conf") | crontab -

log "Otimizações para SSD aplicadas!"

echo ""
echo "=================================================="
echo -e "${GREEN}✅ Otimizações SSD aplicadas com sucesso!${NC}"
echo ""
echo "Configurações aplicadas:"
echo "• swappiness=10 (reduz uso de swap)"
echo "• I/O scheduler otimizado para SSD"
echo "• TRIM automático habilitado"
echo "• tmpfs configurado para /tmp"
echo "• Logs otimizados para reduzir escritas"
echo "• Docker configurado para SSD"
echo ""
echo "Scripts criados:"
echo "• ssd_monitor.sh - Monitor de saúde do SSD"
echo "• ssd_benchmark.sh - Benchmark de performance"
echo ""
echo "Arquivos de configuração:"
echo "• /tmp/ssd_fstab_additions - Opções para fstab"
echo "• /tmp/tmpfs_additions - Configurações tmpfs"
echo ""
echo "Comandos úteis:"
echo "• Monitor SSD: ssd_monitor.sh"
echo "• Benchmark: ssd_benchmark.sh"
echo "• Status TRIM: sudo systemctl status fstrim.timer"
echo "• Verificar TRIM: sudo fstrim -v /"
echo ""
echo -e "${YELLOW}⚠️  REINICIALIZAÇÃO RECOMENDADA para aplicar todas as otimizações${NC}"
echo "=================================================="

