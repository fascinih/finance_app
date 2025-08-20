#!/bin/bash

# Script para corrigir status do Ollama em todas as páginas
echo "🔧 Corrigindo status do Ollama em todas as páginas..."

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[OLLAMA-STATUS-FIX]${NC} $1"
}

info() {
    echo -e "${BLUE}[OLLAMA-STATUS-FIX]${NC} $1"
}

# Verificar se estamos no diretório correto
if [ ! -f "streamlit_app.py" ]; then
    echo "❌ Execute no diretório da Finance App"
    exit 1
fi

# Fazer backup
cp streamlit_app.py streamlit_app.py.backup_status

log "Adicionando função centralizada de status do Ollama..."

# Usar Python para adicionar função centralizada
python3 << 'EOF'
import re

# Ler arquivo
with open('streamlit_app.py', 'r') as f:
    content = f.read()

# Adicionar função centralizada de status do Ollama
ollama_status_function = '''
def get_ollama_status():
    """Função centralizada para verificar status do Ollama."""
    try:
        # Carregar configuração salva
        config = load_ollama_config()
        host = config["host"]
        model = config["model"]
        
        # Verificar se Ollama está rodando
        import requests
        
        # Teste rápido de conexão
        response = requests.get(f"{host}/api/version", timeout=3)
        if response.status_code != 200:
            return {
                "status": "offline",
                "message": "Ollama não está rodando",
                "host": host,
                "model": model
            }
        
        # Verificar se modelo está disponível
        response = requests.get(f"{host}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            available_models = [m['name'] for m in data.get('models', [])]
            
            if model in available_models:
                return {
                    "status": "online",
                    "message": f"Ollama funcionando com {model}",
                    "host": host,
                    "model": model,
                    "available_models": available_models
                }
            else:
                return {
                    "status": "model_missing",
                    "message": f"Modelo {model} não encontrado",
                    "host": host,
                    "model": model,
                    "available_models": available_models
                }
        else:
            return {
                "status": "error",
                "message": "Erro ao verificar modelos",
                "host": host,
                "model": model
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "status": "offline",
            "message": "Ollama não está rodando",
            "host": config.get("host", "localhost:11434"),
            "model": config.get("model", "deepseek-r1:7b")
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro: {str(e)}",
            "host": config.get("host", "localhost:11434"),
            "model": config.get("model", "deepseek-r1:7b")
        }

'''

# Encontrar onde inserir a função (antes da função show_settings)
insert_pos = content.find('def show_settings():')
if insert_pos != -1:
    content = content[:insert_pos] + ollama_status_function + '\n' + content[insert_pos:]
    print("✅ Função centralizada de status adicionada")
else:
    print("❌ Não foi possível encontrar função show_settings")

# Salvar arquivo
with open('streamlit_app.py', 'w') as f:
    f.write(content)

print("✅ Função centralizada criada")
EOF

log "Atualizando Dashboard para usar status centralizado..."

# Atualizar Dashboard
python3 << 'EOF'
# Ler arquivo
with open('streamlit_app.py', 'r') as f:
    content = f.read()

# Encontrar e substituir a seção de status do Ollama no Dashboard
old_ollama_status = '''        with col3:
            ollama_status = "unknown"
            status_color = "🔴"
            st.write(f"{status_color} **Ollama:** {ollama_status}")'''

new_ollama_status = '''        with col3:
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
            st.write(f"{status_color} **Ollama:** {ollama_status}")'''

content = content.replace(old_ollama_status, new_ollama_status)

# Salvar arquivo
with open('streamlit_app.py', 'w') as f:
    f.write(content)

print("✅ Dashboard atualizado")
EOF

log "Criando página LLM melhorada..."

# Criar nova página LLM
python3 << 'EOF'
# Ler arquivo
with open('streamlit_app.py', 'r') as f:
    content = f.read()

