"""
Finance App Models Package.

Este módulo contém todos os modelos de dados da aplicação financeira,
otimizados para análise com LLM e performance em PostgreSQL.
"""

from .database import (
    Base, 
    engine, 
    async_engine,
    SessionLocal, 
    AsyncSessionLocal,
    get_db, 
    get_async_db,
    get_redis,
    DatabaseManager,
    CacheManager,
    metadata
)

from .transactions import (
    Transaction,
    TransactionType,
    TransactionStatus,
    ImportBatch
)

from .categories import (
    Category,
    CategoryType,
    CategoryRule
)

# Export all models for easy import
__all__ = [
    # Database utilities
    "Base",
    "engine", 
    "async_engine",
    "SessionLocal",
    "AsyncSessionLocal", 
    "get_db",
    "get_async_db",
    "get_redis",
    "DatabaseManager",
    "CacheManager",
    "metadata",
    
    # Transaction models
    "Transaction",
    "TransactionType", 
    "TransactionStatus",
    "ImportBatch",
    
    # Category models
    "Category",
    "CategoryType",
    "CategoryRule",
]

# Version info
__version__ = "1.0.0"

