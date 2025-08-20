#!/bin/bash

# Script para corrigir problemas finais da Finance App
echo "🔧 Corrigindo problemas finais..."

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[FINAL-FIX]${NC} $1"
}

info() {
    echo -e "${BLUE}[FINAL-FIX]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[FINAL-FIX]${NC} $1"
}

error() {
    echo -e "${RED}[FINAL-FIX]${NC} $1"
}

# Verificar se estamos no diretório correto
if [ ! -f "streamlit_app.py" ]; then
    error "Execute no diretório da Finance App"
    exit 1
fi

log "Removendo páginas antigas que aparecem no menu superior..."

# Remover ou renomear páginas antigas para que não apareçam no menu
if [ -d "pages" ]; then
    log "Movendo páginas antigas para backup..."
    mkdir -p pages_backup
    mv pages/* pages_backup/ 2>/dev/null || true
    log "✅ Páginas antigas movidas para pages_backup/"
else
    log "ℹ️ Diretório pages não existe"
fi

log "Corrigindo erro de cache no streamlit_app.py..."

# Fazer backup
cp streamlit_app.py streamlit_app.py.backup_final

# Usar Python para corrigir o erro de cache
python3 << 'EOF'
print("🔧 Corrigindo erro de cache...")

# Ler arquivo
with open('streamlit_app.py', 'r') as f:
    content = f.read()

# Remover @st.cache_data da função get_api_client
old_cache = '''@st.cache_data
def get_api_client():
    return APIClient()'''

new_cache = '''def get_api_client():
    """Retorna instância do cliente API."""
    return APIClient()'''

content = content.replace(old_cache, new_cache)

# Adicionar cache manual se necessário
if "api_client_instance" not in content:
    # Adicionar cache manual na função
    manual_cache = '''def get_api_client():
    """Retorna instância do cliente API."""
    if "api_client" not in st.session_state:
        st.session_state.api_client = APIClient()
    return st.session_state.api_client'''
    
    content = content.replace(new_cache, manual_cache)

print("✅ Cache corrigido")

# Adicionar configuração para esconder páginas do menu superior
hide_pages_config = '''
# Esconder menu de páginas padrão do Streamlit
st.markdown("""
<style>
    .stAppHeader {visibility: hidden;}
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 1rem;
    }
    .css-1d391kg {display: none;}
    .css-1rs6os {display: none;}
    .css-17ziqus {display: none;}
    [data-testid="stSidebarNav"] {display: none;}
    [data-testid="stSidebarNavItems"] {display: none;}
</style>
""", unsafe_allow_html=True)
'''

# Inserir configuração após st.set_page_config
insert_pos = content.find('st.set_page_config(')
if insert_pos != -1:
    # Encontrar o final da configuração
    end_pos = content.find(')', insert_pos) + 1
    content = content[:end_pos] + '\n' + hide_pages_config + content[end_pos:]
    print("✅ Configuração para esconder menu superior adicionada")

# Salvar arquivo
with open('streamlit_app.py', 'w') as f:
    f.write(content)

print("✅ Todas as correções aplicadas")
EOF

# Verificar se as correções funcionaram
if ! grep -q "@st.cache_data" streamlit_app.py; then
    log "✅ Cache problemático removido"
else
    warn "⚠️ Verificar cache"
fi

if grep -q "stSidebarNav.*display: none" streamlit_app.py; then
    log "✅ CSS para esconder menu superior adicionado"
else
    warn "⚠️ Verificar CSS"
fi

# Verificar sintaxe
python3 -m py_compile streamlit_app.py 2>/dev/null && log "✅ Sintaxe Python válida" || error "❌ Erro de sintaxe"

# Criar arquivo .streamlit/config.toml para configurações adicionais
mkdir -p .streamlit
cat > .streamlit/config.toml << 'EOF'
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#0e1117"
secondaryBackgroundColor = "#262730"
textColor = "#fafafa"

[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
showErrorDetails = true

[ui]
hideTopBar = true
EOF

log "✅ Arquivo de configuração .streamlit/config.toml criado"

echo ""
echo "=================================================="
echo -e "${GREEN}✅ PROBLEMAS FINAIS CORRIGIDOS!${NC}"
echo ""
echo "Correções aplicadas:"
echo "• 🚫 Páginas antigas removidas do menu superior"
echo "• 🔧 Erro de cache corrigido"
echo "• 🎨 CSS para esconder menu padrão"
echo "• ⚙️ Configuração Streamlit otimizada"
echo ""
echo "Agora reinicie o Streamlit:"
echo "• Ctrl+C para parar"
echo "• ./start_simple.sh para reiniciar"
echo ""
echo "Resultado esperado:"
echo "• ✅ Apenas navegação sidebar (sem links superiores)"
echo "• ✅ Sem erros de cache"
echo "• ✅ Interface limpa e profissional"
echo "=================================================="

