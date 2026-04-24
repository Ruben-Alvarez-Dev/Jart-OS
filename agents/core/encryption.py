"""
Jart-OS EncryptionManager — AES-style symmetric encryption
Spec: Fase 5 Punto 5 — Seguridad

Uses Fernet (AES-128-CBC + HMAC-SHA256) if cryptography is available.
Falls back to XOR-based obfuscation (NOT production-grade) otherwise.
"""

import os
import base64
import hashlib
import logging
from typing import Optional

log = logging.getLogger("jart-os.core.encryption")

try:
    from cryptography.fernet import Fernet
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False
    log.warning("cryptography not installed. Using XOR fallback. pip install cryptography")


class EncryptionManager:
    """
    Symmetric encryption for sensitive data.

    Usage:
        enc = EncryptionManager()
        ciphertext = enc.encrypt("secret data")
        plaintext = enc.decrypt(ciphertext)
    """

    def __init__(self, key: str = None):
        if HAS_CRYPTO:
            if key:
                # Derive Fernet key from arbitrary string
                k = hashlib.sha256(key.encode()).digest()
                self._fernet_key = base64.urlsafe_b64encode(k)
            else:
                self._fernet_key = Fernet.generate_key()
            self._fernet = Fernet(self._fernet_key)
        else:
            # XOR fallback
            self._xor_key = key.encode() if key else None
            if self._xor_key is None:
                raise RuntimeError("ENCRYPTION_KEY env var is required — no default for security")

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext -> base64 string."""
        if HAS_CRYPTO:
            return self._fernet.encrypt(plaintext.encode()).decode()
        else:
            return self._xor_encrypt(plaintext)

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt base64 string -> plaintext."""
        if HAS_CRYPTO:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        else:
            return self._xor_decrypt(ciphertext)

    # ------------------------------------------------------------------
    # XOR fallback (NOT secure, only for dev/testing)
    # ------------------------------------------------------------------

    def _xor_encrypt(self, plaintext: str) -> str:
        data = plaintext.encode()
        key = self._xor_key
        encrypted = bytes(a ^ key[i % len(key)] for i, a in enumerate(data))
        return base64.b64encode(encrypted).decode()

    def _xor_decrypt(self, ciphertext: str) -> str:
        data = base64.b64decode(ciphertext)
        key = self._xor_key
        decrypted = bytes(a ^ key[i % len(key)] for i, a in enumerate(data))
        return decrypted.decode()
