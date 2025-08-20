#!/bin/bash

# Script para instalar dependências que faltam
echo "🔧 Instalando dependências que faltam..."

# Verificar se venv existe
if [ ! -d "venv" ]; then
    echo "❌ Ambiente virtual não encontrado"
    exit 1
fi

# Ativar ambiente virtual
source venv/bin/activate

echo "📦 Instalando módulos que faltam..."

# Instalar dependências que faltam uma por uma
pip install httpx
pip install aiofiles
pip install python-multipart
pip install python-jose[cryptography]
pip install passlib[bcrypt]
pip install redis
pip install alembic
pip install pydantic-settings
pip install rich
pip install loguru
pip install click
pip install psutil
pip install cryptography

echo "✅ Dependências instaladas!"

# Verificar instalações importantes
echo "🔍 Verificando instalações..."
python -c "import httpx; print('✅ httpx instalado')" 2>/dev/null || echo "❌ httpx falhou"
python -c "import aiofiles; print('✅ aiofiles instalado')" 2>/dev/null || echo "❌ aiofiles falhou"
python -c "import redis; print('✅ redis instalado')" 2>/dev/null || echo "❌ redis falhou"
python -c "import cryptography; print('✅ cryptography instalado')" 2>/dev/null || echo "❌ cryptography falhou"

echo ""
echo "🚀 Agora execute: ./start_simple.sh"

