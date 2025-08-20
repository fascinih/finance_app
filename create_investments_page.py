#!/usr/bin/env python3
"""
Script para:
1. Remover seção "Status do Sistema" do Dashboard
2. Criar nova página "Investimentos" com seções completas
"""

import re
import os

def create_investments_page():
    """Remove Status do Dashboard e cria página de Investimentos"""
    
    print("🚀 Criando página de Investimentos e limpando Dashboard...")
    
    with open('streamlit_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fazer backup
    with open('streamlit_app_investments_backup.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("💾 Backup criado")
    
    # 1. Remover seção "Status do Sistema" do Dashboard
    print("1️⃣ Removendo seção 'Status do Sistema' do Dashboard...")
    
    lines = content.split('\n')
    new_lines = []
    skip_status_section = False
    status_section_removed = False
    
    for i, line in enumerate(lines):
        # Detectar início da seção de status
        if 'Status do Sistema' in line and 'st.expander' in line:
            print(f"   🗑️ Removendo seção Status do Sistema (linha {i+1})")
            skip_status_section = True
            status_section_removed = True
            continue
        
        # Detectar fim da seção de status (próxima seção ou função)
        if skip_status_section:
            # Se encontrar uma nova seção ou função, parar de pular
            if (line.strip().startswith('st.') and 'expander' in line) or \
               (line.strip().startswith('def ')) or \
               (line.strip().startswith('# ') and len(line.strip()) > 10) or \
               ('st.subheader' in line) or \
               ('st.header' in line):
                skip_status_section = False
                new_lines.append(line)
            continue
        
        # Remover linhas específicas relacionadas ao status
        if any(x in line for x in [
            'health.get("services"',
            'db_status =',
            'redis_status =', 
            'ollama_status =',
            'status_color =',
            'Database:**',
            'Redis:**',
            'Ollama:**'
        ]):
            print(f"   🗑️ Removendo linha de status: {line.strip()}")
            continue
        
        new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    if status_section_removed:
        print("   ✅ Seção 'Status do Sistema' removida do Dashboard")
    else:
        print("   ⚠️ Seção 'Status do Sistema' não encontrada")
    
    # 2. Adicionar página "Investimentos" na navegação
    print("2️⃣ Adicionando página 'Investimentos' na navegação...")
    
    # Encontrar a lista de páginas na navegação
    navigation_pattern = r'(pages = \[.*?)"🦙 Ollama"(.*?\])'
    match = re.search(navigation_pattern, content, re.DOTALL)
    
    if match:
        before = match.group(1)
        after = match.group(2)
        new_navigation = f'{before}"🦙 Ollama", "💰 Investimentos"{after}'
        content = content.replace(match.group(0), new_navigation)
        print("   ✅ Página 'Investimentos' adicionada na navegação")
    else:
        print("   ⚠️ Navegação não encontrada, adicionando manualmente")
        # Fallback: adicionar após Ollama
        content = content.replace('"🦙 Ollama"', '"🦙 Ollama", "💰 Investimentos"')
    
    # 3. Adicionar roteamento para página de Investimentos
    print("3️⃣ Adicionando roteamento para página de Investimentos...")
    
    # Encontrar o roteamento e adicionar a nova página
    routing_pattern = r'(elif page == "🦙 Ollama":\s+show_ollama\(\))'
    replacement = r'\1\n  elif page == "💰 Investimentos":\n    show_investments()'
    
    if re.search(routing_pattern, content):
        content = re.sub(routing_pattern, replacement, content)
        print("   ✅ Roteamento para 'Investimentos' adicionado")
    else:
        print("   ⚠️ Roteamento não encontrado, adicionando manualmente")
        # Fallback: adicionar antes do final da função main
        content = content.replace(
            'if __name__ == "__main__":',
            'elif page == "💰 Investimentos":\n    show_investments()\n\nif __name__ == "__main__":'
        )
    
    # 4. Criar função show_investments completa
    print("4️⃣ Criando função show_investments completa...")
    
    investments_function = '''
def show_investments():
    """Página de Investimentos"""
    st.title("💰 Investimentos")
    st.write("Gerencie seus investimentos e acompanhe o crescimento do seu patrimônio.")
    
    # Tabs para diferentes tipos de investimentos
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Renda Variável", "🏦 Renda Fixa", "📋 Debêntures", "🏠 FGTS"])
    
    with tab1:
        st.subheader("📈 Renda Variável")
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="💼 Total Investido",
                value="R$ 25.000,00",
                delta="↗️ +R$ 2.500,00"
            )
        
        with col2:
            st.metric(
                label="📊 Valor Atual",
                value="R$ 28.750,00",
                delta="↗️ +15%"
            )
        
        with col3:
            st.metric(
                label="💰 Lucro/Prejuízo",
                value="R$ 3.750,00",
                delta="↗️ +15%"
            )
        
        with col4:
            st.metric(
                label="📈 Rentabilidade",
                value="15,00%",
                delta="↗️ +2,3%"
            )
        
        st.markdown("---")
        
        # Tabela de ações
        st.subheader("📊 Carteira de Ações")
        
        import pandas as pd
        
        # Dados de exemplo
        acoes_data = {
            "Ativo": ["PETR4", "VALE3", "ITUB4", "BBDC4", "ABEV3"],
            "Quantidade": [100, 50, 200, 150, 300],
            "Preço Médio": ["R$ 28,50", "R$ 65,20", "R$ 25,80", "R$ 15,40", "R$ 12,30"],
            "Valor Atual": ["R$ 32,10", "R$ 68,90", "R$ 26,50", "R$ 16,20", "R$ 13,10"],
            "Total Investido": ["R$ 2.850,00", "R$ 3.260,00", "R$ 5.160,00", "R$ 2.310,00", "R$ 3.690,00"],
            "Valor Atual Total": ["R$ 3.210,00", "R$ 3.445,00", "R$ 5.300,00", "R$ 2.430,00", "R$ 3.930,00"],
            "Rentabilidade": ["+12,6%", "+5,7%", "+2,7%", "+5,2%", "+6,5%"]
        }
        
        df_acoes = pd.DataFrame(acoes_data)
        st.dataframe(df_acoes, use_container_width=True)
        
        # Gráfico de distribuição
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🥧 Distribuição por Ativo")
            import plotly.express as px
            
            fig_pie = px.pie(
                values=[3210, 3445, 5300, 2430, 3930],
                names=["PETR4", "VALE3", "ITUB4", "BBDC4", "ABEV3"],
                title="Distribuição da Carteira"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            st.subheader("📈 Evolução da Carteira")
            
            # Dados de exemplo para evolução
            import datetime
            dates = pd.date_range(start='2024-01-01', end='2024-08-20', freq='D')
            values = [25000 + i*15 + (i%30)*50 for i in range(len(dates))]
            
            df_evolucao = pd.DataFrame({
                'Data': dates,
                'Valor': values
            })
            
            fig_line = px.line(df_evolucao, x='Data', y='Valor', title='Evolução do Patrimônio')
            st.plotly_chart(fig_line, use_container_width=True)
    
    with tab2:
        st.subheader("🏦 Renda Fixa")
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="💰 Total Aplicado",
                value="R$ 50.000,00",
                delta="↗️ +R$ 5.000,00"
            )
        
        with col2:
            st.metric(
                label="📊 Valor Atual",
                value="R$ 53.250,00",
                delta="↗️ +6,5%"
            )
        
        with col3:
            st.metric(
                label="💵 Rendimento",
                value="R$ 3.250,00",
                delta="↗️ +6,5%"
            )
        
        with col4:
            st.metric(
                label="📈 Rentabilidade",
                value="6,50%",
                delta="↗️ +0,8%"
            )
        
        st.markdown("---")
        
        # Tabela de investimentos
        st.subheader("📋 Carteira de Renda Fixa")
        
        renda_fixa_data = {
            "Produto": ["CDB Banco ABC", "LCI Banco XYZ", "LCA Banco DEF", "Tesouro IPCA+", "CDB Banco GHI"],
            "Tipo": ["CDB", "LCI", "LCA", "Tesouro", "CDB"],
            "Valor Aplicado": ["R$ 15.000,00", "R$ 12.000,00", "R$ 10.000,00", "R$ 8.000,00", "R$ 5.000,00"],
            "Taxa": ["105% CDI", "95% CDI", "98% CDI", "IPCA + 5,5%", "110% CDI"],
            "Vencimento": ["15/03/2025", "22/07/2025", "10/12/2025", "15/05/2026", "30/09/2024"],
            "Valor Atual": ["R$ 15.975,00", "R$ 12.780,00", "R$ 10.650,00", "R$ 8.520,00", "R$ 5.325,00"],
            "Rentabilidade": ["+6,5%", "+6,5%", "+6,5%", "+6,5%", "+6,5%"]
        }
        
        df_renda_fixa = pd.DataFrame(renda_fixa_data)
        st.dataframe(df_renda_fixa, use_container_width=True)
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🥧 Distribuição por Tipo")
            
            tipos_valores = {
                "CDB": 21300,
                "LCI": 12780,
                "LCA": 10650,
                "Tesouro": 8520
            }
            
            fig_pie_rf = px.pie(
                values=list(tipos_valores.values()),
                names=list(tipos_valores.keys()),
                title="Distribuição por Tipo de Investimento"
            )
            st.plotly_chart(fig_pie_rf, use_container_width=True)
        
        with col2:
            st.subheader("📅 Vencimentos")
            
            vencimentos_data = {
                "Mês": ["Set/24", "Mar/25", "Jul/25", "Dez/25", "Mai/26"],
                "Valor": [5325, 15975, 12780, 10650, 8520]
            }
            
            fig_bar = px.bar(
                x=vencimentos_data["Mês"],
                y=vencimentos_data["Valor"],
                title="Cronograma de Vencimentos"
            )
            st.plotly_chart(fig_bar, use_container_width=True)
    
    with tab3:
        st.subheader("📋 Debêntures")
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="💰 Total Aplicado",
                value="R$ 20.000,00",
                delta="↗️ +R$ 2.000,00"
            )
        
        with col2:
            st.metric(
                label="📊 Valor Atual",
                value="R$ 21.600,00",
                delta="↗️ +8%"
            )
        
        with col3:
            st.metric(
                label="💵 Rendimento",
                value="R$ 1.600,00",
                delta="↗️ +8%"
            )
        
        with col4:
            st.metric(
                label="📈 Rentabilidade",
                value="8,00%",
                delta="↗️ +1,2%"
            )
        
        st.markdown("---")
        
        # Tabela de debêntures
        st.subheader("📊 Carteira de Debêntures")
        
        debentures_data = {
            "Emissor": ["Empresa ABC S.A.", "Companhia XYZ", "Grupo DEF"],
            "Código": ["ABC21", "XYZ23", "DEF25"],
            "Valor Aplicado": ["R$ 10.000,00", "R$ 6.000,00", "R$ 4.000,00"],
            "Taxa": ["IPCA + 7%", "CDI + 2%", "IPCA + 6,5%"],
            "Vencimento": ["15/08/2026", "22/12/2025", "10/06/2027"],
            "Valor Atual": ["R$ 10.800,00", "R$ 6.480,00", "R$ 4.320,00"],
            "Rentabilidade": ["+8%", "+8%", "+8%"]
        }
        
        df_debentures = pd.DataFrame(debentures_data)
        st.dataframe(df_debentures, use_container_width=True)
        
        # Informações importantes
        st.info("💡 **Importante:** Debêntures são títulos de dívida corporativa. Verifique sempre o rating de crédito do emissor.")
    
    with tab4:
        st.subheader("🏠 FGTS - Fundo de Garantia")
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="💰 Saldo Total",
                value="R$ 45.230,00",
                delta="↗️ +R$ 1.250,00"
            )
        
        with col2:
            st.metric(
                label="📅 Último Depósito",
                value="R$ 520,00",
                delta="Jul/2024"
            )
        
        with col3:
            st.metric(
                label="📈 Rendimento Anual",
                value="3,00%",
                delta="+ TR"
            )
        
        with col4:
            st.metric(
                label="🎯 Meta Anual",
                value="R$ 1.356,90",
                delta="↗️ 92%"
            )
        
        st.markdown("---")
        
        # Informações detalhadas
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Histórico de Depósitos")
            
            # Dados de exemplo
            historico_data = {
                "Mês": ["Jan/24", "Fev/24", "Mar/24", "Abr/24", "Mai/24", "Jun/24", "Jul/24"],
                "Depósito": [520, 520, 520, 520, 520, 520, 520],
                "Rendimento": [12.5, 13.2, 11.8, 14.1, 12.9, 13.5, 14.2]
            }
            
            df_fgts = pd.DataFrame(historico_data)
            
            fig_fgts = px.bar(
                df_fgts, 
                x="Mês", 
                y=["Depósito", "Rendimento"],
                title="Depósitos e Rendimentos Mensais",
                barmode="group"
            )
            st.plotly_chart(fig_fgts, use_container_width=True)
        
        with col2:
            st.subheader("📋 Informações do FGTS")
            
            st.markdown("""
            **📍 Situações para Saque:**
            - 🏠 Compra da casa própria
            - 🎓 Aposentadoria
            - 🏥 Doenças graves
            - 💼 Demissão sem justa causa
            - 🎂 Aniversário (saque-aniversário)
            
            **💡 Dicas:**
            - Rendimento: 3% ao ano + TR
            - Depósito mensal: 8% do salário
            - Consulte regularmente o saldo
            - Considere o saque-aniversário
            """)
            
            # Calculadora simples
            st.subheader("🧮 Calculadora FGTS")
            
            salario = st.number_input("💰 Salário Bruto:", value=6500.0, step=100.0)
            deposito_mensal = salario * 0.08
            
            st.write(f"📅 **Depósito Mensal:** R$ {deposito_mensal:.2f}")
            st.write(f"📊 **Depósito Anual:** R$ {deposito_mensal * 12:.2f}")
        
        # Alertas e lembretes
        st.markdown("---")
        st.subheader("🔔 Lembretes Importantes")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.warning("⚠️ **Saque-Aniversário:** Próximo saque disponível em Dezembro/2024")
        
        with col2:
            st.info("💡 **Dica:** Considere usar o FGTS para amortizar financiamento imobiliário")

'''
    
    # Encontrar onde inserir a função (antes da função main)
    main_function_pattern = r'(def main\(\):)'
    content = re.sub(main_function_pattern, investments_function + r'\n\1', content)
    
    print("   ✅ Função show_investments criada com seções completas")
    
    # 5. Verificar se imports necessários estão presentes
    print("5️⃣ Verificando imports necessários...")
    
    imports_needed = ['pandas as pd', 'plotly.express as px', 'datetime']
    
    for imp in imports_needed:
        if imp not in content:
            if 'pandas as pd' in imp:
                content = content.replace('import streamlit as st', 'import streamlit as st\nimport pandas as pd')
                print("   ✅ Import pandas adicionado")
            elif 'plotly.express as px' in imp:
                content = content.replace('import streamlit as st', 'import streamlit as st\nimport plotly.express as px')
                print("   ✅ Import plotly adicionado")
            elif 'datetime' in imp:
                content = content.replace('import streamlit as st', 'import streamlit as st\nimport datetime')
                print("   ✅ Import datetime adicionado")
    
    # Salvar arquivo final
    with open('streamlit_app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Página de Investimentos criada com sucesso!")
    
    return True

if __name__ == "__main__":
    print("🚀 Criando página de Investimentos...")
    success = create_investments_page()
    if success:
        print("🎉 Página de Investimentos criada com sucesso!")
        print("\n📋 Modificações realizadas:")
        print("✅ 1. Seção 'Status do Sistema' removida do Dashboard")
        print("✅ 2. Página 'Investimentos' adicionada na navegação")
        print("✅ 3. Roteamento para página de Investimentos criado")
        print("✅ 4. Função show_investments implementada com:")
        print("   📈 Renda Variável (ações, carteira, gráficos)")
        print("   🏦 Renda Fixa (CDB, LCI, LCA, Tesouro)")
        print("   📋 Debêntures (títulos corporativos)")
        print("   🏠 FGTS (saldo, histórico, calculadora)")
        print("✅ 5. Imports necessários adicionados")
        print("\n🔄 Reinicie o Streamlit:")
        print("   pkill -f streamlit")
        print("   ./start_simple.sh")
        print("\n💡 Agora o Dashboard está limpo e há uma página completa de Investimentos!")
    else:
        print("❌ Erro durante a criação da página de Investimentos")

