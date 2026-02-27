"""
Application configuration and constants.

Centralizes all tuneable parameters so they can be adjusted
without touching business logic.  Values are resolved in order:
    1. Environment variable  (if set)
    2. Hardcoded default

For production deployments, set these via your .env or
orchestration layer rather than editing this file.
"""

import os

# ── Proxy Re-Encryption defaults ────────────────────────────────
PRE_THRESHOLD = int(os.getenv("PRE_THRESHOLD", "2"))
PRE_SHARES = int(os.getenv("PRE_SHARES", "3"))

# ── DID document schema ─────────────────────────────────────────
DID_CONTEXT_URL = "https://w3id.org/did/v1"
DID_METHOD = "op"

# ── Token validation (placeholder) ──────────────────────────────
_tbr = os.getenv("TOKEN_BURN_REQUIRED", "false")
TOKEN_BURN_REQUIRED = _tbr.lower() == "true"
TOKEN_CONTRACT_ADDRESS = os.getenv("TOKEN_CONTRACT_ADDRESS", "")

# ── Logging ──────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s | %(name)-18s | %(levelname)-7s | %(message)s"
