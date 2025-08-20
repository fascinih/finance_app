#!/bin/bash

# Script para corrigir especificamente a página de configurações
echo "🔧 Corrigindo página de configurações..."

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[SETTINGS-FIX]${NC} $1"
}

# Verificar se estamos no diretório correto
if [ ! -f "streamlit_app.py" ]; then
    echo "❌ Execute no diretório da Finance App"
    exit 1
fi

# Fazer backup
cp streamlit_app.py streamlit_app.py.backup_settings

log "Corrigindo função show_settings especificamente..."

# Usar Python para fazer correção precisa
python3 << 'EOF'
# Ler arquivo
with open('streamlit_app.py', 'r') as f:
    lines = f.readlines()

# Encontrar e corrigir as linhas problemáticas na função show_settings
for i, line in enumerate(lines):
    # Corrigir linha 596: status = service_info.get("status", "unknown")
    if 'status = service_info.get("status", "unknown")' in line:
        lines[i] = '                status = service_info.get("status", "unknown") if isinstance(service_info, dict) else "unknown"\n'
        print(f"✅ Corrigida linha {i+1}: status")
    
    # Corrigir linha 597: response_time = service_info.get("response_time", 0)
    elif 'response_time = service_info.get("response_time", 0)' in line:
        lines[i] = '                response_time = service_info.get("response_time", 0) if isinstance(service_info, dict) else 0\n'
        print(f"✅ Corrigida linha {i+1}: response_time")

# Salvar arquivo corrigido
with open('streamlit_app.py', 'w') as f:
    f.writelines(lines)

print("✅ Função show_settings corrigida!")
EOF

log "Verificando se a correção funcionou..."

# Verificar se as linhas foram corrigidas
if grep -q "isinstance(service_info, dict)" streamlit_app.py; then
    log "✅ Verificações de tipo adicionadas"
else
    log "⚠️ Aplicando correção alternativa..."
    
    # Correção alternativa usando sed
    sed -i 's/status = service_info\.get("status", "unknown")/status = service_info.get("status", "unknown") if isinstance(service_info, dict) else "unknown"/' streamlit_app.py
    sed -i 's/response_time = service_info\.get("response_time", 0)/response_time = service_info.get("response_time", 0) if isinstance(service_info, dict) else 0/' streamlit_app.py
fi

# Verificar sintaxe
python3 -m py_compile streamlit_app.py 2>/dev/null && log "✅ Sintaxe Python válida" || log "⚠️ Verificar sintaxe"

echo ""
echo "=================================================="
echo -e "${GREEN}✅ Página de configurações corrigida!${NC}"
echo ""
echo "Correções aplicadas:"
echo "• Verificação de tipo para service_info"
echo "• Tratamento seguro de status e response_time"
echo "• Backup: streamlit_app.py.backup_settings"
echo ""
echo "Agora reinicie o Streamlit:"
echo "• Ctrl+C para parar"
echo "• ./start_simple.sh para reiniciar"
echo ""
echo "A página de configurações deve funcionar!"
echo "=================================================="

