"""
Unit tests for the validator functions in bot/validators.py.
Covers positive, negative, and edge cases.
"""

import pytest
from bot.exceptions import ValidationError
from bot.validators import (
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
    validate_stop_price,
)


# =====================================================================
# Symbol Validation Tests
# =====================================================================

def test_validate_symbol_valid() -> None:
    """Verifies that correct USDT-M Binance Future symbols pass and capitalize."""
    assert validate_symbol("btcusdt") == "BTCUSDT"
    assert validate_symbol("ETHUSDT") == "ETHUSDT"
    assert validate_symbol("solusdc") == "SOLUSDC"
    assert validate_symbol("  bnbbusd  ") == "BNBBUSD"


def test_validate_symbol_invalid_format() -> None:
    """Verifies format failures raise ValidationError."""
    # Special characters
    with pytest.raises(ValidationError, match="Invalid symbol format"):
        validate_symbol("BTC-USDT")
        
    # Too short
    with pytest.raises(ValidationError, match="Invalid symbol format"):
        validate_symbol("BT")
        
    # Non-string/empty
    with pytest.raises(ValidationError, match="Symbol must be a non-empty string"):
        validate_symbol("")
    with pytest.raises(ValidationError, match="Symbol must be a non-empty string"):
        validate_symbol(None)


def test_validate_symbol_invalid_base() -> None:
    """Verifies that non-USDT-M stablecoins raise ValidationError."""
    with pytest.raises(ValidationError, match="stablecoin base"):
        validate_symbol("BTCBTC")
    with pytest.raises(ValidationError, match="stablecoin base"):
        validate_symbol("ETHUSD")
    with pytest.raises(ValidationError, match="stablecoin base"):
        validate_symbol("SOLEUR")


# =====================================================================
# Side Validation Tests
# =====================================================================

def test_validate_side_valid() -> None:
    """Verifies side inputs pass and sanitize."""
    assert validate_side("buy") == "BUY"
    assert validate_side("SELL") == "SELL"
    assert validate_side("  Buy  ") == "BUY"


def test_validate_side_invalid() -> None:
    """Verifies incorrect side values raise ValidationError."""
    with pytest.raises(ValidationError, match="Side must be either 'BUY' or 'SELL'"):
        validate_side("HOLD")
    with pytest.raises(ValidationError, match="Side must be either 'BUY' or 'SELL'"):
        validate_side("SHORT")
    with pytest.raises(ValidationError, match="Side must be either 'BUY' or 'SELL'"):
        validate_side("LONG")
    with pytest.raises(ValidationError, match="Order side must be a non-empty string"):
        validate_side(None)


# =====================================================================
# Order Type Validation Tests
# =====================================================================

def test_validate_order_type_valid() -> None:
    """Verifies order types pass and capitalize."""
    assert validate_order_type("market") == "MARKET"
    assert validate_order_type("LIMIT") == "LIMIT"
    assert validate_order_type("stop_limit") == "STOP_LIMIT"


def test_validate_order_type_invalid() -> None:
    """Verifies incorrect order types raise ValidationError."""
    with pytest.raises(ValidationError, match="Type must be one of"):
        validate_order_type("STOP_LOSS")
    with pytest.raises(ValidationError, match="Type must be one of"):
        validate_order_type("TAKE_PROFIT")
    with pytest.raises(ValidationError, match="Order type must be a non-empty string"):
        validate_order_type(None)


# =====================================================================
# Quantity Validation Tests
# =====================================================================

def test_validate_quantity_valid() -> None:
    """Verifies quantity is cast to positive float successfully."""
    assert validate_quantity(0.001) == 0.001
    assert validate_quantity("0.5") == 0.5
    assert validate_quantity(10) == 10.0


def test_validate_quantity_invalid() -> None:
    """Verifies non-positive or non-numeric quantity raises ValidationError."""
    with pytest.raises(ValidationError, match="Quantity must be greater than zero"):
        validate_quantity(0)
    with pytest.raises(ValidationError, match="Quantity must be greater than zero"):
        validate_quantity(-1.5)
    with pytest.raises(ValidationError, match="Quantity must be a valid number"):
        validate_quantity("abc")
    with pytest.raises(ValidationError, match="Quantity is required"):
        validate_quantity(None)


# =====================================================================
# Price Validation Tests
# =====================================================================

def test_validate_price_market() -> None:
    """Verifies price is ignored or returns None for MARKET orders."""
    assert validate_price(None, "MARKET") is None
    assert validate_price("", "MARKET") is None
    assert validate_price(100.5, "MARKET") is None


def test_validate_price_limit_valid() -> None:
    """Verifies positive price for LIMIT or STOP_LIMIT orders works."""
    assert validate_price(95000, "LIMIT") == 95000.0
    assert validate_price("150.75", "STOP_LIMIT") == 150.75


def test_validate_price_limit_missing() -> None:
    """Verifies missing prices raise ValidationError for LIMIT or STOP_LIMIT."""
    with pytest.raises(ValidationError, match="Price is mandatory"):
        validate_price(None, "LIMIT")
    with pytest.raises(ValidationError, match="Price is mandatory"):
        validate_price(" ", "STOP_LIMIT")


def test_validate_price_limit_non_positive() -> None:
    """Verifies negative or zero price raises ValidationError."""
    with pytest.raises(ValidationError, match="Price must be a positive number"):
        validate_price(0, "LIMIT")
    with pytest.raises(ValidationError, match="Price must be a positive number"):
        validate_price("-5", "LIMIT")
    with pytest.raises(ValidationError, match="Price must be a valid number"):
        validate_price("not-a-number", "STOP_LIMIT")


# =====================================================================
# Stop Price Validation Tests
# =====================================================================

def test_validate_stop_price_non_stop_limit() -> None:
    """Verifies stop price is ignored for non-STOP_LIMIT order types."""
    assert validate_stop_price(100.0, "LIMIT") is None
    assert validate_stop_price(50.0, "MARKET") is None
    assert validate_stop_price(None, "LIMIT") is None


def test_validate_stop_price_stop_limit_valid() -> None:
    """Verifies stop price is validated correctly for STOP_LIMIT."""
    assert validate_stop_price(96000, "STOP_LIMIT") == 96000.0
    assert validate_stop_price("123.45", "STOP_LIMIT") == 123.45


def test_validate_stop_price_stop_limit_missing_or_invalid() -> None:
    """Verifies stop price failure modes for STOP_LIMIT."""
    with pytest.raises(ValidationError, match="Stop Price is mandatory"):
        validate_stop_price(None, "STOP_LIMIT")
    with pytest.raises(ValidationError, match="Stop Price must be a positive number"):
        validate_stop_price(0, "STOP_LIMIT")
    with pytest.raises(ValidationError, match="Stop Price must be a positive number"):
        validate_stop_price(-10.5, "STOP_LIMIT")
    with pytest.raises(ValidationError, match="Stop Price must be a valid number"):
        validate_stop_price("abc", "STOP_LIMIT")
