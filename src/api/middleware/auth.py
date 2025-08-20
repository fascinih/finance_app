"""
Authentication Middleware for Finance App API.
"""

import jwt
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from src.config import settings


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT authentication."""
    
    # Public endpoints that don't require authentication
    PUBLIC_ENDPOINTS = {
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/health/",
        "/health/check",
        "/info",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and validate authentication."""
        
        # Skip authentication for public endpoints
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)
        
        # Skip authentication in development mode
        if settings.DEBUG and settings.ENVIRONMENT == "development":
            # Set a mock user for development
            request.state.user = {
                "id": "dev-user",
                "email": "dev@finance-app.com",
                "name": "Development User"
            }
            return await call_next(request)
        
        # Extract and validate token
        token = self._extract_token(request)
        if not token:
            raise HTTPException(
                status_code=401,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        try:
            # Decode and validate JWT
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Set user info in request state
            request.state.user = {
                "id": payload.get("sub"),
                "email": payload.get("email"),
                "name": payload.get("name"),
                "exp": payload.get("exp")
            }
            
            logger.debug(f"Authenticated user: {payload.get('email')}")
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return await call_next(request)
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public."""
        # Exact match
        if path in self.PUBLIC_ENDPOINTS:
            return True
        
        # Pattern matching for health endpoints
        if path.startswith("/health"):
            return True
        
        # Pattern matching for static files
        if path.startswith("/static"):
            return True
        
        return False
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from request."""
        # Check Authorization header
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            return authorization[7:]  # Remove "Bearer " prefix
        
        # Check query parameter (for WebSocket or special cases)
        token = request.query_params.get("token")
        if token:
            return token
        
        # Check cookie (if using cookie-based auth)
        token = request.cookies.get("access_token")
        if token:
            return token
        
        return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.client_requests = {}  # In production, use Redis
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and apply rate limiting."""
        
        # Skip rate limiting in development
        if settings.DEBUG:
            return await call_next(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check rate limit
        if self._is_rate_limited(client_ip):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60"}
            )
        
        # Record request
        self._record_request(client_ip)
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"
    
    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client is rate limited."""
        import time
        
        current_time = time.time()
        window_start = current_time - 60  # 1 minute window
        
        # Get client request history
        if client_ip not in self.client_requests:
            return False
        
        # Filter requests within the time window
        recent_requests = [
            req_time for req_time in self.client_requests[client_ip]
            if req_time > window_start
        ]
        
        return len(recent_requests) >= self.requests_per_minute
    
    def _record_request(self, client_ip: str):
        """Record a request for rate limiting."""
        import time
        
        current_time = time.time()
        
        if client_ip not in self.client_requests:
            self.client_requests[client_ip] = []
        
        # Add current request
        self.client_requests[client_ip].append(current_time)
        
        # Clean old requests (keep only last hour)
        hour_ago = current_time - 3600
        self.client_requests[client_ip] = [
            req_time for req_time in self.client_requests[client_ip]
            if req_time > hour_ago
        ]


def get_current_user(request: Request) -> dict:
    """Get current authenticated user from request."""
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    return request.state.user


def require_auth(request: Request) -> dict:
    """Dependency to require authentication."""
    return get_current_user(request)

