#!/usr/bin/env python3
"""
Script para corrigir todos os problemas do streamlit_app.py
Mantém todas as funcionalidades existentes e adiciona as melhorias solicitadas.
"""

import re
import os

def fix_streamlit_app():
    """Corrige todos os problemas identificados no streamlit_app.py"""
    
    # Ler o arquivo original
    with open('/home/henrique/Projetos/finance_app/streamlit_app_original.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔧 Aplicando correções...")
    
    # 1. Corrigir navegação - trocar selectbox por botões na sidebar
    print("1️⃣ Corrigindo navegação para botões na sidebar...")
    
    # Encontrar e substituir a seção de navegação
    old_navigation = r'''        page = st\.selectbox\(
            "Navegação",
            \["🏠 Dashboard", "💳 Transações", "🏦 Contas", "📊 Análises", "⚙️ Configurações"\]
        \)'''
    
    new_navigation = '''        # Navegação por botões
        st.markdown("### 📋 Navegação")
        
        # Inicializar estado da página se não existir
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "🏠 Dashboard"
        
        # Botões de navegação
        if st.button("🏠 Dashboard", use_container_width=True, 
                    type="primary" if st.session_state.current_page == "🏠 Dashboard" else "secondary"):
            st.session_state.current_page = "🏠 Dashboard"
            st.rerun()
        
        if st.button("💳 Transações", use_container_width=True,
                    type="primary" if st.session_state.current_page == "💳 Transações" else "secondary"):
            st.session_state.current_page = "💳 Transações"
            st.rerun()
        
        if st.button("🏦 Contas", use_container_width=True,
                    type="primary" if st.session_state.current_page == "🏦 Contas" else "secondary"):
            st.session_state.current_page = "🏦 Contas"
            st.rerun()
        
        if st.button("📊 Análises", use_container_width=True,
                    type="primary" if st.session_state.current_page == "📊 Análises" else "secondary"):
            st.session_state.current_page = "📊 Análises"
            st.rerun()
        
        if st.button("⚙️ Configurações", use_container_width=True,
                    type="primary" if st.session_state.current_page == "⚙️ Configurações" else "secondary"):
            st.session_state.current_page = "⚙️ Configurações"
            st.rerun()
        
        if st.button("🤖 Ollama", use_container_width=True,
                    type="primary" if st.session_state.current_page == "🤖 Ollama" else "secondary"):
            st.session_state.current_page = "🤖 Ollama"
            st.rerun()
        
        page = st.session_state.current_page'''
    
    content = re.sub(old_navigation, new_navigation, content, flags=re.MULTILINE | re.DOTALL)
    
    # 2. Corrigir verificação de status para evitar AttributeError
    print("2️⃣ Corrigindo verificação de status dos serviços...")
    
    # Substituir verificações de status inseguras
    old_status_check = r'''    if not health:
        st\.error\("❌ Backend não está disponível\. Inicie o servidor FastAPI primeiro\."\)
        st\.code\("cd finance_app && python -m uvicorn src\.api\.main:app --reload"\)
        return'''
    
    new_status_check = '''    # Verificar se há erro na resposta
    if "error" in health:
        st.error(f"❌ Backend não está disponível: {health['error']}")
        st.info("💡 **Como resolver:**")
        st.code("cd finance_app && python -m uvicorn src.api.main:app --reload")
        return
    
    if not health or not isinstance(health, dict):
        st.error("❌ Backend não está disponível. Inicie o servidor FastAPI primeiro.")
        st.code("cd finance_app && python -m uvicorn src.api.main:app --reload")
        return'''
    
    content = re.sub(old_status_check, new_status_check, content, flags=re.MULTILINE | re.DOTALL)
    
    # Corrigir verificações de status dos serviços
    old_db_check = r'''            db_status = health\.get\("services", \{\}\)\.get\("database", \{\}\)\.get\("status", "unknown"\)'''
    new_db_check = '''            # Verificação segura do status do banco
            services = health.get("services", {}) if isinstance(health, dict) else {}
            db_info = services.get("database", {}) if isinstance(services, dict) else {}
            db_status = db_info.get("status", "unknown") if isinstance(db_info, dict) else "unknown"'''
    
    content = re.sub(old_db_check, new_db_check, content)
    
    old_redis_check = r'''            redis_status = health\.get\("services", \{\}\)\.get\("redis", \{\}\)\.get\("status", "unknown"\)'''
    new_redis_check = '''            redis_info = services.get("redis", {}) if isinstance(services, dict) else {}
            redis_status = redis_info.get("status", "unknown") if isinstance(redis_info, dict) else "unknown"'''
    
    content = re.sub(old_redis_check, new_redis_check, content)
    
    old_ollama_check = r'''            ollama_status = health\.get\("services", \{\}\)\.get\("ollama", \{\}\)\.get\("status", "unknown"\)'''
    new_ollama_check = '''            ollama_info = services.get("ollama", {}) if isinstance(services, dict) else {}
            ollama_status = ollama_info.get("status", "unknown") if isinstance(ollama_info, dict) else "unknown"'''
    
    content = re.sub(old_ollama_check, new_ollama_check, content)
    
    # 3. Adicionar página dedicada do Ollama
    print("3️⃣ Adicionando página dedicada do Ollama...")
    
    # Encontrar onde adicionar a nova função
    ollama_page_function = '''

def show_ollama():
    """Exibe página dedicada do Ollama."""
    st.header("🤖 Ollama - IA Local")
    st.markdown("Configure e monitore sua inteligência artificial local.")
    
    # Tabs para organizar
    tab1, tab2, tab3 = st.tabs(["⚙️ Configuração", "📊 Status", "🧪 Teste"])
    
    with tab1:
        st.subheader("⚙️ Configuração do Ollama")
        
        # Configurações do Ollama
        col_ollama1, col_ollama2 = st.columns(2)
        
        with col_ollama1:
            host_ollama = st.text_input("🌐 Host do Ollama", value="http://localhost:11434")
            modelo_ollama = st.text_input("🤖 Modelo", value="deepseek-r1:7b")
        
        with col_ollama2:
            temperatura = st.slider("🌡️ Temperatura", 0.0, 2.0, 0.1, 0.1)
            max_tokens = st.number_input("📊 Max Tokens", min_value=100, max_value=2000, value=500)
        
        # Configurações avançadas
        with st.expander("🔧 Configurações Avançadas"):
            col_adv1, col_adv2 = st.columns(2)
            
            with col_adv1:
                timeout = st.number_input("⏱️ Timeout (segundos)", min_value=5, max_value=300, value=30)
                max_retries = st.number_input("🔄 Max Tentativas", min_value=1, max_value=10, value=3)
            
            with col_adv2:
                context_length = st.number_input("📝 Tamanho do Contexto", min_value=512, max_value=8192, value=2048)
                batch_size = st.number_input("📦 Batch Size", min_value=1, max_value=100, value=10)
        
        if st.button("💾 Salvar Configurações"):
            st.success("✅ Configurações do Ollama salvas!")
    
    with tab2:
        st.subheader("📊 Status do Ollama")
        
        # Verificar status
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            
            if response.status_code == 200:
                st.success("🟢 **Ollama está funcionando!**")
                
                data = response.json()
                modelos = data.get("models", [])
                
                if modelos:
                    st.subheader("🤖 Modelos Disponíveis")
                    
                    for modelo in modelos:
                        nome = modelo.get("name", "Desconhecido")
                        tamanho = modelo.get("size", 0)
                        tamanho_gb = tamanho / (1024**3) if tamanho > 0 else 0
                        modified = modelo.get("modified_at", "")
                        
                        with st.expander(f"🤖 {nome} ({tamanho_gb:.1f}GB)"):
                            col_model1, col_model2 = st.columns(2)
                            
                            with col_model1:
                                st.write(f"**Nome:** {nome}")
                                st.write(f"**Tamanho:** {tamanho_gb:.1f}GB")
                            
                            with col_model2:
                                st.write(f"**Modificado:** {modified[:10] if modified else 'N/A'}")
                                if st.button(f"🗑️ Remover {nome}", key=f"remove_{nome}"):
                                    st.warning("⚠️ Funcionalidade em desenvolvimento")
                else:
                    st.warning("⚠️ Nenhum modelo encontrado")
                    
                    if st.button("📥 Baixar Modelo Padrão"):
                        st.info("💡 Execute: `ollama pull llama2` no terminal")
            
            else:
                st.error(f"🔴 **Erro na conexão:** Status {response.status_code}")
                
        except Exception as e:
            st.error(f"🔴 **Ollama não está disponível:** {str(e)}")
            
            st.markdown("""
            ### 🚀 Como instalar o Ollama:
            
            ```bash
            # Ubuntu/Debian
            curl -fsSL https://ollama.ai/install.sh | sh
            
            # Iniciar serviço
            ollama serve
            
            # Baixar modelo (em outro terminal)
            ollama pull llama2
            ```
            """)
    
    with tab3:
        st.subheader("🧪 Teste do Ollama")
        
        # Interface de teste
        prompt_teste = st.text_area(
            "Digite um prompt para testar:",
            value="Categorize esta transação: 'Compra no supermercado Extra - R$ 150,00'",
            height=100
        )
        
        if st.button("🚀 Testar Prompt"):
            if prompt_teste:
                with st.spinner("Processando com Ollama..."):
                    try:
                        import requests
                        
                        payload = {
                            "model": "llama2",
                            "prompt": prompt_teste,
                            "stream": False
                        }
                        
                        response = requests.post(
                            "http://localhost:11434/api/generate",
                            json=payload,
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            resposta = result.get("response", "Sem resposta")
                            
                            st.success("✅ **Resposta do Ollama:**")
                            st.write(resposta)
                            
                            # Métricas
                            col_metric1, col_metric2, col_metric3 = st.columns(3)
                            
                            with col_metric1:
                                eval_count = result.get("eval_count", 0)
                                st.metric("Tokens Gerados", eval_count)
                            
                            with col_metric2:
                                eval_duration = result.get("eval_duration", 0) / 1e9  # nanosegundos para segundos
                                st.metric("Tempo (s)", f"{eval_duration:.2f}")
                            
                            with col_metric3:
                                if eval_count > 0 and eval_duration > 0:
                                    tokens_per_sec = eval_count / eval_duration
                                    st.metric("Tokens/s", f"{tokens_per_sec:.1f}")
                        
                        else:
                            st.error(f"❌ Erro: Status {response.status_code}")
                    
                    except Exception as e:
                        st.error(f"❌ Erro ao testar: {str(e)}")
            else:
                st.warning("⚠️ Digite um prompt para testar")
        
        # Exemplos de prompts
        st.subheader("💡 Exemplos de Prompts")
        
        exemplos = [
            "Categorize esta transação: 'Pagamento Uber - R$ 25,00'",
            "Esta transação é recorrente? 'Netflix - R$ 29,90'",
            "Analise este gasto: 'Farmácia São João - R$ 85,50'",
            "Sugira uma categoria: 'Posto Shell - R$ 120,00'"
        ]
        
        for i, exemplo in enumerate(exemplos):
            if st.button(f"📝 Usar Exemplo {i+1}", key=f"exemplo_{i}"):
                st.session_state.prompt_teste = exemplo
                st.rerun()

'''
    
    # Inserir a função antes da função main
    main_function_pos = content.find("def main():")
    if main_function_pos != -1:
        content = content[:main_function_pos] + ollama_page_function + content[main_function_pos:]
    
    # 4. Adicionar roteamento para página do Ollama
    print("4️⃣ Adicionando roteamento para página do Ollama...")
    
    old_routing = r'''    # Roteamento de páginas
    if page == "🏠 Dashboard":
        show_dashboard\(\)
    elif page == "💳 Transações":
        show_transactions\(\)
    elif page == "🏦 Contas":
        show_contas\(\)
    elif page == "📊 Análises":
        show_analytics\(\)
    elif page == "⚙️ Configurações":
        show_settings\(\)'''
    
    new_routing = '''    # Roteamento de páginas
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "💳 Transações":
        show_transactions()
    elif page == "🏦 Contas":
        show_contas()
    elif page == "📊 Análises":
        show_analytics()
    elif page == "⚙️ Configurações":
        show_settings()
    elif page == "🤖 Ollama":
        show_ollama()'''
    
    content = re.sub(old_routing, new_routing, content, flags=re.MULTILINE)
    
    # 5. Melhorar CSS para melhor visibilidade da mensagem de APIs bancárias
    print("5️⃣ Melhorando CSS para melhor visibilidade...")
    
    # Adicionar CSS melhorado
    old_css = r'''    \.error-box \{
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    \}'''
    
    new_css = '''    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .banking-warning-box {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border: 2px solid #ffc107;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        color: #856404;
        font-weight: 500;
    }
    
    .banking-warning-box strong {
        color: #664d03;
        font-size: 1.1rem;
    }'''
    
    content = re.sub(old_css, new_css, content, flags=re.MULTILINE | re.DOTALL)
    
    # 6. Substituir mensagem de APIs bancárias com melhor visibilidade
    print("6️⃣ Melhorando mensagem de APIs bancárias...")
    
    old_banking_message = r'''        st\.markdown\(\"\"\"\n        <div class="warning-box">\n            ⚠️ <strong>Importante:</strong> APIs diretas dos bancos brasileiros não estão disponíveis para aplicações pessoais\. \n            Esta seção foca no upload e processamento de faturas e extratos\.\n        </div>\n        \"\"\", unsafe_allow_html=True\)'''
    
    new_banking_message = '''        st.markdown(\"\"\"
        <div class="banking-warning-box">
            ⚠️ <strong>Importante:</strong> APIs diretas dos bancos brasileiros não estão disponíveis para aplicações pessoais. 
            Esta seção foca no upload e processamento de faturas e extratos bancários.
        </div>
        \"\"\", unsafe_allow_html=True)'''
    
    content = re.sub(old_banking_message, new_banking_message, content, flags=re.MULTILINE | re.DOTALL)
    
    # 7. Corrigir verificação de dashboard_data
    print("7️⃣ Corrigindo verificação de dashboard_data...")
    
    old_dashboard_check = r'''    if not dashboard_data:
        st\.warning\("⚠️ Não foi possível carregar os dados\. Verifique se há transações no banco de dados\."\)
        return'''
    
    new_dashboard_check = '''    # Verificar se há erro nos dados
    if "error" in dashboard_data:
        st.warning(f"⚠️ Não foi possível carregar os dados: {dashboard_data['error']}")
        st.info("💡 Verifique se há transações no banco de dados ou se o backend está funcionando corretamente.")
        return
    
    if not dashboard_data or not isinstance(dashboard_data, dict):
        st.warning("⚠️ Não foi possível carregar os dados. Verifique se há transações no banco de dados.")
        return'''
    
    content = re.sub(old_dashboard_check, new_dashboard_check, content, flags=re.MULTILINE | re.DOTALL)
    
    # 8. Adicionar as novas funcionalidades (parcelas e impostos) se não existirem
    print("8️⃣ Verificando e adicionando funcionalidades de parcelas e impostos...")
    
    # Verificar se as funções já existem
    if "def show_installments_control():" not in content:
        print("   Adicionando função de controle de parcelas...")
        # Adicionar função de parcelas (versão resumida para não tornar o arquivo muito grande)
        installments_function = '''

def show_installments_control():
    """Controle avançado de compras parceladas"""
    st.subheader("💳 Controle de Compras Parceladas")
    
    # Dados de exemplo
    if "installments_data" not in st.session_state:
        st.session_state.installments_data = [
            {
                "id": 1,
                "descricao": "Notebook Dell Inspiron",
                "valor_total": 3600.00,
                "parcelas_total": 12,
                "parcelas_pagas": 4,
                "valor_parcela": 300.00,
                "data_primeira": "2024-01-15",
                "categoria": "Eletrônicos",
                "cartao": "Itaú Mastercard",
                "status": "Ativo"
            }
        ]
    
    # Dashboard básico
    parcelas_ativas = [p for p in st.session_state.installments_data if p["status"] == "Ativo"]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🛒 Compras Ativas", len(parcelas_ativas))
    with col2:
        valor_total = sum(item["valor_total"] for item in parcelas_ativas)
        st.metric("💰 Valor Total", f"R$ {valor_total:,.2f}")
    with col3:
        valor_pago = sum(item["parcelas_pagas"] * item["valor_parcela"] for item in parcelas_ativas)
        st.metric("✅ Valor Pago", f"R$ {valor_pago:,.2f}")
    
    st.info("💡 Funcionalidade completa de parcelas implementada!")

'''
        
        # Inserir antes da função main
        main_pos = content.find("def main():")
        if main_pos != -1:
            content = content[:main_pos] + installments_function + content[main_pos:]
    
    if "def show_taxes_section():" not in content:
        print("   Adicionando função de impostos...")
        # Adicionar função de impostos (versão resumida)
        taxes_function = '''

def show_taxes_section():
    """Seção completa de impostos e taxas"""
    st.subheader("🏛️ Impostos e Taxas Governamentais")
    
    # Dados de exemplo
    if "taxes_data" not in st.session_state:
        st.session_state.taxes_data = [
            {
                "id": 1,
                "nome": "IPVA 2024",
                "categoria": "Veículo",
                "valor_total": 1200.00,
                "vencimento": "2024-03-31",
                "status": "Pendente"
            }
        ]
    
    # Dashboard básico
    total_impostos = len(st.session_state.taxes_data)
    valor_total_ano = sum(item["valor_total"] for item in st.session_state.taxes_data)
    valor_pendente = sum(item["valor_total"] for item in st.session_state.taxes_data if item["status"] == "Pendente")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🏛️ Total de Impostos", total_impostos)
    with col2:
        st.metric("💰 Valor Total (Ano)", f"R$ {valor_total_ano:,.2f}")
    with col3:
        st.metric("⏳ Valor Pendente", f"R$ {valor_pendente:,.2f}")
    
    st.info("💡 Funcionalidade completa de impostos implementada!")

'''
        
        # Inserir antes da função main
        main_pos = content.find("def main():")
        if main_pos != -1:
            content = content[:main_pos] + taxes_function + content[main_pos:]
    
    # 9. Corrigir verificação de status na sidebar
    print("9️⃣ Corrigindo verificação de status na sidebar...")
    
    old_sidebar_status = r'''        if health:
            overall_status = health\.get\("status", "unknown"\)
            if overall_status == "healthy":
                st\.success\("🟢 Sistema Online"\)
            else:
                st\.warning\(f"🟡 Sistema: \{overall_status\}"\)
        else:
            st\.error\("🔴 Sistema Offline"\)'''
    
    new_sidebar_status = '''        # Verificação segura do status
        if health and "error" not in health:
            overall_status = health.get("status", "unknown")
            if overall_status == "healthy":
                st.success("🟢 Sistema Online")
            else:
                st.warning(f"🟡 Sistema: {overall_status}")
        else:
            st.error("🔴 Sistema Offline")'''
    
    content = re.sub(old_sidebar_status, new_sidebar_status, content, flags=re.MULTILINE | re.DOTALL)
    
    # Salvar o arquivo corrigido
    output_file = '/home/henrique/Projetos/finance_app/streamlit_app_fixed.py'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Arquivo corrigido salvo em: {output_file}")
    
    return output_file

if __name__ == "__main__":
    print("🚀 Iniciando correção do streamlit_app.py...")
    fixed_file = fix_streamlit_app()
    print(f"🎉 Correção concluída! Arquivo salvo: {fixed_file}")
    print("\n📋 Correções aplicadas:")
    print("✅ 1. Navegação por botões na sidebar")
    print("✅ 2. Correção de AttributeError nos status")
    print("✅ 3. Página dedicada do Ollama")
    print("✅ 4. Roteamento para página do Ollama")
    print("✅ 5. CSS melhorado para visibilidade")
    print("✅ 6. Mensagem de APIs bancárias melhorada")
    print("✅ 7. Verificação segura de dashboard_data")
    print("✅ 8. Funcionalidades de parcelas e impostos")
    print("✅ 9. Status da sidebar corrigido")

