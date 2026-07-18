from __future__ import annotations

import hashlib
import hmac

from config import settings


def hash_access_code(access_code: str) -> str:
    """Hash a customer code with an optional server-side pepper."""
    return hmac.new(
        settings.access_code_pepper.encode("utf-8"),
        access_code.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
