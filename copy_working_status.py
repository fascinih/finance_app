#!/usr/bin/env python3
"""
Script para copiar a lógica de status que funciona em Configurações para o Dashboard
"""

import re
import os

def copy_working_status():
    """Copia a lógica de status que funciona"""
    
    print("🔧 Copiando lógica de status que funciona...")
    
    with open('streamlit_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fazer backup
    with open('streamlit_app_status_backup.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("💾 Backup criado")
    
    # 1. Encontrar a lógica que funciona (das Configurações)
    print("1️⃣ Extraindo lógica que funciona das Configurações...")
    
    working_logic = '''        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Verificar status da API
            try:
                response = requests.get("http://localhost:8000/health", timeout=3)
                if response.status_code == 200:
                    st.success("🟢 API: Conectada")
                else:
                    st.error("🔴 API: Erro")
            except:
                st.error("🔴 API: Offline")
        
        with col2:
            # Verificar Database
            try:
                import subprocess
                result = subprocess.run(['pg_isready', '-h', 'localhost', '-p', '5432'], 
                                      capture_output=True, timeout=2)
                if result.returncode == 0:
                    st.success("🟢 Database: Conectado")
                else:
                    st.error("🔴 Database: Offline")
            except:
                st.error("🔴 Database: Erro")
        
        with col3:
            # Status do Ollama
            try:
                ollama_response = requests.get("http://localhost:11434/api/tags", timeout=3)
                if ollama_response.status_code == 200:
                    st.success("🟢 Ollama: Funcionando")
                else:
                    st.warning("🟡 Ollama: Problema")
            except:
                st.error("🔴 Ollama: Offline")
        
        if st.button("🔄 Atualizar Status"):
            st.rerun()'''
    
    # 2. Encontrar onde está a lógica problemática no Dashboard
    print("2️⃣ Procurando lógica problemática no Dashboard...")
    
    # Procurar pelas linhas que usam health.get()
    lines = content.split('\n')
    new_lines = []
    in_status_section = False
    status_section_start = -1
    
    for i, line in enumerate(lines):
        # Detectar início da seção de status problemática
        if 'health.get("services", {}).get("database"' in line:
            in_status_section = True
            status_section_start = i
            print(f"   ✅ Encontrou seção problemática na linha {i+1}")
            
            # Encontrar a indentação correta
            indent = len(line) - len(line.lstrip())
            
            # Adicionar a lógica que funciona com a indentação correta
            working_lines = working_logic.split('\n')
            for working_line in working_lines:
                if working_line.strip():  # Não adicionar linhas vazias desnecessárias
                    new_lines.append(' ' * indent + working_line.lstrip())
                else:
                    new_lines.append('')
            
            # Pular as próximas linhas da seção problemática
            skip_count = 0
            for j in range(i, min(i+20, len(lines))):
                if ('health.get(' in lines[j] or 
                    'db_status' in lines[j] or 
                    'redis_status' in lines[j] or 
                    'ollama_status' in lines[j]):
                    skip_count += 1
                else:
                    break
            
            # Pular as linhas problemáticas
            for _ in range(skip_count):
                if i + 1 < len(lines):
                    i += 1
            
            in_status_section = False
            continue
        
        # Se estamos pulando a seção problemática, não adicionar a linha
        if in_status_section:
            continue
        
        new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    # 3. Verificar se ainda há referências problemáticas
    print("3️⃣ Verificando se ainda há referências problemáticas...")
    
    problematic_patterns = [
        'health.get("services"',
        'db_status = health',
        'redis_status = health',
        'ollama_status = health'
    ]
    
    for pattern in problematic_patterns:
        if pattern in content:
            print(f"   ⚠️ Ainda encontrado: {pattern}")
            # Remover linhas que contêm esses padrões
            lines = content.split('\n')
            new_lines = [line for line in lines if pattern not in line]
            content = '\n'.join(new_lines)
            print(f"   ✅ Removido: {pattern}")
    
    # 4. Garantir que requests está importado
    print("4️⃣ Verificando imports...")
    
    if 'import requests' not in content:
        content = content.replace('import streamlit as st', 'import streamlit as st\nimport requests')
        print("   ✅ Import requests adicionado")
    
    # Salvar arquivo corrigido
    with open('streamlit_app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Lógica de status copiada com sucesso!")
    
    return True

if __name__ == "__main__":
    print("🚀 Copiando lógica de status que funciona...")
    success = copy_working_status()
    if success:
        print("🎉 Cópia da lógica concluída!")
        print("\n📋 O que foi feito:")
        print("✅ 1. Extraída lógica que funciona das Configurações")
        print("✅ 2. Substituída lógica problemática do Dashboard")
        print("✅ 3. Removidas referências a health.get()")
        print("✅ 4. Verificados imports necessários")
        print("\n🔄 Reinicie o Streamlit:")
        print("   pkill -f streamlit")
        print("   ./start_simple.sh")
        print("\n💡 Agora o Dashboard deve mostrar o mesmo status das Configurações!")
    else:
        print("❌ Erro durante a cópia da lógica")