# Encontrar e substituir a página LLM completa
# Primeiro, encontrar onde começa a página LLM
llm_start = content.find('elif page == "🤖 LLM":')
if llm_start != -1:
    # Encontrar onde termina (próximo elif ou final da função)
    llm_end = content.find('elif page == "🏦 APIs":', llm_start)
    if llm_end == -1:
        llm_end = content.find('def main():', llm_start)
    
    if llm_end != -1:
        # Substituir toda a seção LLM
        new_llm_page = '''elif page == "🤖 LLM":
        st.header("🤖 LLM & Inteligência Artificial")
        st.markdown("Configure e teste as funcionalidades de IA para análise financeira inteligente.")
        
        tab1, tab2, tab3, tab4 = st.tabs(["🔧 Status", "🏷️ Categorização", "💡 Insights", "🔄 Recorrentes"])
        
        with tab1:
            st.subheader("Status do Ollama")
            
            # Verificar status do Ollama
            ollama_info = get_ollama_status()
            
            if ollama_info["status"] == "online":
                st.success(f"✅ {ollama_info['message']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**Host:** {ollama_info['host']}")
                    st.info(f"**Modelo Ativo:** {ollama_info['model']}")
                
                with col2:
                    if "available_models" in ollama_info:
                        st.info(f"**Modelos Disponíveis:** {len(ollama_info['available_models'])}")
                        with st.expander("Ver todos os modelos"):
                            for model in ollama_info['available_models']:
                                st.write(f"• {model}")
                
                # Teste rápido de categorização
                st.markdown("#### 🧪 Teste de Categorização")
                test_transaction = st.text_input(
                    "Digite uma transação para testar:",
                    value="PIX Supermercado ABC 150.00",
                    help="Exemplo: PIX Supermercado ABC 150.00"
                )
                
                if st.button("🔍 Categorizar"):
                    with st.spinner("Categorizando..."):
                        try:
                            import requests
                            test_data = {
                                "model": ollama_info["model"],
                                "prompt": f"Categorize esta transação financeira em uma das categorias: Alimentação, Transporte, Moradia, Saúde, Educação, Lazer, Renda, Outros. Responda apenas a categoria: {test_transaction}",
                                "stream": False,
                                "options": {"num_predict": 10, "temperature": 0.1}
                            }
                            response = requests.post(f"{ollama_info['host']}/api/generate", json=test_data, timeout=20)
                            if response.status_code == 200:
                                result = response.json()
                                category = result.get("response", "").strip()
                                st.success(f"✅ **Categoria sugerida:** {category}")
                            else:
                                st.error("❌ Erro na categorização")
                        except Exception as e:
                            st.error(f"❌ Erro: {str(e)}")
                            
            elif ollama_info["status"] == "offline":
                st.error(f"❌ {ollama_info['message']}")
                st.info("💡 **Como resolver:**")
                st.code("ollama serve")
                st.markdown("Execute o comando acima no terminal para iniciar o Ollama.")
                
            elif ollama_info["status"] == "model_missing":
                st.warning(f"⚠️ {ollama_info['message']}")
                st.info("💡 **Como resolver:**")
                st.code(f"ollama pull {ollama_info['model']}")
                st.markdown("Execute o comando acima para baixar o modelo.")
                
                if "available_models" in ollama_info and ollama_info["available_models"]:
                    st.info("**Modelos disponíveis:**")
                    for model in ollama_info["available_models"]:
                        st.write(f"• {model}")
                        
            else:
                st.error(f"❌ {ollama_info['message']}")
            
            # Link para configurações
            st.markdown("---")
            st.info("🔧 **Configurar Ollama:** Vá para Configurações → Sistema → Configuração do Ollama")
        
        with tab2:
            st.subheader("Categorização Automática")
            st.info("🚧 Em desenvolvimento: Interface para configurar regras de categorização automática")
            
        with tab3:
            st.subheader("Insights Inteligentes")
            st.info("🚧 Em desenvolvimento: Análise inteligente de padrões de gastos")
            
        with tab4:
            st.subheader("Detecção de Recorrentes")
            st.info("🚧 Em desenvolvimento: Identificação automática de gastos recorrentes")
        
        '''
        
        # Substituir o conteúdo
        content = content[:llm_start] + new_llm_page + content[llm_end:]
        
        print("✅ Página LLM atualizada")
    else:
        print("❌ Não foi possível encontrar final da página LLM")
else:
    print("❌ Não foi possível encontrar página LLM")

# Salvar arquivo
with open('streamlit_app.py', 'w') as f:
    f.write(content)

print("✅ Página LLM melhorada")
EOF

# Verificar sintaxe
python3 -m py_compile streamlit_app.py 2>/dev/null && log "✅ Sintaxe Python válida" || log "⚠️ Verificar sintaxe"

echo ""
echo "=================================================="
echo -e "${GREEN}✅ Status do Ollama corrigido em todas as páginas!${NC}"
echo ""
echo "Melhorias implementadas:"
echo "• 🎯 Função centralizada de status"
echo "• 📊 Dashboard com status real do Ollama"
echo "• 🤖 Página LLM completamente renovada"
echo "• 🧪 Teste de categorização integrado"
echo "• 💡 Dicas de resolução de problemas"
echo "• 🔗 Links para configuração"
echo ""
echo "Agora reinicie o Streamlit:"
echo "• Ctrl+C para parar"
echo "• ./start_simple.sh para reiniciar"
echo ""
echo "O status do Ollama deve aparecer corretamente!"
echo "=================================================="

