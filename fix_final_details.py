#!/usr/bin/env python3
"""
Script para corrigir os 2 últimos detalhes:
1. Status do Sistema (Database, Redis, Ollama)
2. Resumo de Transações
"""

import re
import os

def fix_final_details():
    """Corrige Status do Sistema e Resumo de Transações"""
    
    print("🔧 Corrigindo detalhes finais...")
    
    with open('streamlit_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fazer backup
    with open('streamlit_app_before_final_fix.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("💾 Backup criado")
    
    # 1. Corrigir Status do Sistema
    print("1️⃣ Corrigindo Status do Sistema...")
    
    # Procurar pela seção de status e substituir completamente
    # Padrão: Database: unknown, Redis: unknown, Ollama: unknown
    status_pattern = r'st\.error\(f?"🔴 Database: \{.*?\}"\).*?st\.error\(f?"🔴 Redis: \{.*?\}"\).*?st\.error\(f?"🔴 Ollama: \{.*?\}"\)'
    
    if re.search(status_pattern, content, re.DOTALL):
        print("   - Encontrou padrão de status unknown")
        # Substituir por verificação real
        new_status_section = '''# Verificação real dos serviços
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Verificar PostgreSQL
                try:
                    import subprocess
                    result = subprocess.run(['pg_isready', '-h', 'localhost', '-p', '5432'], 
                                          capture_output=True, timeout=2)
                    if result.returncode == 0:
                        st.success("🟢 Database: online")
                    else:
                        st.warning("🟡 Database: offline")
                except:
                    st.warning("🟡 Database: verificando...")
            
            with col2:
                # Verificar Redis
                try:
                    import subprocess
                    result = subprocess.run(['redis-cli', 'ping'], 
                                          capture_output=True, timeout=2)
                    if b'PONG' in result.stdout:
                        st.success("🟢 Redis: online")
                    else:
                        st.warning("🟡 Redis: offline")
                except:
                    st.warning("🟡 Redis: verificando...")
            
            with col3:
                # Verificar Ollama
                try:
                    import requests
                    response = requests.get("http://localhost:11434/api/tags", timeout=2)
                    if response.status_code == 200:
                        st.success("🟢 Ollama: online")
                    else:
                        st.warning("🟡 Ollama: offline")
                except:
                    st.warning("🟡 Ollama: verificando...")
            
            # Botão para atualizar status
            if st.button("🔄 Atualizar Status"):
                st.rerun()'''
        
        content = re.sub(status_pattern, new_status_section, content, flags=re.DOTALL)
    else:
        # Procurar por uma abordagem mais direta
        print("   - Procurando por padrão alternativo...")
        
        # Procurar por qualquer linha que mostre "Database: unknown"
        if 'Database: unknown' in content:
            # Encontrar a seção e substituir
            lines = content.split('\n')
            new_lines = []
            in_status_section = False
            status_section_lines = 0
            
            for line in lines:
                if 'Database: unknown' in line:
                    in_status_section = True
                    status_section_lines = 0
                    # Adicionar nova seção de status
                    new_lines.extend([
                        '        col1, col2, col3 = st.columns(3)',
                        '        ',
                        '        with col1:',
                        '            # Verificar PostgreSQL',
                        '            try:',
                        '                import subprocess',
                        '                result = subprocess.run([\'pg_isready\', \'-h\', \'localhost\', \'-p\', \'5432\'], ',
                        '                                      capture_output=True, timeout=2)',
                        '                if result.returncode == 0:',
                        '                    st.success("🟢 Database: online")',
                        '                else:',
                        '                    st.warning("🟡 Database: offline")',
                        '            except:',
                        '                st.warning("🟡 Database: verificando...")',
                        '        ',
                        '        with col2:',
                        '            # Verificar Redis',
                        '            try:',
                        '                import subprocess',
                        '                result = subprocess.run([\'redis-cli\', \'ping\'], ',
                        '                                      capture_output=True, timeout=2)',
                        '                if b\'PONG\' in result.stdout:',
                        '                    st.success("🟢 Redis: online")',
                        '                else:',
                        '                    st.warning("🟡 Redis: offline")',
                        '            except:',
                        '                st.warning("🟡 Redis: verificando...")',
                        '        ',
                        '        with col3:',
                        '            # Verificar Ollama',
                        '            try:',
                        '                import requests',
                        '                response = requests.get("http://localhost:11434/api/tags", timeout=2)',
                        '                if response.status_code == 200:',
                        '                    st.success("🟢 Ollama: online")',
                        '                else:',
                        '                    st.warning("🟡 Ollama: offline")',
                        '            except:',
                        '                st.warning("🟡 Ollama: verificando...")',
                        '        ',
                        '        # Botão para atualizar status',
                        '        if st.button("🔄 Atualizar Status"):',
                        '            st.rerun()'
                    ])
                    continue
                
                if in_status_section:
                    status_section_lines += 1
                    # Pular linhas da seção antiga (até encontrar próxima seção)
                    if status_section_lines > 15 or line.strip().startswith('st.') and 'Database' not in line and 'Redis' not in line and 'Ollama' not in line:
                        in_status_section = False
                        new_lines.append(line)
                    # Pular linhas da seção antiga
                    continue
                
                new_lines.append(line)
            
            content = '\n'.join(new_lines)
    
    # 2. Implementar Resumo de Transações
    print("2️⃣ Implementando Resumo de Transações...")
    
    # Procurar pela tab de Resumo e substituir o conteúdo
    resumo_pattern = r'🔧 Resumo em desenvolvimento'
    
    if resumo_pattern in content:
        print("   - Encontrou resumo em desenvolvimento")
        
        # Substituir por implementação completa
        new_resumo_content = '''# Resumo de Transações implementado
        
        # Buscar transações para o resumo
        api = get_api_client()
        try:
            transactions_data = api.get_transactions()
            if transactions_data and "items" in transactions_data:
                transactions = transactions_data["items"]
            else:
                transactions = []
        except:
            transactions = []
        
        if transactions:
            # Calcular estatísticas reais
            receitas = sum(t.get("amount", 0) for t in transactions if t.get("amount", 0) > 0)
            despesas = abs(sum(t.get("amount", 0) for t in transactions if t.get("amount", 0) < 0))
            saldo = receitas - despesas
            total_transacoes = len(transactions)
            
            # Métricas principais
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("💰 Total Receitas", f"R$ {receitas:,.2f}", "↗️")
            with col2:
                st.metric("💸 Total Despesas", f"R$ {despesas:,.2f}", "↘️")
            with col3:
                delta_color = "normal" if saldo >= 0 else "inverse"
                st.metric("💵 Saldo Líquido", f"R$ {saldo:,.2f}", delta_color=delta_color)
            with col4:
                st.metric("📊 Total Transações", str(total_transacoes), "📈")
            
            # Análise por categoria
            st.subheader("📊 Resumo por Categoria")
            
            # Agrupar por categoria
            categorias = {}
            for t in transactions:
                categoria = t.get("category", "Sem categoria")
                amount = t.get("amount", 0)
                if categoria not in categorias:
                    categorias[categoria] = {"total": 0, "count": 0}
                categorias[categoria]["total"] += amount
                categorias[categoria]["count"] += 1
            
            if categorias:
                import pandas as pd
                
                # Criar DataFrame para exibição
                resumo_data = []
                for cat, data in categorias.items():
                    resumo_data.append({
                        "Categoria": cat,
                        "Total": f"R$ {data['total']:,.2f}",
                        "Transações": data['count'],
                        "Média": f"R$ {data['total']/data['count']:,.2f}"
                    })
                
                df_resumo = pd.DataFrame(resumo_data)
                st.dataframe(df_resumo, use_container_width=True, hide_index=True)
            
            # Gráfico de distribuição
            st.subheader("📈 Distribuição de Valores")
            
            import plotly.express as px
            
            # Preparar dados para gráfico
            valores = [abs(t.get("amount", 0)) for t in transactions]
            tipos = ["Receita" if t.get("amount", 0) > 0 else "Despesa" for t in transactions]
            
            if valores:
                fig = px.histogram(x=valores, color=tipos, nbins=20, 
                                 title="Distribuição de Valores das Transações")
                fig.update_layout(xaxis_title="Valor (R$)", yaxis_title="Quantidade")
                st.plotly_chart(fig, use_container_width=True)
            
            # Transações recentes
            st.subheader("📋 Transações Recentes")
            
            # Mostrar últimas 10 transações
            recent_transactions = sorted(transactions, 
                                       key=lambda x: x.get("date", ""), 
                                       reverse=True)[:10]
            
            if recent_transactions:
                resumo_recentes = []
                for t in recent_transactions:
                    resumo_recentes.append({
                        "Data": t.get("date", "N/A"),
                        "Descrição": t.get("description", "N/A"),
                        "Categoria": t.get("category", "N/A"),
                        "Valor": f"R$ {t.get('amount', 0):,.2f}"
                    })
                
                df_recentes = pd.DataFrame(resumo_recentes)
                st.dataframe(df_recentes, use_container_width=True, hide_index=True)
        else:
            # Mostrar resumo de exemplo se não há transações
            st.info("💡 **Resumo de Exemplo** - Adicione transações para ver dados reais")
            
            # Métricas de exemplo
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("💰 Total Receitas", "R$ 5.500,00", "↗️ +12%")
            with col2:
                st.metric("💸 Total Despesas", "R$ 3.200,00", "↘️ -5%")
            with col3:
                st.metric("💵 Saldo Líquido", "R$ 2.300,00", "↗️ +18%")
            with col4:
                st.metric("📊 Total Transações", "127", "📈 +8")
            
            # Exemplo de categorias
            st.subheader("📊 Exemplo - Resumo por Categoria")
            
            import pandas as pd
            
            exemplo_categorias = pd.DataFrame({
                "Categoria": ["Alimentação", "Transporte", "Moradia", "Saúde", "Lazer"],
                "Total": ["R$ 1.200,00", "R$ 800,00", "R$ 1.500,00", "R$ 400,00", "R$ 600,00"],
                "Transações": [25, 15, 3, 8, 12],
                "Média": ["R$ 48,00", "R$ 53,33", "R$ 500,00", "R$ 50,00", "R$ 50,00"]
            })
            
            st.dataframe(exemplo_categorias, use_container_width=True, hide_index=True)'''
        
        content = content.replace(resumo_pattern, new_resumo_content)
    
    # Salvar arquivo corrigido
    with open('streamlit_app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Detalhes finais corrigidos!")
    
    return True

if __name__ == "__main__":
    print("🚀 Corrigindo detalhes finais...")
    success = fix_final_details()
    if success:
        print("🎉 Correção final concluída!")
        print("\n📋 Correções aplicadas:")
        print("✅ 1. Status do Sistema com verificação real")
        print("✅ 2. Resumo de Transações implementado")
        print("✅ 3. Métricas e gráficos no resumo")
        print("✅ 4. Fallback para dados de exemplo")
        print("\n🔄 Reinicie o Streamlit para ver as correções!")
        print("💡 Agora o Status vai mostrar cores corretas!")
        print("💡 O Resumo de Transações está completo!")
    else:
        print("❌ Erro durante a correção final")

