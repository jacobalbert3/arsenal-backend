from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff" 
        response.headers["X-Frame-Options"] = "SAMEORIGIN"  # controls if the browser can render the page in a frame
        response.headers["X-XSS-Protection"] = "1; mode=block" # protects against XSS attacks
        # Remove HSTS and CSP for local development
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains" # makes sure the browser only uses HTTPS
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response
