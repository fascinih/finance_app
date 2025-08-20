#!/bin/bash

# Script para corrigir problemas de timeout do Ollama
echo "🔧 Corrigindo timeouts do Ollama..."

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[OLLAMA-TIMEOUT-FIX]${NC} $1"
}

info() {
    echo -e "${BLUE}[OLLAMA-TIMEOUT-FIX]${NC} $1"
}

# Verificar se estamos no diretório correto
if [ ! -f "streamlit_app.py" ]; then
    echo "❌ Execute no diretório da Finance App"
    exit 1
fi

# Fazer backup
cp streamlit_app.py streamlit_app.py.backup_timeout

log "Melhorando funções de timeout do Ollama..."

# Usar Python para corrigir as funções
python3 << 'EOF'
import re

# Ler arquivo
with open('streamlit_app.py', 'r') as f:
    content = f.read()

# Substituir função test_ollama_connection por versão melhorada
old_function = r'def test_ollama_connection\(host, model\):.*?except Exception as e:\s+return False, f"Erro: \{str\(e\)\}"'

new_function = '''def test_ollama_connection(host, model):
    """Testa conexão com Ollama com timeouts melhorados."""
    try:
        import requests
        import json
        
        # Primeiro, testar se Ollama está rodando (timeout curto)
        try:
            response = requests.get(f"{host}/api/version", timeout=3)
            if response.status_code != 200:
                return False, "Ollama não está respondendo"
        except requests.exceptions.Timeout:
            return False, "Ollama não está respondendo (timeout)"
        except requests.exceptions.ConnectionError:
            return False, "Ollama não está rodando"
        
        # Verificar se o modelo existe (sem gerar texto)
        try:
            response = requests.get(f"{host}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                available_models = [m['name'] for m in data.get('models', [])]
                if model not in available_models:
                    return False, f"Modelo '{model}' não encontrado. Disponíveis: {', '.join(available_models[:3])}"
            else:
                return False, "Não foi possível verificar modelos"
        except requests.exceptions.Timeout:
            return False, "Timeout ao verificar modelos"
        
        return True, f"Ollama funcionando. Modelo '{model}' disponível"
            
    except Exception as e:
        return False, f"Erro: {str(e)}"'''

# Substituir usando regex com flag DOTALL
content = re.sub(old_function, new_function, content, flags=re.DOTALL)

# Substituir função get_ollama_models por versão melhorada
old_models_function = r'def get_ollama_models\(host\):.*?except Exception as e:\s+return False, \[\]'

new_models_function = '''def get_ollama_models(host):
    """Lista modelos disponíveis no Ollama com timeout melhorado."""
    try:
        import requests
        
        response = requests.get(f"{host}/api/tags", timeout=8)
        if response.status_code == 200:
            data = response.json()
            models = []
            for model in data.get('models', []):
                name = model['name']
                size = model.get('size', 0)
                size_gb = size / (1024**3) if size > 0 else 0
                models.append(f"{name} ({size_gb:.1f}GB)" if size_gb > 0 else name)
            return True, models
        else:
            return False, []
            
    except requests.exceptions.Timeout:
        return False, ["Timeout ao buscar modelos"]
    except requests.exceptions.ConnectionError:
        return False, ["Ollama não está rodando"]
    except Exception as e:
        return False, [f"Erro: {str(e)}"]'''

content = re.sub(old_models_function, new_models_function, content, flags=re.DOTALL)

# Adicionar função de teste rápido melhorada
quick_test_function = '''
def quick_ollama_test(host, model):
    """Teste rápido do Ollama com prompt simples."""
    try:
        import requests
        
        # Prompt muito simples para teste rápido
        test_data = {
            "model": model,
            "prompt": "Responda apenas: OK",
            "stream": False,
            "options": {
                "num_predict": 5,  # Máximo 5 tokens
                "temperature": 0.1
            }
        }
        
        response = requests.post(f"{host}/api/generate", json=test_data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return True, result.get("response", "Sem resposta").strip()
        else:
            return False, f"Erro HTTP {response.status_code}"
            
    except requests.exceptions.Timeout:
        return False, "Timeout - modelo pode estar carregando"
    except requests.exceptions.ConnectionError:
        return False, "Conexão falhou"
    except Exception as e:
        return False, f"Erro: {str(e)}"

'''

