#!/bin/bash

# Script para corrigir cores de status e página LLM duplicada
echo "🔧 Corrigindo cores de status e página LLM..."

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[STATUS-COLORS-FIX]${NC} $1"
}

info() {
    echo -e "${BLUE}[STATUS-COLORS-FIX]${NC} $1"
}

# Verificar se estamos no diretório correto
if [ ! -f "streamlit_app.py" ]; then
    echo "❌ Execute no diretório da Finance App"
    exit 1
fi

# Fazer backup
cp streamlit_app.py streamlit_app.py.backup_colors

log "Corrigindo cores dos status no Dashboard..."

# Usar Python para corrigir as cores
python3 << 'EOF'
import re

# Ler arquivo
with open('streamlit_app.py', 'r') as f:
    content = f.read()

print("🔧 Corrigindo cores do Database...")

# Corrigir cor do Database (connected = verde)
old_db_pattern = r'db_status = health\.get\("database", "connected"\) if isinstance\(health, dict\) else "connected"\s+status_color = "🟢" if db_status == "healthy" else "🔴"'
new_db_pattern = '''db_status = health.get("database", "connected") if isinstance(health, dict) else "connected"
            status_color = "🟢" if db_status in ["healthy", "connected"] else "🔴"'''

content = re.sub(old_db_pattern, new_db_pattern, content)

# Se não encontrou o padrão acima, tentar padrão mais simples
if "connected" in content and "🔴" in content:
    # Procurar e corrigir linha por linha
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'db_status = ' in line and 'connected' in line:
            # Próxima linha deve ter status_color
            if i + 1 < len(lines) and 'status_color' in lines[i + 1]:
                lines[i + 1] = '            status_color = "🟢" if db_status in ["healthy", "connected"] else "🔴"'
                print(f"✅ Corrigida linha {i+2}: Database status color")
    content = '\n'.join(lines)

print("🔧 Corrigindo cores do Redis...")

# Corrigir cor do Redis (available = verde)
old_redis_pattern = r'redis_status = health\.get\("services", {}\)\.get\("cache", "available"\) if isinstance\(health, dict\) else "available"\s+status_color = "🟢" if redis_status == "healthy" else "🔴"'
new_redis_pattern = '''redis_status = health.get("services", {}).get("cache", "available") if isinstance(health, dict) else "available"
            status_color = "🟢" if redis_status in ["healthy", "available"] else "🔴"'''

content = re.sub(old_redis_pattern, new_redis_pattern, content)

# Se não encontrou, corrigir manualmente
if "available" in content:
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'redis_status' in line and 'available' in line:
            # Próxima linha deve ter status_color
            if i + 1 < len(lines) and 'status_color' in lines[i + 1] and 'redis' not in lines[i + 1]:
                lines[i + 1] = '            status_color = "🟢" if redis_status in ["healthy", "available"] else "🔴"'
                print(f"✅ Corrigida linha {i+2}: Redis status color")
    content = '\n'.join(lines)

print("🔧 Corrigindo status do Ollama...")

# Corrigir status do Ollama para usar função centralizada
if "ollama_status = \"unknown\"" in content:
    old_ollama = '''            ollama_status = "unknown"
            status_color = "🔴"
            st.write(f"{status_color} **Ollama:** {ollama_status}")'''
    
    new_ollama = '''            try:
                ollama_info = get_ollama_status()
                if ollama_info["status"] == "online":
                    status_color = "🟢"
                    ollama_status = "funcionando"
                elif ollama_info["status"] == "offline":
                    status_color = "🔴"
                    ollama_status = "offline"
                elif ollama_info["status"] == "model_missing":
                    status_color = "🟡"
                    ollama_status = "modelo não encontrado"
                else:
                    status_color = "🔴"
                    ollama_status = "erro"
            except:
                status_color = "🔴"
                ollama_status = "unknown"
            st.write(f"{status_color} **Ollama:** {ollama_status}")'''
    
    content = content.replace(old_ollama, new_ollama)
    print("✅ Status do Ollama corrigido")

print("🔧 Removendo atalho LLM da sidebar...")

# Remover ou corrigir atalho LLM da sidebar que está criando página separada
# Procurar por links ou botões LLM na sidebar
if "st.info(" in content and "LLM" in content:
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'st.info(' in line and 'LLM' in line and 'sidebar' in content[max(0, i-10):i+10]:
            # Substituir por link que muda a página principal
            if 'Esta aplicação usa Ollama' in line:
                lines[i] = '        st.info("Esta aplicação usa Ollama (LLM local) para categorização automática e análises inteligentes.")'
                print(f"✅ Corrigida linha {i+1}: Removido link LLM problemático")
    content = '\n'.join(lines)

# Adicionar botão para ir para página LLM na sidebar
sidebar_llm_button = '''
        # Botão para página LLM
        if st.button("🤖 Ir para LLM", use_container_width=True):
            st.session_state.page = "🤖 LLM"
            st.rerun()
'''

# Inserir botão antes do Status na sidebar
insert_pos = content.find('st.markdown("### 📋 Status")')
if insert_pos != -1:
    content = content[:insert_pos] + sidebar_llm_button + '\n        ' + content[insert_pos:]
    print("✅ Botão LLM adicionado na sidebar")

# Salvar arquivo
with open('streamlit_app.py', 'w') as f:
    f.write(content)

print("✅ Todas as correções aplicadas")
EOF

log "Verificando se as correções foram aplicadas..."

# Verificar se as correções funcionaram
if grep -q "connected.*🟢" streamlit_app.py; then
    log "✅ Cor do Database corrigida"
else
    log "⚠️ Verificar cor do Database"
fi

if grep -q "available.*🟢" streamlit_app.py; then
    log "✅ Cor do Redis corrigida"
else
    log "⚠️ Verificar cor do Redis"
fi

if grep -q "get_ollama_status()" streamlit_app.py; then
    log "✅ Status do Ollama usando função centralizada"
else
    log "⚠️ Verificar status do Ollama"
fi

# Verificar sintaxe
python3 -m py_compile streamlit_app.py 2>/dev/null && log "✅ Sintaxe Python válida" || log "⚠️ Verificar sintaxe"

echo ""
echo "=================================================="
echo -e "${GREEN}✅ Cores de status e página LLM corrigidas!${NC}"
echo ""
echo "Correções aplicadas:"
echo "• 🟢 Database 'connected' = Verde"
echo "• 🟢 Redis 'available' = Verde"  
echo "• 🤖 Ollama usando status centralizado"
echo "• 🔗 Atalho LLM da sidebar corrigido"
echo "• 🎯 Navegação unificada"
echo ""
echo "Agora reinicie o Streamlit:"
echo "• Ctrl+C para parar"
echo "• ./start_simple.sh para reiniciar"
echo ""
echo "Status devem aparecer com cores corretas:"
echo "• 🟢 Database: connected"
echo "• 🟢 Redis: available"
echo "• 🟢 Ollama: funcionando"
echo "=================================================="

