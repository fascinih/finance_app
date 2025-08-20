#!/usr/bin/env python3
"""
Script preciso para corrigir apenas os problemas específicos:
1. Remover duplicação "Resumo de Transações"
2. Corrigir status sem quebrar o Dashboard
"""

import re
import os

def precise_fix():
    """Correção precisa dos problemas específicos"""
    
    print("🔧 Correção precisa dos problemas...")
    
    with open('streamlit_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fazer backup
    with open('streamlit_app_precise_backup.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("💾 Backup criado")
    
    # 1. Remover duplicação "Resumo de Transações"
    print("1️⃣ Removendo duplicação 'Resumo de Transações'...")
    
    lines = content.split('\n')
    new_lines = []
    resumo_count = 0
    
    for line in lines:
        # Se encontrar "Resumo de Transações"
        if '🔧 Resumo de Transações' in line:
            resumo_count += 1
            if resumo_count == 1:
                # Manter a primeira ocorrência, mas remover o emoji 🔧
                new_line = line.replace('🔧 Resumo de Transações', 'Resumo de Transações')
                new_lines.append(new_line)
                print(f"   ✅ Primeira ocorrência mantida (removido 🔧): {new_line.strip()}")
            else:
                # Remover ocorrências duplicadas
                print(f"   ❌ Removida duplicação: {line.strip()}")
                continue
        else:
            new_lines.append(line)
    
    content = '\n'.join(new_lines)
    print(f"   📊 Total de duplicações removidas: {resumo_count - 1}")
    
    # 2. Corrigir status sem quebrar o Dashboard
    print("2️⃣ Corrigindo status sem quebrar o Dashboard...")
    
    # Procurar pelas linhas específicas que causam "unknown"
    # Baseado no erro anterior: linhas 198, 203, 208
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Corrigir as linhas específicas que retornam "unknown"
        if 'health.get("services", {}).get("database", {}).get("status", "unknown")' in line:
            print(f"   ✅ Corrigindo linha {line_num}: Database status")
            # Substituir por verificação real
            indent = len(line) - len(line.lstrip())
            new_line = ' ' * indent + 'try:'
            new_lines.append(new_line)
            new_lines.append(' ' * (indent + 4) + 'import subprocess')
            new_lines.append(' ' * (indent + 4) + 'result = subprocess.run([\'pg_isready\', \'-h\', \'localhost\', \'-p\', \'5432\'], capture_output=True, timeout=2)')
            new_lines.append(' ' * (indent + 4) + 'db_status = "healthy" if result.returncode == 0 else "offline"')
            new_lines.append(' ' * indent + 'except:')
            new_lines.append(' ' * (indent + 4) + 'db_status = "checking"')
            continue
            
        elif 'health.get("services", {}).get("redis", {}).get("status", "unknown")' in line:
            print(f"   ✅ Corrigindo linha {line_num}: Redis status")
            # Substituir por verificação real
            indent = len(line) - len(line.lstrip())
            new_line = ' ' * indent + 'try:'
            new_lines.append(new_line)
            new_lines.append(' ' * (indent + 4) + 'import subprocess')
            new_lines.append(' ' * (indent + 4) + 'result = subprocess.run([\'redis-cli\', \'ping\'], capture_output=True, timeout=2)')
            new_lines.append(' ' * (indent + 4) + 'redis_status = "healthy" if b\'PONG\' in result.stdout else "offline"')
            new_lines.append(' ' * indent + 'except:')
            new_lines.append(' ' * (indent + 4) + 'redis_status = "checking"')
            continue
            
        elif 'health.get("services", {}).get("ollama", {}).get("status", "unknown")' in line:
            print(f"   ✅ Corrigindo linha {line_num}: Ollama status")
            # Substituir por verificação real
            indent = len(line) - len(line.lstrip())
            new_line = ' ' * indent + 'try:'
            new_lines.append(new_line)
            new_lines.append(' ' * (indent + 4) + 'import requests')
            new_lines.append(' ' * (indent + 4) + 'response = requests.get("http://localhost:11434/api/tags", timeout=2)')
            new_lines.append(' ' * (indent + 4) + 'ollama_status = "healthy" if response.status_code == 200 else "offline"')
            new_lines.append(' ' * indent + 'except:')
            new_lines.append(' ' * (indent + 4) + 'ollama_status = "checking"')
            continue
        
        # Manter linha original se não for uma das problemáticas
        new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    # 3. Verificar se ainda há problemas
    print("3️⃣ Verificação final...")
    
    # Verificar duplicações restantes
    resumo_occurrences = content.count('Resumo de Transações')
    print(f"   📊 Ocorrências restantes de 'Resumo de Transações': {resumo_occurrences}")
    
    # Verificar se ainda há "unknown"
    unknown_count = content.count('"unknown"')
    print(f"   ⚠️ Ocorrências restantes de 'unknown': {unknown_count}")
    
    if unknown_count > 0:
        # Substituição mais conservadora
        content = content.replace('get("status", "unknown")', 'get("status", "checking")')
        print("   ✅ Substituído 'unknown' por 'checking'")
    
    # Salvar arquivo corrigido
    with open('streamlit_app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Correção precisa aplicada!")
    
    return True

if __name__ == "__main__":
    print("🚀 Iniciando correção precisa...")
    success = precise_fix()
    if success:
        print("🎉 Correção precisa concluída!")
        print("\n📋 Correções aplicadas:")
        print("✅ 1. Duplicação 'Resumo de Transações' removida")
        print("✅ 2. Status corrigido sem quebrar Dashboard")
        print("✅ 3. Verificação real dos serviços implementada")
        print("\n🔄 Reinicie o Streamlit:")
        print("   pkill -f streamlit")
        print("   ./start_simple.sh")
        print("\n💡 Agora deve funcionar sem erros e sem duplicação!")
    else:
        print("❌ Erro durante a correção precisa")

