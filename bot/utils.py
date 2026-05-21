"""
Utility functions for TradeForge.
Handles cryptographic payload signing and precise timestamp calculations.
"""

import hmac
import hashlib
import time


def generate_signature(secret_key: str, query_string: str) -> str:
    """
    Generates HMAC-SHA256 signature for Binance API authentication.
    
    Args:
        secret_key: API secret key.
        query_string: The string containing request parameters ordered alphabetically/chronologically.
        
    Returns:
        Hex-encoded signature string.
    """
    return hmac.new(
        key=secret_key.encode("utf-8"),
        msg=query_string.encode("utf-8"),
        digestmod=hashlib.sha256
    ).hexdigest()


def get_timestamp_ms() -> int:
    """
    Returns the current UNIX epoch timestamp in milliseconds.
    
    Returns:
        Integer representing time in milliseconds.
    """
    return int(time.time() * 1000)
