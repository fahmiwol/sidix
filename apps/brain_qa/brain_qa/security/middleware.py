"""
middleware.py — FastAPI Security Middleware (orchestrator semua layer)

Pipeline per request:
  1. Validate request (IP, UA, path) → block kalau bad
  2. Log security event (LOW kalau pass, HIGH kalau block)
  3. Pass ke handler — handler bertanggung jawab call sanitize_user_input()
     untuk body content (kalau aplikatif)
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from .request_validator import validate_request, block_ip
from .audit_log import log_security_event


class SidixSecurityMiddleware(BaseHTTPMiddleware):
    """
    Pre-process semua request: blok yang jelas-jelas suspicious.
    Allow-list paths kritis (health check, etc) untuk skip pemeriksaan berat.
    """

    SKIP_PATHS = {"/health", "/openapi.json", "/docs", "/redoc"}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip safe paths
        if path in self.SKIP_PATHS:
            return await call_next(request)

        # Extract metadata
        source_ip = self._extract_ip(request)
        user_agent = request.headers.get("user-agent", "")
        method = request.method
        body_length = int(request.headers.get("content-length", 0) or 0)

        # Validate
        result = validate_request(
            source_ip=source_ip,
            user_agent=user_agent,
            path=path,
            body_length=body_length,
            method=method,
        )

        if result.blocked:
            # Log + auto-block kalau scoring tinggi
            log_security_event(
                event_type=f"request_blocked:{result.reason}",
                severity="HIGH",
                source_ip=source_ip,
                user_agent=user_agent,
                endpoint=path,
                description=f"blocked: {result.reason}, flags={result.flags}",
                details={"score": result.anomaly_score, "method": method},
            )
            # Auto-block IP kalau score >= 80 (1 hari)
            if result.anomaly_score >= 80 and source_ip:
                block_ip(source_ip, reason=result.reason, duration_seconds=86400)
            return JSONResponse(
                status_code=403,
                content={"error": "request blocked", "reason": "policy_violation"},
            )

        # Anomaly score tinggi tapi belum blok → log saja
        if result.anomaly_score >= 40:
            log_security_event(
                event_type="suspicious_request",
                severity="MEDIUM",
                source_ip=source_ip,
                user_agent=user_agent,
                endpoint=path,
                description=f"anomaly score {result.anomaly_score}",
                details={"flags": result.flags},
            )

        # Continue ke handler
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            log_security_event(
                event_type="handler_exception",
                severity="MEDIUM",
                source_ip=source_ip,
                endpoint=path,
                description=str(e)[:300],
            )
            raise

    @staticmethod
    def _extract_ip(request: Request) -> str:
        """Get real client IP (consider X-Forwarded-For dari nginx)."""
        xff = request.headers.get("x-forwarded-for", "")
        if xff:
            # Ambil IP pertama (paling kiri = real client)
            return xff.split(",")[0].strip()
        if request.client:
            return request.client.host
        return ""
