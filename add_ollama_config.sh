#!/bin/bash

# Script para adicionar configuração do Ollama na página de Configurações
echo "🤖 Adicionando configuração do Ollama..."

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[OLLAMA-CONFIG]${NC} $1"
}

info() {
    echo -e "${BLUE}[OLLAMA-CONFIG]${NC} $1"
}

# Verificar se estamos no diretório correto
if [ ! -f "streamlit_app.py" ]; then
    echo "❌ Execute no diretório da Finance App"
    exit 1
fi

# Fazer backup
cp streamlit_app.py streamlit_app.py.backup_ollama

log "Adicionando funções de configuração do Ollama..."

# Usar Python para adicionar as funções
python3 << 'EOF'
import re

# Ler arquivo
with open('streamlit_app.py', 'r') as f:
    content = f.read()

# Adicionar funções helper para Ollama após as funções existentes
ollama_functions = '''
def test_ollama_connection(host, model):
    """Testa conexão com Ollama."""
    try:
        import requests
        import json
        
        # Testar se Ollama está rodando
        response = requests.get(f"{host}/api/version", timeout=5)
        if response.status_code != 200:
            return False, "Ollama não está rodando"
        
        # Testar modelo específico
        test_data = {
            "model": model,
            "prompt": "Test",
            "stream": False
        }
        
        response = requests.post(f"{host}/api/generate", json=test_data, timeout=10)
        if response.status_code == 200:
            return True, "Conexão e modelo funcionando"
        else:
            return False, f"Modelo '{model}' não disponível"
            
    except requests.exceptions.ConnectionError:
        return False, "Não foi possível conectar ao Ollama"
    except requests.exceptions.Timeout:
        return False, "Timeout na conexão"
    except Exception as e:
        return False, f"Erro: {str(e)}"

def get_ollama_models(host):
    """Lista modelos disponíveis no Ollama."""
    try:
        import requests
        
        response = requests.get(f"{host}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [model['name'] for model in data.get('models', [])]
            return True, models
        else:
            return False, []
            
    except Exception as e:
        return False, []

def save_ollama_config(host, model, temperature, max_tokens):
    """Salva configuração do Ollama."""
    config = {
        "ollama_host": host,
        "ollama_model": model,
        "ollama_temperature": temperature,
        "ollama_max_tokens": max_tokens
    }
    
    # Salvar em session_state
    for key, value in config.items():
        st.session_state[key] = value
    
    return True

def load_ollama_config():
    """Carrega configuração do Ollama."""
    return {
        "host": st.session_state.get("ollama_host", "http://localhost:11434"),
        "model": st.session_state.get("ollama_model", "deepseek-r1:7b"),
        "temperature": st.session_state.get("ollama_temperature", 0.1),
        "max_tokens": st.session_state.get("ollama_max_tokens", 500)
    }

'''

# Encontrar onde inserir as funções (antes da função show_settings)
insert_pos = content.find('def show_settings():')
if insert_pos != -1:
    content = content[:insert_pos] + ollama_functions + '\n' + content[insert_pos:]
    print("✅ Funções do Ollama adicionadas")
else:
    print("❌ Não foi possível encontrar função show_settings")

# Salvar arquivo
with open('streamlit_app.py', 'w') as f:
    f.write(content)

print("✅ Funções helper do Ollama adicionadas")
EOF

log "Modificando função show_settings para incluir configuração do Ollama..."

# Adicionar seção do Ollama na função show_settings
python3 << 'EOF'
# Ler arquivo
with open('streamlit_app.py', 'r') as f:
    content = f.read()

# Encontrar a seção tab1 e adicionar configuração do Ollama
old_tab1_content = '''    with tab1:
        st.subheader("Configurações do Sistema")
        
        api = get_api_client()
        
        # Status dos serviços
        with st.spinner("Verificando status dos serviços..."):
            health = api.get_health()
        
        if health:
            st.success("✅ API conectada com sucesso!")
            
            services = health.get("services", {})
            
            for service_name, service_info in services.items():
                status = service_info.get("status", "unknown") if isinstance(service_info, dict) else "unknown"
                response_time = service_info.get("response_time", 0) if isinstance(service_info, dict) else 0
                
                if status == "healthy":
                    st.success(f"✅ {service_name.title()}: {status} ({response_time:.3f}s)")
                else:
                    st.error(f"❌ {service_name.title()}: {status}")
        else:
            st.error("❌ Não foi possível conectar à API")'''

