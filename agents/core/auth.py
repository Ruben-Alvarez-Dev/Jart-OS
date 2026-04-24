"""
Jart-OS AuthManager — JWT authentication
Spec: Fase 5 Punto 5 — Seguridad
"""

import os
import time
import json
import logging
from typing import Optional

log = logging.getLogger("jart-os.core.auth")

# Try to import jwt, fallback to simple HMAC if not available
try:
    import jwt
    HAS_JWT = True
except ImportError:
    import hashlib
    import hmac
    HAS_JWT = False
    log.warning("PyJWT not installed. Using simple HMAC fallback. pip install PyJWT")


class AuthManager:
    """
    JWT-based authentication for agents and users.

    Roles: admin, agent, user
    TTL: admin=24h, agent=1h, user=8h
    """

    ROLE_TTL = {
        "admin": 86400,   # 24h
        "agent": 3600,    # 1h
        "user": 28800,    # 8h
    }

    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or os.getenv("JWT_SECRET")
        if not self.secret_key:
            raise RuntimeError("JWT_SECRET env var is required — no default for security")
        self.token_blacklist_key = "jart-os:auth:blacklist"

    def generate_token(self, subject: str, role: str, ttl: int = None) -> str:
        """Generate a JWT token."""
        expiry = ttl or self.ROLE_TTL.get(role, 3600)
        now = int(time.time())

        payload = {
            "sub": subject,
            "role": role,
            "iat": now,
            "exp": now + expiry,
        }

        if HAS_JWT:
            return jwt.encode(payload, self.secret_key, algorithm="HS256")
        else:
            # Simple HMAC fallback
            payload_str = json.dumps(payload, sort_keys=True)
            sig = hmac.new(
                self.secret_key.encode(),
                payload_str.encode(),
                hashlib.sha256,
            ).hexdigest()
            import base64
            payload_b64 = base64.urlsafe_b64encode(payload_str.encode()).decode()
            return f"{payload_b64}.{sig}"

    def verify_token(self, token: str) -> Optional[dict]:
        """Verify token and return payload. None if invalid/expired."""
        if not token:
            return None

        try:
            if HAS_JWT:
                payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            else:
                import base64
                parts = token.split(".")
                if len(parts) != 2:
                    return None
                payload_b64, sig = parts
                payload_str = base64.urlsafe_b64decode(payload_b64).decode()
                expected_sig = hmac.new(
                    self.secret_key.encode(),
                    payload_str.encode(),
                    hashlib.sha256,
                ).hexdigest()
                if sig != expected_sig:
                    return None
                payload = json.loads(payload_str)

            # Check expiry
            if payload.get("exp", 0) < int(time.time()):
                return None

            return payload

        except Exception as e:
            log.warning(f"Token verification failed: {e}")
            return None

    def revoke_token(self, token: str, redis_client=None):
        """Add token to blacklist."""
        if redis_client:
            payload = self.verify_token(token)
            if payload:
                ttl = payload.get("exp", 0) - int(time.time())
                if ttl > 0:
                    redis_client.setex(
                        f"{self.token_blacklist_key}:{token}",
                        ttl,
                        "revoked",
                    )

    def is_revoked(self, token: str, redis_client=None) -> bool:
        """Check if token is in blacklist."""
        if not redis_client:
            return False
        return redis_client.exists(f"{self.token_blacklist_key}:{token}") > 0
