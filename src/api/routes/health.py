"""
Health Check Routes for Finance App API.
"""

import time
import psutil
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any

from src.models import DatabaseManager
from src.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: float
    version: str
    environment: str
    uptime: float
    services: Dict[str, Any]
    system: Dict[str, Any]


class ServiceStatus(BaseModel):
    """Service status model."""
    status: str
    response_time: float
    details: Dict[str, Any] = {}


@router.get("/", response_model=HealthResponse)
@router.get("/check", response_model=HealthResponse)
async def health_check():
    """
    Comprehensive health check endpoint.
    
    Returns system status, service availability, and performance metrics.
    """
    start_time = time.time()
    
    # Check database
    db_start = time.time()
    db_status = "healthy" if DatabaseManager.check_connection() else "unhealthy"
    db_response_time = time.time() - db_start
    
    # Check Redis
    redis_start = time.time()
    redis_status = "healthy" if DatabaseManager.check_redis_connection() else "unhealthy"
    redis_response_time = time.time() - redis_start
    
    # Check Ollama (if configured)
    ollama_status = "unknown"
    ollama_response_time = 0
    ollama_details = {}
    
    if settings.OLLAMA_HOST:
        try:
            import httpx
            ollama_start = time.time()
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{settings.OLLAMA_HOST}/api/tags")
                if response.status_code == 200:
                    ollama_status = "healthy"
                    models = response.json().get("models", [])
                    ollama_details = {
                        "models_available": len(models),
                        "default_model": settings.OLLAMA_DEFAULT_MODEL,
                        "models": [model.get("name") for model in models[:5]]  # First 5 models
                    }
                else:
                    ollama_status = "unhealthy"
                    ollama_details = {"error": f"HTTP {response.status_code}"}
            
            ollama_response_time = time.time() - ollama_start
            
        except Exception as e:
            ollama_status = "unhealthy"
            ollama_response_time = time.time() - ollama_start
            ollama_details = {"error": str(e)}
    
    # System metrics
    system_info = {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
    }
    
    # Overall status
    overall_status = "healthy"
    if db_status != "healthy" or redis_status != "healthy":
        overall_status = "degraded"
    if db_status != "healthy" and redis_status != "healthy":
        overall_status = "unhealthy"
    
    # Calculate total response time
    total_response_time = time.time() - start_time
    
    return HealthResponse(
        status=overall_status,
        timestamp=time.time(),
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        uptime=total_response_time,
        services={
            "database": {
                "status": db_status,
                "response_time": db_response_time,
                "details": {
                    "url": settings.DATABASE_URL.split("@")[1] if "@" in settings.DATABASE_URL else "hidden"
                }
            },
            "redis": {
                "status": redis_status,
                "response_time": redis_response_time,
                "details": {
                    "url": f"{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
                }
            },
            "ollama": {
                "status": ollama_status,
                "response_time": ollama_response_time,
                "details": ollama_details
            }
        },
        system=system_info
    )


@router.get("/database")
async def database_health():
    """Database-specific health check."""
    start_time = time.time()
    
    try:
        # Test connection
        is_connected = DatabaseManager.check_connection()
        
        # Get database stats
        stats = DatabaseManager.get_db_stats() if is_connected else []
        
        response_time = time.time() - start_time
        
        return {
            "status": "healthy" if is_connected else "unhealthy",
            "response_time": response_time,
            "connection": is_connected,
            "stats": stats[:10],  # Limit to first 10 tables
            "total_tables": len(stats)
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "response_time": time.time() - start_time,
            "error": str(e)
        }


@router.get("/redis")
async def redis_health():
    """Redis-specific health check."""
    start_time = time.time()
    
    try:
        from src.models import get_redis
        redis_client = get_redis()
        
        # Test connection
        redis_client.ping()
        
        # Get Redis info
        info = redis_client.info()
        
        response_time = time.time() - start_time
        
        return {
            "status": "healthy",
            "response_time": response_time,
            "info": {
                "version": info.get("redis_version"),
                "uptime": info.get("uptime_in_seconds"),
                "connected_clients": info.get("connected_clients"),
                "used_memory": info.get("used_memory_human"),
                "keyspace": {k: v for k, v in info.items() if k.startswith("db")}
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "response_time": time.time() - start_time,
            "error": str(e)
        }


@router.get("/ollama")
async def ollama_health():
    """Ollama-specific health check."""
    start_time = time.time()
    
    try:
        import httpx
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Check if Ollama is running
            response = await client.get(f"{settings.OLLAMA_HOST}/api/tags")
            
            if response.status_code == 200:
                models_data = response.json()
                models = models_data.get("models", [])
                
                # Test default model
                model_status = {}
                if settings.OLLAMA_DEFAULT_MODEL:
                    try:
                        test_response = await client.post(
                            f"{settings.OLLAMA_HOST}/api/generate",
                            json={
                                "model": settings.OLLAMA_DEFAULT_MODEL,
                                "prompt": "Test",
                                "stream": False
                            },
                            timeout=5.0
                        )
                        model_status[settings.OLLAMA_DEFAULT_MODEL] = "available" if test_response.status_code == 200 else "error"
                    except Exception:
                        model_status[settings.OLLAMA_DEFAULT_MODEL] = "timeout"
                
                response_time = time.time() - start_time
                
                return {
                    "status": "healthy",
                    "response_time": response_time,
                    "host": settings.OLLAMA_HOST,
                    "models": {
                        "total": len(models),
                        "available": [model.get("name") for model in models],
                        "default": settings.OLLAMA_DEFAULT_MODEL,
                        "status": model_status
                    }
                }
            else:
                return {
                    "status": "unhealthy",
                    "response_time": time.time() - start_time,
                    "error": f"HTTP {response.status_code}"
                }
                
    except Exception as e:
        return {
            "status": "unhealthy",
            "response_time": time.time() - start_time,
            "error": str(e)
        }


@router.get("/system")
async def system_health():
    """System resource health check."""
    try:
        # CPU information
        cpu_info = {
            "percent": psutil.cpu_percent(interval=1),
            "count": psutil.cpu_count(),
            "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        }
        
        # Memory information
        memory = psutil.virtual_memory()
        memory_info = {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used,
            "free": memory.free
        }
        
        # Disk information
        disk = psutil.disk_usage('/')
        disk_info = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": (disk.used / disk.total) * 100
        }
        
        # Network information
        network = psutil.net_io_counters()
        network_info = {
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv,
            "packets_sent": network.packets_sent,
            "packets_recv": network.packets_recv
        }
        
        # Load average (Unix only)
        load_avg = None
        if hasattr(psutil, 'getloadavg'):
            load_avg = psutil.getloadavg()
        
        return {
            "status": "healthy",
            "cpu": cpu_info,
            "memory": memory_info,
            "disk": disk_info,
            "network": network_info,
            "load_average": load_avg,
            "boot_time": psutil.boot_time()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