# Adicionar a nova função antes da função show_settings
insert_pos = content.find('def show_settings():')
if insert_pos != -1:
    content = content[:insert_pos] + quick_test_function + '\n' + content[insert_pos:]

# Salvar arquivo
with open('streamlit_app.py', 'w') as f:
    f.write(content)

print("✅ Funções de timeout melhoradas")
EOF

log "Atualizando interface para usar timeouts melhorados..."

# Atualizar a interface para usar a nova função de teste rápido
python3 << 'EOF'
# Ler arquivo
with open('streamlit_app.py', 'r') as f:
    content = f.read()

# Substituir o botão de teste rápido por versão melhorada
old_test_button = '''        with col4:
            if st.button("🧪 Teste Rápido"):
                with st.spinner("Testando modelo..."):
                    try:
                        import requests
                        test_data = {
                            "model": ollama_model,
                            "prompt": "Categorize esta transação: PIX Supermercado ABC 150.00",
                            "stream": False
                        }
                        response = requests.post(f"{ollama_host}/api/generate", json=test_data, timeout=15)
                        if response.status_code == 200:
                            result = response.json()
                            st.success("✅ Teste bem-sucedido!")
                            st.write("**Resposta:**", result.get("response", "Sem resposta"))
                        else:
                            st.error("❌ Falha no teste")
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")'''

new_test_button = '''        with col4:
            if st.button("🧪 Teste Rápido"):
                with st.spinner("Testando modelo (pode demorar se estiver carregando)..."):
                    success, message = quick_ollama_test(ollama_host, ollama_model)
                    if success:
                        st.success(f"✅ Teste bem-sucedido!")
                        st.write(f"**Resposta:** {message}")
                    else:
                        st.error(f"❌ {message}")
                        if "timeout" in message.lower() or "carregando" in message.lower():
                            st.info("💡 **Dica:** O modelo pode estar sendo carregado pela primeira vez. Aguarde alguns minutos e tente novamente.")'''

content = content.replace(old_test_button, new_test_button)

# Melhorar o botão de listar modelos
old_list_button = '''        with col2:
            if st.button("📋 Listar Modelos"):
                with st.spinner("Buscando modelos..."):
                    success, models = get_ollama_models(ollama_host)
                    if success and models:
                        st.success("Modelos disponíveis:")
                        for model in models:
                            st.write(f"• {model}")
                    else:
                        st.error("❌ Não foi possível listar modelos")'''

new_list_button = '''        with col2:
            if st.button("📋 Listar Modelos"):
                with st.spinner("Buscando modelos..."):
                    success, models = get_ollama_models(ollama_host)
                    if success and models:
                        st.success("Modelos disponíveis:")
                        for model in models:
                            st.write(f"• {model}")
                    else:
                        if isinstance(models, list) and models:
                            st.error("❌ Problemas ao listar:")
                            for error in models:
                                st.write(f"• {error}")
                        else:
                            st.error("❌ Não foi possível listar modelos")'''

content = content.replace(old_list_button, new_list_button)

# Salvar arquivo
with open('streamlit_app.py', 'w') as f:
    f.write(content)

print("✅ Interface atualizada com timeouts melhorados")
EOF

# Verificar sintaxe
python3 -m py_compile streamlit_app.py 2>/dev/null && log "✅ Sintaxe Python válida" || log "⚠️ Verificar sintaxe"

echo ""
echo "=================================================="
echo -e "${GREEN}✅ Timeouts do Ollama corrigidos!${NC}"
echo ""
echo "Melhorias implementadas:"
echo "• ⏱️ Timeouts mais inteligentes (3s, 5s, 8s, 30s)"
echo "• 🔍 Verificação de modelo antes de testar"
echo "• 📋 Lista de modelos com tamanhos"
echo "• 🧪 Teste rápido com prompt simples"
echo "• 💡 Dicas para problemas de timeout"
echo "• ⚠️ Mensagens de erro mais claras"
echo ""
echo "Agora reinicie o Streamlit:"
echo "• Ctrl+C para parar"
echo "• ./start_simple.sh para reiniciar"
echo ""
echo "Os timeouts devem estar muito melhores!"
echo "=================================================="