new_tab1_content = '''    with tab1:
        st.subheader("Configurações do Sistema")
        
        # Seção API Backend
        st.markdown("#### 🔗 Backend API")
        api = get_api_client()
        
        # Status dos serviços
        with st.spinner("Verificando status dos serviços..."):
            health = api.get_health()
        
        if health:
            st.success("✅ API conectada com sucesso!")
            
            services = health.get("services", {})
            
            for service_name, service_info in services.items():
                status = service_info.get("status", "unknown") if isinstance(service_info, dict) else "unknown"
                response_time = service_info.get("response_time", 0) if isinstance(service_info, dict) else 0
                
                if status == "healthy":
                    st.success(f"✅ {service_name.title()}: {status} ({response_time:.3f}s)")
                else:
                    st.error(f"❌ {service_name.title()}: {status}")
        else:
            st.error("❌ Não foi possível conectar à API")
        
        st.markdown("---")
        
        # Seção Configuração do Ollama
        st.markdown("#### 🤖 Configuração do Ollama")
        
        # Carregar configuração atual
        config = load_ollama_config()
        
        col1, col2 = st.columns(2)
        
        with col1:
            ollama_host = st.text_input(
                "Host do Ollama",
                value=config["host"],
                help="URL do servidor Ollama (ex: http://localhost:11434)"
            )
            
            ollama_model = st.text_input(
                "Modelo",
                value=config["model"],
                help="Nome do modelo a ser usado (ex: deepseek-r1:7b, mistral:7b)"
            )
        
        with col2:
            ollama_temperature = st.slider(
                "Temperatura",
                min_value=0.0,
                max_value=2.0,
                value=config["temperature"],
                step=0.1,
                help="Controla a criatividade das respostas (0.0 = mais preciso, 2.0 = mais criativo)"
            )
            
            ollama_max_tokens = st.number_input(
                "Máximo de Tokens",
                min_value=50,
                max_value=2000,
                value=config["max_tokens"],
                step=50,
                help="Número máximo de tokens na resposta"
            )
        
        # Botões de ação
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔍 Testar Conexão"):
                with st.spinner("Testando conexão..."):
                    success, message = test_ollama_connection(ollama_host, ollama_model)
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
        
        with col2:
            if st.button("📋 Listar Modelos"):
                with st.spinner("Buscando modelos..."):
                    success, models = get_ollama_models(ollama_host)
                    if success and models:
                        st.success("Modelos disponíveis:")
                        for model in models:
                            st.write(f"• {model}")
                    else:
                        st.error("❌ Não foi possível listar modelos")
        
        with col3:
            if st.button("💾 Salvar Config"):
                save_ollama_config(ollama_host, ollama_model, ollama_temperature, ollama_max_tokens)
                st.success("✅ Configuração salva!")
        
        with col4:
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
                        st.error(f"❌ Erro: {str(e)}")
        
        # Informações sobre o Ollama
        with st.expander("ℹ️ Informações sobre Ollama", expanded=False):
            st.markdown("""
            **Ollama** é um servidor local de LLM que permite executar modelos de IA em sua máquina.
            
            **Modelos Recomendados:**
            - `deepseek-r1:7b` - Excelente para análise financeira e raciocínio
            - `mistral:7b` - Modelo versátil e rápido
            - `llama3.2:3b` - Modelo menor, mais rápido
            
            **Como instalar modelos:**
            ```bash
            ollama pull deepseek-r1:7b
            ollama pull mistral:7b
            ```
            
            **Status do Ollama:**
            - ✅ Rodando: Ollama está ativo e pronto
            - ❌ Parado: Execute `ollama serve` no terminal
            """)'''

# Substituir o conteúdo
content = content.replace(old_tab1_content, new_tab1_content)

# Salvar arquivo
with open('streamlit_app.py', 'w') as f:
    f.write(content)

print("✅ Seção de configuração do Ollama adicionada")
EOF

# Verificar se as mudanças foram aplicadas
if grep -q "Configuração do Ollama" streamlit_app.py; then
    log "✅ Configuração do Ollama adicionada com sucesso"
else
    log "⚠️ Verificar se as mudanças foram aplicadas"
fi

# Verificar sintaxe
python3 -m py_compile streamlit_app.py 2>/dev/null && log "✅ Sintaxe Python válida" || log "⚠️ Verificar sintaxe"

echo ""
echo "=================================================="
echo -e "${GREEN}✅ Configuração do Ollama implementada!${NC}"
echo ""
echo "Funcionalidades adicionadas:"
echo "• 🔧 Configuração de host e modelo"
echo "• 🎛️ Controles de temperatura e tokens"
echo "• 🔍 Teste de conexão"
echo "• 📋 Listagem de modelos disponíveis"
echo "• 💾 Salvamento de configurações"
echo "• 🧪 Teste rápido de categorização"
echo "• ℹ️ Informações e documentação"
echo ""
echo "Agora reinicie o Streamlit:"
echo "• Ctrl+C para parar"
echo "• ./start_simple.sh para reiniciar"
echo ""
echo "Vá para Configurações → Sistema para configurar o Ollama!"
echo "=================================================="

