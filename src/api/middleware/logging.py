"""
Logging Middleware for Finance App API.
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
import json


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Log request
        await self._log_request(request, request_id)
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            logger.error(
                f"Request failed | "
                f"ID: {request_id} | "
                f"Method: {request.method} | "
                f"URL: {request.url} | "
                f"Error: {str(e)} | "
                f"Duration: {process_time:.3f}s"
            )
            raise
        
        # Calculate process time
        process_time = time.time() - start_time
        
        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log response
        await self._log_response(request, response, request_id, process_time)
        
        return response
    
    async def _log_request(self, request: Request, request_id: str):
        """Log incoming request."""
        
        # Get client info
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "Unknown")
        
        # Get request body for POST/PUT requests (if small enough)
        body_preview = ""
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if len(body) < 1000:  # Only log small bodies
                    body_preview = body.decode("utf-8")[:500]
                else:
                    body_preview = f"<large body: {len(body)} bytes>"
            except Exception:
                body_preview = "<unable to read body>"
        
        logger.info(
            f"Request started | "
            f"ID: {request_id} | "
            f"Method: {request.method} | "
            f"URL: {request.url} | "
            f"Client: {client_ip} | "
            f"User-Agent: {user_agent[:100]} | "
            f"Body: {body_preview}"
        )
    
    async def _log_response(self, request: Request, response: Response, request_id: str, process_time: float):
        """Log outgoing response."""
        
        # Determine log level based on status code
        if response.status_code >= 500:
            log_level = "error"
        elif response.status_code >= 400:
            log_level = "warning"
        else:
            log_level = "info"
        
        # Log response
        log_message = (
            f"Request completed | "
            f"ID: {request_id} | "
            f"Method: {request.method} | "
            f"URL: {request.url} | "
            f"Status: {response.status_code} | "
            f"Duration: {process_time:.3f}s"
        )
        
        if log_level == "error":
            logger.error(log_message)
        elif log_level == "warning":
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting metrics."""
    
    def __init__(self, app):
        super().__init__(app)
        self.request_count = 0
        self.request_times = []
        self.error_count = 0
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics."""
        
        start_time = time.time()
        self.request_count += 1
        
        try:
            response = await call_next(request)
            
            # Record timing
            process_time = time.time() - start_time
            self.request_times.append(process_time)
            
            # Keep only last 1000 request times
            if len(self.request_times) > 1000:
                self.request_times = self.request_times[-1000:]
            
            # Count errors
            if response.status_code >= 400:
                self.error_count += 1
            
            return response
            
        except Exception as e:
            self.error_count += 1
            process_time = time.time() - start_time
            self.request_times.append(process_time)
            raise
    
    def get_metrics(self) -> dict:
        """Get current metrics."""
        if not self.request_times:
            return {
                "request_count": self.request_count,
                "error_count": self.error_count,
                "avg_response_time": 0,
                "min_response_time": 0,
                "max_response_time": 0
            }
        
        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / self.request_count if self.request_count > 0 else 0,
            "avg_response_time": sum(self.request_times) / len(self.request_times),
            "min_response_time": min(self.request_times),
            "max_response_time": max(self.request_times),
            "recent_requests": len(self.request_times)
        }

