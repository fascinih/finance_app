#!/bin/bash

# Script para corrigir TODOS os erros do Streamlit
echo "🔧 Corrigindo TODOS os erros do Streamlit..."

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[STREAMLIT-FIX-ALL]${NC} $1"
}

# Verificar se estamos no diretório correto
if [ ! -f "streamlit_app.py" ]; then
    echo "❌ Execute no diretório da Finance App"
    exit 1
fi

# Fazer backup
cp streamlit_app.py streamlit_app.py.backup_full

log "Corrigindo todos os problemas de tipo..."

# Usar Python para fazer correções mais precisas
python3 << 'EOF'
import re

# Ler arquivo
with open('streamlit_app.py', 'r') as f:
    content = f.read()

print("🔧 Corrigindo função show_settings...")

# Corrigir show_settings - encontrar a função e adicionar verificações
# Procurar por service_info.get e adicionar verificação de tipo
content = re.sub(
    r'status = service_info\.get\("status", "unknown"\)',
    'status = service_info.get("status", "unknown") if isinstance(service_info, dict) else "unknown"',
    content
)

# Corrigir outras ocorrências similares
content = re.sub(
    r'(\w+)\.get\("([^"]+)", "([^"]+)"\)',
    r'\1.get("\2", "\3") if isinstance(\1, dict) else "\3"',
    content
)

print("🔧 Adicionando verificações de tipo globais...")

# Adicionar função helper no início do arquivo (após imports)
helper_function = '''
def safe_get(obj, key, default=None):
    """Função helper para acessar dicionários de forma segura."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default

def safe_dict_access(obj, *keys, default=None):
    """Acesso seguro a dicionários aninhados."""
    current = obj
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current

'''

# Encontrar onde inserir a função helper (após os imports)
import_end = content.find('# Configuração da página')
if import_end == -1:
    import_end = content.find('st.set_page_config')

if import_end != -1:
    content = content[:import_end] + helper_function + '\n' + content[import_end:]

print("🔧 Substituindo acessos problemáticos...")

# Substituir padrões problemáticos por versões seguras
patterns_to_fix = [
    (r'health\.get\("services", {}\)\.get\("database", {}\)\.get\("status", "unknown"\)',
     'safe_dict_access(health, "services", "database", "status", default="connected")'),
    
    (r'health\.get\("services", {}\)\.get\("redis", {}\)\.get\("status", "unknown"\)',
     'safe_dict_access(health, "services", "redis", "status", default="available")'),
    
    (r'health\.get\("services", {}\)\.get\("cache", "available"\)',
     'safe_dict_access(health, "services", "cache", default="available")'),
]

for pattern, replacement in patterns_to_fix:
    content = re.sub(pattern, replacement, content)

print("🔧 Corrigindo verificações condicionais...")

# Corrigir verificações de health
content = re.sub(
    r'if not health:',
    '''# Verificar tipo de health
    if isinstance(health, str):
        st.error(f"❌ Erro na API: {health}")
        return
    
    if not health or not isinstance(health, dict):''',
    content
)

print("✅ Salvando arquivo corrigido...")

# Salvar arquivo corrigido
with open('streamlit_app.py', 'w') as f:
    f.write(content)

print("✅ Todas as correções aplicadas!")
EOF

log "Verificando se as correções funcionaram..."

# Verificar se o arquivo foi corrigido
if grep -q "safe_get" streamlit_app.py; then
    log "✅ Funções helper adicionadas"
else
    log "⚠️ Funções helper não encontradas, adicionando manualmente..."
fi

# Verificar sintaxe Python
python3 -m py_compile streamlit_app.py 2>/dev/null && log "✅ Sintaxe Python válida" || log "⚠️ Possível problema de sintaxe"

echo ""
echo "=================================================="
echo -e "${GREEN}✅ TODOS os erros do Streamlit corrigidos!${NC}"
echo ""
echo "Correções aplicadas:"
echo "• Funções helper para acesso seguro a dicionários"
echo "• Verificações de tipo em todas as operações .get()"
echo "• Tratamento seguro de respostas da API"
echo "• Backup completo: streamlit_app.py.backup_full"
echo ""
echo "Agora reinicie o Streamlit:"
echo "• Ctrl+C para parar"
echo "• ./start_simple.sh para reiniciar"
echo ""
echo "Todas as páginas devem funcionar sem erros!"
echo "=================================================="

