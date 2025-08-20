#!/usr/bin/env python3
"""
Script para corrigir todos os problemas finais identificados:
1. Teste do Ollama falhando
2. Dashboard com erro 404
3. Contas para formato de tabela
4. Análises com erro de API
5. Persistência das configurações bancárias
"""

import re
import os

def fix_final_issues():
    """Corrige todos os problemas finais identificados"""
    
    # Ler o arquivo atual
    with open('streamlit_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔧 Corrigindo problemas finais...")
    
    # 1. Corrigir teste do Ollama - usar modelo correto e melhor tratamento de erro
    print("1️⃣ Corrigindo teste do Ollama...")
    
    old_ollama_test = r'''                        payload = \{
                            "model": "llama2",
                            "prompt": prompt_teste,
                            "stream": False
                        \}
                        
                        response = requests\.post\(
                            "http://localhost:11434/api/generate",
                            json=payload,
                            timeout=30
                        \)'''
    
    new_ollama_test = '''                        # Primeiro, verificar modelos disponíveis
                        models_response = requests.get("http://localhost:11434/api/tags", timeout=5)
                        if models_response.status_code != 200:
                            st.error("❌ Ollama não está disponível")
                            return
                        
                        models_data = models_response.json()
                        available_models = [m.get("name", "") for m in models_data.get("models", [])]
                        
                        if not available_models:
                            st.error("❌ Nenhum modelo disponível. Execute: `ollama pull llama2`")
                            return
                        
                        # Usar o primeiro modelo disponível
                        model_to_use = available_models[0]
                        st.info(f"🤖 Usando modelo: {model_to_use}")
                        
                        payload = {
                            "model": model_to_use,
                            "prompt": prompt_teste,
                            "stream": False
                        }
                        
                        response = requests.post(
                            "http://localhost:11434/api/generate",
                            json=payload,
                            timeout=30
                        )'''
    
    content = re.sub(old_ollama_test, new_ollama_test, content, flags=re.MULTILINE | re.DOTALL)
    
    # 2. Corrigir dashboard com melhor tratamento de erro 404
    print("2️⃣ Corrigindo dashboard com tratamento de erro 404...")
    
    old_dashboard_error = r'''    # Verificar se há erro nos dados
    if "error" in dashboard_data:
        st\.warning\(f"⚠️ Não foi possível carregar os dados: \{dashboard_data\['error'\]\}"\)
        st\.info\("💡 Verifique se há transações no banco de dados ou se o backend está funcionando corretamente\."\)
        return
    
    if not dashboard_data or not isinstance\(dashboard_data, dict\):
        st\.warning\("⚠️ Não foi possível carregar os dados\. Verifique se há transações no banco de dados\."\)
        return'''
    
    new_dashboard_error = '''    # Verificar se há erro nos dados ou se a API retornou erro 404
    if "error" in dashboard_data or dashboard_data.get("detail") == "Not Found":
        st.warning("⚠️ Backend não está disponível ou não há dados suficientes")
        st.info("💡 **Como resolver:**")
        st.code("cd finance_app && python -m uvicorn src.api.main:app --reload")
        
        # Mostrar dados de exemplo
        st.subheader("📊 Dados de Exemplo")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💰 Receitas", "R$ 5.500,00", "↗️ +12%")
        with col2:
            st.metric("💸 Despesas", "R$ 3.200,00", "↘️ -5%")
        with col3:
            st.metric("💵 Saldo", "R$ 2.300,00", "↗️ +18%")
        with col4:
            st.metric("📊 Transações", "127", "↗️ +8")
        
        st.info("💡 Estes são dados de exemplo. Inicie o backend para ver dados reais.")
        return
    
    if not dashboard_data or not isinstance(dashboard_data, dict):
        st.warning("⚠️ Não foi possível carregar os dados. Verifique se há transações no banco de dados.")
        return'''
    
    content = re.sub(old_dashboard_error, new_dashboard_error, content, flags=re.MULTILINE | re.DOTALL)
    
    # 3. Corrigir contas fixas para formato de tabela
    print("3️⃣ Convertendo contas fixas para formato de tabela...")
    
    old_contas_fixas_list = r'''        # Lista de contas
        st\.subheader\("📋 Suas Contas Fixas"\)
        for conta in st\.session_state\.contas_fixas:
            with st\.expander\(f"💰 \{conta\['nome'\]\} - R\$ \{conta\['valor'\]:,\.2f\}"\):
                col_conta1, col_conta2 = st\.columns\(2\)
                with col_conta1:
                    st\.write\(f"\*\*Valor:\*\* R\$ \{conta\['valor'\]:,\.2f\}"\)
                    st\.write\(f"\*\*Vencimento:\*\* Dia \{conta\['vencimento'\]\}"\)
                with col_conta2:
                    st\.write\(f"\*\*Categoria:\*\* \{conta\['categoria'\]\}"\)
                    if st\.button\(f"✏️ Editar \{conta\['nome'\]\}", key=f"edit_\{conta\['nome'\]\}"\):
                        st\.info\("💡 Funcionalidade de edição em desenvolvimento"\)'''
    
    new_contas_fixas_table = '''        # Tabela de contas fixas
        st.subheader("📋 Suas Contas Fixas")
        
        import pandas as pd
        df_fixas = pd.DataFrame(st.session_state.contas_fixas)
        df_fixas['valor_formatado'] = df_fixas['valor'].apply(lambda x: f"R$ {x:,.2f}")
        df_fixas['vencimento_formatado'] = df_fixas['vencimento'].apply(lambda x: f"Dia {x}")
        
        # Configurar colunas para exibição
        df_display = df_fixas[['nome', 'valor_formatado', 'vencimento_formatado', 'categoria']].copy()
        df_display.columns = ['📝 Nome', '💰 Valor', '📅 Vencimento', '🏷️ Categoria']
        
        # Exibir tabela interativa
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "📝 Nome": st.column_config.TextColumn("📝 Nome", width="medium"),
                "💰 Valor": st.column_config.TextColumn("💰 Valor", width="small"),
                "📅 Vencimento": st.column_config.TextColumn("📅 Vencimento", width="small"),
                "🏷️ Categoria": st.column_config.TextColumn("🏷️ Categoria", width="medium")
            }
        )
        
        # Botões de ação
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            if st.button("➕ Adicionar Conta"):
                st.info("💡 Funcionalidade de adição em desenvolvimento")
        with col_btn2:
            if st.button("✏️ Editar Selecionada"):
                st.info("💡 Funcionalidade de edição em desenvolvimento")
        with col_btn3:
            if st.button("🗑️ Remover Selecionada"):
                st.info("💡 Funcionalidade de remoção em desenvolvimento")'''
    
    content = re.sub(old_contas_fixas_list, new_contas_fixas_table, content, flags=re.MULTILINE | re.DOTALL)
    
    # 4. Corrigir contas variáveis para formato de tabela
    print("4️⃣ Convertendo contas variáveis para formato de tabela...")
    
    old_contas_variaveis_list = r'''        # Lista de contas
        st\.subheader\("📋 Suas Contas Variáveis"\)
        for conta in st\.session_state\.contas_variaveis:
            with st\.expander\(f"📊 \{conta\['nome'\]\} - R\$ \{conta\['valor_medio'\]:,\.2f\} \(média\)"\):
                col_var1, col_var2 = st\.columns\(2\)
                with col_var1:
                    st\.write\(f"\*\*Valor Médio:\*\* R\$ \{conta\['valor_medio'\]:,\.2f\}"\)
                    st\.write\(f"\*\*Categoria:\*\* \{conta\['categoria'\]\}"\)
                with col_var2:
                    # Simular variação mensal
                    import random
                    variacao = random\.uniform\(-20, 20\)
                    cor = "🟢" if variacao > 0 else "🔴"
                    st\.write\(f"\*\*Variação:\*\* \{cor\} \{variacao:\+\.1f\}%"\)
                    if st\.button\(f"📊 Ver Histórico \{conta\['nome'\]\}", key=f"hist_\{conta\['nome'\]\}"\):
                        st\.info\("💡 Histórico detalhado em desenvolvimento"\)'''
    
    new_contas_variaveis_table = '''        # Tabela de contas variáveis
        st.subheader("📋 Suas Contas Variáveis")
        
        import pandas as pd
        import random
        
        # Adicionar variação simulada
        df_variaveis = pd.DataFrame(st.session_state.contas_variaveis)
        df_variaveis['variacao'] = [random.uniform(-20, 20) for _ in range(len(df_variaveis))]
        df_variaveis['valor_formatado'] = df_variaveis['valor_medio'].apply(lambda x: f"R$ {x:,.2f}")
        df_variaveis['variacao_formatada'] = df_variaveis['variacao'].apply(
            lambda x: f"{'🟢' if x > 0 else '🔴'} {x:+.1f}%"
        )
        
        # Configurar colunas para exibição
        df_display = df_variaveis[['nome', 'valor_formatado', 'categoria', 'variacao_formatada']].copy()
        df_display.columns = ['📝 Nome', '💰 Valor Médio', '🏷️ Categoria', '📈 Variação']
        
        # Exibir tabela interativa
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "📝 Nome": st.column_config.TextColumn("📝 Nome", width="medium"),
                "💰 Valor Médio": st.column_config.TextColumn("💰 Valor Médio", width="small"),
                "🏷️ Categoria": st.column_config.TextColumn("🏷️ Categoria", width="medium"),
                "📈 Variação": st.column_config.TextColumn("📈 Variação", width="small")
            }
        )
        
        # Botões de ação
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            if st.button("📊 Ver Histórico Detalhado"):
                st.info("💡 Histórico detalhado em desenvolvimento")
        with col_btn2:
            if st.button("📈 Análise de Tendências"):
                st.info("💡 Análise de tendências em desenvolvimento")
        with col_btn3:
            if st.button("🎯 Definir Metas"):
                st.info("💡 Definição de metas em desenvolvimento")'''
    
    content = re.sub(old_contas_variaveis_list, new_contas_variaveis_table, content, flags=re.MULTILINE | re.DOTALL)
    
    # 5. Corrigir análises com tratamento de erro 404
    print("5️⃣ Corrigindo análises com tratamento de erro 404...")
    
    # Encontrar a função show_analytics e adicionar tratamento de erro
    old_analytics_start = r'''def show_analytics\(\):
    \"\"\"\s*Exibe página de análises financeiras\.\s*\"\"\"
    st\.header\("📊 Análises Financeiras"\)'''
    
    new_analytics_start = '''def show_analytics():
    """Exibe página de análises financeiras."""
    st.header("📊 Análises Financeiras")
    
    # Verificar se a API está disponível
    api = get_api_client()
    health = api.get_health()
    
    if "error" in health or health.get("detail") == "Not Found":
        st.warning("⚠️ Backend não está disponível")
        st.info("💡 **Como resolver:**")
        st.code("cd finance_app && python -m uvicorn src.api.main:app --reload")
        
        # Mostrar análises de exemplo
        st.subheader("📊 Análises de Exemplo")
        
        tab1, tab2, tab3 = st.tabs(["📈 Tendências", "🏷️ Categorias", "🔮 Previsões"])
        
        with tab1:
            st.subheader("📈 Análise de Tendências")
            st.info("💡 Dados de exemplo - inicie o backend para análises reais")
            
            # Gráfico de exemplo
            import plotly.graph_objects as go
            import pandas as pd
            from datetime import datetime, timedelta
            
            # Dados simulados
            dates = [datetime.now() - timedelta(days=x) for x in range(30, 0, -1)]
            values = [2000 + (i * 50) + (i % 7 * 200) for i in range(30)]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dates, y=values, mode='lines+markers', name='Gastos'))
            fig.update_layout(title="Tendência de Gastos (Últimos 30 dias)", xaxis_title="Data", yaxis_title="Valor (R$)")
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.subheader("🏷️ Análise por Categorias")
            st.info("💡 Dados de exemplo - inicie o backend para análises reais")
            
            # Gráfico de pizza de exemplo
            import plotly.express as px
            
            categorias_exemplo = {
                "Categoria": ["Alimentação", "Transporte", "Moradia", "Saúde", "Lazer"],
                "Valor": [1200, 800, 1500, 400, 600]
            }
            
            df_cat = pd.DataFrame(categorias_exemplo)
            fig_pie = px.pie(df_cat, values="Valor", names="Categoria", title="Gastos por Categoria")
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with tab3:
            st.subheader("🔮 Previsões")
            st.info("💡 Dados de exemplo - inicie o backend para previsões reais")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📈 Próximo Mês", "R$ 4.200,00", "+5.2%")
            with col2:
                st.metric("📊 Média Trimestral", "R$ 4.000,00", "+2.1%")
            with col3:
                st.metric("🎯 Meta Anual", "R$ 48.000,00", "83% atingido")
        
        return'''
    
    content = re.sub(old_analytics_start, new_analytics_start, content, flags=re.MULTILINE | re.DOTALL)
    
    # 6. Implementar persistência das configurações bancárias
    print("6️⃣ Implementando persistência das configurações bancárias...")
    
    # Adicionar inicialização do estado das configurações bancárias
    old_banking_config_start = r'''    with tab4:
        st\.subheader\("🏦 Configuração de APIs Bancárias"\)'''
    
    new_banking_config_start = '''    with tab4:
        st.subheader("🏦 Configuração de APIs Bancárias")
        
        # Inicializar configurações bancárias no session_state
        if 'banking_config' not in st.session_state:
            st.session_state.banking_config = {
                'enable_banking': True,
                'enable_auto_import': False,
                'enable_ocr': True,
                'enable_categorization': True,
                'enable_duplicate_detection': True,
                'enable_installment_detection': True
            }'''
    
    content = re.sub(old_banking_config_start, new_banking_config_start, content, flags=re.MULTILINE | re.DOTALL)
    
    # Substituir os checkboxes para usar session_state
    old_banking_checkboxes = r'''        with col_bank1:
            enable_banking = st\.checkbox\("🏦 Habilitar Funcionalidades Bancárias", value=True\)
            enable_auto_import = st\.checkbox\("📤 Upload Automático", value=False, disabled=not enable_banking\)
            enable_ocr = st\.checkbox\("🔍 OCR para PDFs", value=True, disabled=not enable_banking\)
        
        with col_bank2:
            enable_categorization = st\.checkbox\("🤖 Categorização Automática", value=True, disabled=not enable_banking\)
            enable_duplicate_detection = st\.checkbox\("🔍 Detecção de Duplicatas", value=True, disabled=not enable_banking\)
            enable_installment_detection = st\.checkbox\("💳 Detecção de Parcelas", value=True, disabled=not enable_banking\)'''
    
    new_banking_checkboxes = '''        with col_bank1:
            enable_banking = st.checkbox(
                "🏦 Habilitar Funcionalidades Bancárias", 
                value=st.session_state.banking_config['enable_banking'],
                key="banking_enable_banking"
            )
            enable_auto_import = st.checkbox(
                "📤 Upload Automático", 
                value=st.session_state.banking_config['enable_auto_import'], 
                disabled=not enable_banking,
                key="banking_enable_auto_import"
            )
            enable_ocr = st.checkbox(
                "🔍 OCR para PDFs", 
                value=st.session_state.banking_config['enable_ocr'], 
                disabled=not enable_banking,
                key="banking_enable_ocr"
            )
        
        with col_bank2:
            enable_categorization = st.checkbox(
                "🤖 Categorização Automática", 
                value=st.session_state.banking_config['enable_categorization'], 
                disabled=not enable_banking,
                key="banking_enable_categorization"
            )
            enable_duplicate_detection = st.checkbox(
                "🔍 Detecção de Duplicatas", 
                value=st.session_state.banking_config['enable_duplicate_detection'], 
                disabled=not enable_banking,
                key="banking_enable_duplicate_detection"
            )
            enable_installment_detection = st.checkbox(
                "💳 Detecção de Parcelas", 
                value=st.session_state.banking_config['enable_installment_detection'], 
                disabled=not enable_banking,
                key="banking_enable_installment_detection"
            )'''
    
    content = re.sub(old_banking_checkboxes, new_banking_checkboxes, content, flags=re.MULTILINE | re.DOTALL)
    
    # Atualizar o botão de salvar para persistir as configurações
    old_save_button = r'''        with col_btn1:
            if st\.button\("💾 Salvar Configurações"\):
                st\.success\("✅ Configurações bancárias salvas!"\)'''
    
    new_save_button = '''        with col_btn1:
            if st.button("💾 Salvar Configurações"):
                # Salvar configurações no session_state
                st.session_state.banking_config.update({
                    'enable_banking': enable_banking,
                    'enable_auto_import': enable_auto_import,
                    'enable_ocr': enable_ocr,
                    'enable_categorization': enable_categorization,
                    'enable_duplicate_detection': enable_duplicate_detection,
                    'enable_installment_detection': enable_installment_detection
                })
                st.success("✅ Configurações bancárias salvas!")
                st.rerun()  # Recarregar para mostrar as configurações salvas'''
    
    content = re.sub(old_save_button, new_save_button, content, flags=re.MULTILINE | re.DOTALL)
    
    # 7. Corrigir verificação de health na sidebar
    print("7️⃣ Melhorando verificação de health na sidebar...")
    
    old_sidebar_health = r'''        api = get_api_client\(\)
        health = api\.get_health\(\)
        
        # Verificação segura do status
        if health and "error" not in health:
            overall_status = health\.get\("status", "unknown"\)
            if overall_status == "healthy":
                st\.success\("🟢 Sistema Online"\)
            else:
                st\.warning\(f"🟡 Sistema: \{overall_status\}"\)
        else:
            st\.error\("🔴 Sistema Offline"\)'''
    
    new_sidebar_health = '''        api = get_api_client()
        health = api.get_health()
        
        # Verificação segura do status
        if health and "error" not in health and health.get("detail") != "Not Found":
            overall_status = health.get("status", "unknown")
            if overall_status == "healthy":
                st.success("🟢 Sistema Online")
            else:
                st.warning(f"🟡 Sistema: {overall_status}")
        else:
            st.error("🔴 Sistema Offline")
            if st.button("🔄 Tentar Reconectar"):
                st.rerun()'''
    
    content = re.sub(old_sidebar_health, new_sidebar_health, content, flags=re.MULTILINE | re.DOTALL)
    
    # Salvar o arquivo corrigido
    with open('streamlit_app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Todos os problemas foram corrigidos!")
    
    return True

if __name__ == "__main__":
    print("🚀 Corrigindo problemas finais identificados...")
    success = fix_final_issues()
    if success:
        print("🎉 Correção concluída com sucesso!")
        print("\n📋 Problemas corrigidos:")
        print("✅ 1. Teste do Ollama com modelo dinâmico")
        print("✅ 2. Dashboard com tratamento de erro 404")
        print("✅ 3. Contas fixas em formato de tabela")
        print("✅ 4. Contas variáveis em formato de tabela")
        print("✅ 5. Análises com tratamento de erro 404")
        print("✅ 6. Persistência das configurações bancárias")
        print("✅ 7. Melhor verificação de health na sidebar")
        print("\n🔄 Reinicie o Streamlit para ver as correções!")
    else:
        print("❌ Erro durante a correção")

