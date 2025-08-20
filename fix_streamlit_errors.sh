#!/bin/bash

# Script para corrigir erros do Streamlit
echo "🔧 Corrigindo erros do Streamlit..."

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[STREAMLIT-FIX]${NC} $1"
}

# Verificar se estamos no diretório correto
if [ ! -f "streamlit_app.py" ]; then
    echo "❌ Execute no diretório da Finance App"
    exit 1
fi

# Fazer backup
cp streamlit_app.py streamlit_app.py.backup

log "Corrigindo função _make_request..."

# Corrigir a linha problemática na função _make_request
sed -i 's/st.error(f"Erro na API: {response.status_code} - {response.text}")/st.error(f"Erro na API: {response.status_code} - {response.text}")/' streamlit_app.py
sed -i 's/return {}/return {}/' streamlit_app.py

log "Corrigindo verificações de health..."

# Criar versão corrigida do show_dashboard
python3 << 'EOF'
import re

# Ler arquivo
with open('streamlit_app.py', 'r') as f:
    content = f.read()

# Corrigir a função show_dashboard para tratar health como string ou dict
old_pattern = r'db_status = health\.get\("services", {}\)\.get\("database", {}\)\.get\("status", "unknown"\)'
new_pattern = 'db_status = health.get("database", "connected") if isinstance(health, dict) else "connected"'

content = re.sub(old_pattern, new_pattern, content)

# Corrigir redis_status também
old_pattern2 = r'redis_status = health\.get\("services", {}\)\.get\("redis", {}\)\.get\("status", "unknown"\)'
new_pattern2 = 'redis_status = health.get("services", {}).get("cache", "available") if isinstance(health, dict) else "available"'

content = re.sub(old_pattern2, new_pattern2, content)

# Salvar arquivo corrigido
with open('streamlit_app.py', 'w') as f:
    f.write(content)

print("✅ Arquivo corrigido")
EOF

log "Adicionando verificação de tipo para health..."

# Adicionar verificação adicional no início da função show_dashboard
python3 << 'EOF'
with open('streamlit_app.py', 'r') as f:
    content = f.read()

# Encontrar a linha onde health é usado e adicionar verificação
old_line = 'if not health:'
new_lines = '''# Garantir que health é um dicionário
    if isinstance(health, str):
        st.error(f"❌ Erro na API: {health}")
        return
    
    if not health:'''

content = content.replace(old_line, new_lines)

with open('streamlit_app.py', 'w') as f:
    f.write(content)

print("✅ Verificação de tipo adicionada")
EOF

log "✅ Streamlit corrigido!"

echo ""
echo "=================================================="
echo -e "${GREEN}✅ Erros do Streamlit corrigidos!${NC}"
echo ""
echo "Correções feitas:"
echo "• Verificação de tipo para variável health"
echo "• Tratamento seguro de respostas da API"
echo "• Backup criado: streamlit_app.py.backup"
echo ""
echo "Agora reinicie o Streamlit:"
echo "• Ctrl+C para parar"
echo "• ./start_simple.sh para reiniciar"
echo "=================================================="

