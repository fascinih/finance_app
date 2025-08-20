"""
Database configuration and connection management for Finance App.
Otimizado para PostgreSQL com SQLAlchemy 2.0+
"""

import os
from typing import AsyncGenerator, Optional
from sqlalchemy import create_engine, MetaData, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import QueuePool
import redis
from loguru import logger

# Database URL configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://finance_user:finance_password@localhost:5432/finance_app")
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Database engine configuration optimized for SSD
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=os.getenv("DEBUG", "false").lower() == "true",
    connect_args={
        "options": "-c timezone=America/Sao_Paulo",
        "application_name": "finance_app",
    }
)

# Async engine for high-performance operations
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=os.getenv("DEBUG", "false").lower() == "true",
)

# Session factories
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Redis connection
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Metadata for migrations
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    metadata = metadata


# Database event listeners for optimization
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set PostgreSQL-specific optimizations on connection."""
    if "postgresql" in str(dbapi_connection):
        with dbapi_connection.cursor() as cursor:
            # Set timezone
            cursor.execute("SET timezone = 'America/Sao_Paulo'")
            # Optimize for SSD
            cursor.execute("SET random_page_cost = 1.1")
            cursor.execute("SET seq_page_cost = 1.0")
            # Performance settings
            cursor.execute("SET work_mem = '64MB'")
            cursor.execute("SET maintenance_work_mem = '256MB'")


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Async database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


def get_redis():
    """Get Redis client."""
    return redis_client


class DatabaseManager:
    """Database management utilities."""
    
    @staticmethod
    def create_tables():
        """Create all tables."""
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    @staticmethod
    def drop_tables():
        """Drop all tables."""
        try:
            Base.metadata.drop_all(bind=engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Error dropping tables: {e}")
            raise
    
    @staticmethod
    def check_connection() -> bool:
        """Check database connection."""
        try:
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            logger.info("Database connection successful")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    @staticmethod
    def check_redis_connection() -> bool:
        """Check Redis connection."""
        try:
            redis_client.ping()
            logger.info("Redis connection successful")
            return True
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            return False
    
    @staticmethod
    def get_db_stats():
        """Get database statistics."""
        try:
            with engine.connect() as conn:
                result = conn.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        n_tup_ins as inserts,
                        n_tup_upd as updates,
                        n_tup_del as deletes,
                        n_live_tup as live_tuples,
                        n_dead_tup as dead_tuples
                    FROM pg_stat_user_tables
                    ORDER BY n_live_tup DESC;
                """)
                return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return []


# Cache utilities
class CacheManager:
    """Redis cache management utilities."""
    
    @staticmethod
    def set(key: str, value: str, ttl: int = 3600):
        """Set cache value with TTL."""
        try:
            redis_client.setex(key, ttl, value)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    @staticmethod
    def get(key: str) -> Optional[str]:
        """Get cache value."""
        try:
            return redis_client.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    @staticmethod
    def delete(key: str):
        """Delete cache key."""
        try:
            redis_client.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
    
    @staticmethod
    def clear_pattern(pattern: str):
        """Clear cache keys matching pattern."""
        try:
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")


# Initialize database on import
if __name__ == "__main__":
    # Test connections
    db_manager = DatabaseManager()
    print(f"Database connection: {db_manager.check_connection()}")
    print(f"Redis connection: {db_manager.check_redis_connection()}")

