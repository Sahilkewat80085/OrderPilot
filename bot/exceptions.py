"""
Custom exception hierarchy for TradeForge.
Ensures elegant, domain-specific error reporting.
"""

class TradeForgeError(Exception):
    """Base exception for all TradeForge bot operations."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ConfigurationError(TradeForgeError):
    """Raised when environment variables or configurations are missing or invalid."""
    pass


class ValidationError(TradeForgeError):
    """Raised when request parameters fail validator checks (e.g. side, qty, price)."""
    pass


class APIError(TradeForgeError):
    """Base exception for external Binance API interactions."""
    pass


class APIConnectionError(APIError):
    """Raised when HTTPX connection timeouts or network failures occur."""
    pass


class APIResponseError(APIError):
    """
    Raised when Binance returns a non-200 status code.
    Contains detailed error code and message sent by Binance matching engine.
    """
    def __init__(self, message: str, status_code: int, binance_code: int | None = None, response_text: str | None = None):
        detail = f" (Binance Code: {binance_code})" if binance_code is not None else ""
        full_message = f"HTTP {status_code}{detail}: {message}"
        super().__init__(full_message)
        self.status_code = status_code
        self.binance_code = binance_code
        self.response_text = response_text
