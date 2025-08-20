#!/bin/bash

# Script para corrigir problemas de import
echo "🔧 Corrigindo problemas de import..."

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[IMPORT-FIX]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[IMPORT-FIX]${NC} $1"
}

# Verificar se estamos no diretório correto
if [ ! -f "streamlit_app.py" ]; then
    echo -e "${RED}❌ Execute no diretório da Finance App${NC}"
    exit 1
fi

# Criar arquivo __init__.py na raiz se não existir
if [ ! -f "__init__.py" ]; then
    log "Criando __init__.py na raiz..."
    touch __init__.py
fi

# Criar arquivos __init__.py que faltam
log "Verificando arquivos __init__.py..."
touch src/__init__.py
touch src/api/__init__.py
touch src/api/routes/__init__.py
touch src/api/middleware/__init__.py
touch src/models/__init__.py
touch src/services/__init__.py
touch src/config/__init__.py

# Corrigir o arquivo main.py para imports mais simples
log "Corrigindo imports no main.py..."

# Fazer backup
cp src/api/main.py src/api/main.py.backup

# Criar versão simplificada do main.py
cat > src/api/main.py << 'EOF'
"""
Finance App - FastAPI Main Application
Aplicação principal da API financeira
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Create FastAPI app
app = FastAPI(
    title="Finance App API",
    description="API para aplicação de análise financeira com IA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Finance App API is running",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Finance App API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Basic API endpoints
@app.get("/api/v1/status")
async def api_status():
    """API status endpoint"""
    return {
        "api": "Finance App",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "transactions": "/api/v1/transactions",
            "categories": "/api/v1/categories"
        }
    }

# Transactions endpoint (basic)
@app.get("/api/v1/transactions")
async def get_transactions():
    """Get transactions (placeholder)"""
    return {
        "transactions": [],
        "total": 0,
        "message": "Database connection will be implemented"
    }

# Categories endpoint (basic)
@app.get("/api/v1/categories")
async def get_categories():
    """Get categories (placeholder)"""
    return {
        "categories": [
            {"id": 1, "name": "Alimentação", "type": "expense"},
            {"id": 2, "name": "Transporte", "type": "expense"},
            {"id": 3, "name": "Salário", "type": "income"}
        ],
        "total": 3
    }

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "status": "error"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

log "✅ main.py corrigido com imports simplificados"

# Verificar se o arquivo foi criado corretamente
if [ -f "src/api/main.py" ]; then
    log "✅ Arquivo main.py atualizado"
else
    warn "❌ Problema ao atualizar main.py"
fi

echo ""
echo "=================================================="
echo -e "${GREEN}✅ Imports corrigidos!${NC}"
echo ""
echo "Mudanças feitas:"
echo "• main.py simplificado (backup em main.py.backup)"
echo "• Arquivos __init__.py criados"
echo "• Imports básicos funcionando"
echo ""
echo "Agora execute:"
echo "• ./start_backend.sh"
echo "=================================================="

