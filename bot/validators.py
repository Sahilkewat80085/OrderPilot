"""
Input validators for TradeForge.
Ensures command-line inputs and programmatic requests conform to Binance API rules.
"""

import re
from typing import Any
from bot.exceptions import ValidationError


def validate_symbol(symbol: Any) -> str:
    """
    Sanitizes and validates the crypto market symbol (e.g. BTCUSDT, ETHUSDT).
    
    Args:
        symbol: The input symbol string.
        
    Returns:
        Cleaned uppercase symbol string.
        
    Raises:
        ValidationError: If format is invalid or symbol is blank.
    """
    if not symbol or not isinstance(symbol, str):
        raise ValidationError("Symbol must be a non-empty string.")
        
    sanitized = symbol.strip().upper()
    
    # Binance Futures USDS-M symbol validation (e.g., BTCUSDT, SOLUSDT, BNBUSDT)
    # Must consist of only letters and numbers, typically between 3 and 15 characters
    # Usually ends with USDT, BUSD, or USDC
    pattern = r"^[A-Z0-9]{3,15}$"
    if not re.match(pattern, sanitized):
        raise ValidationError(
            f"Invalid symbol format: '{symbol}'. Symbol must contain only alphanumeric characters "
            "and be between 3 and 15 characters long (e.g. BTCUSDT, ETHUSDT)."
        )
        
    # Ensure it ends with a standard USDT-M settlement coin
    valid_suffixes = ("USDT", "BUSD", "USDC", "USDS")
    if not sanitized.endswith(valid_suffixes):
        raise ValidationError(
            f"Invalid symbol stablecoin base: '{symbol}'. "
            f"Usd-M futures symbols must end with one of: {', '.join(valid_suffixes)}."
        )
        
    return sanitized


def validate_side(side: Any) -> str:
    """
    Validates and formats the order side (BUY or SELL).
    
    Args:
        side: The input order side string.
        
    Returns:
        Uppercase side string ('BUY' or 'SELL').
        
    Raises:
        ValidationError: If invalid order side is provided.
    """
    if not side or not isinstance(side, str):
        raise ValidationError("Order side must be a non-empty string.")
        
    sanitized = side.strip().upper()
    if sanitized not in ("BUY", "SELL"):
        raise ValidationError(
            f"Invalid order side: '{side}'. Side must be either 'BUY' or 'SELL'."
        )
        
    return sanitized


def validate_order_type(order_type: Any) -> str:
    """
    Validates and formats the order type (MARKET, LIMIT, or STOP_LIMIT).
    
    Args:
        order_type: The input order type string.
        
    Returns:
        Uppercase type string ('MARKET', 'LIMIT', or 'STOP_LIMIT').
        
    Raises:
        ValidationError: If invalid order type is provided.
    """
    if not order_type or not isinstance(order_type, str):
        raise ValidationError("Order type must be a non-empty string.")
        
    sanitized = order_type.strip().upper()
    valid_types = ("MARKET", "LIMIT", "STOP_LIMIT")
    if sanitized not in valid_types:
        raise ValidationError(
            f"Invalid order type: '{order_type}'. Type must be one of: {', '.join(valid_types)}."
        )
        
    return sanitized


def validate_quantity(quantity: Any) -> float:
    """
    Validates that the quantity is a positive number.
    
    Args:
        quantity: Float, integer, or numeric string representation of quantity.
        
    Returns:
        Float value of the quantity.
        
    Raises:
        ValidationError: If quantity is non-positive or cannot be cast to float.
    """
    if quantity is None:
        raise ValidationError("Quantity is required and cannot be empty.")
        
    try:
        qty_float = float(quantity)
    except (ValueError, TypeError):
        raise ValidationError(f"Quantity must be a valid number, got '{quantity}'.")
        
    if qty_float <= 0:
        raise ValidationError(f"Quantity must be greater than zero, got {qty_float}.")
        
    return qty_float


def validate_price(price: Any, order_type: str) -> float | None:
    """
    Validates price requirements based on order type.
    
    Args:
        price: Price input (required for LIMIT/STOP_LIMIT, ignored or must be empty for MARKET).
        order_type: The validated uppercase order type string.
        
    Returns:
        Float value of price, or None if MARKET.
        
    Raises:
        ValidationError: If price is missing for LIMIT/STOP_LIMIT or non-positive.
    """
    if order_type in ("LIMIT", "STOP_LIMIT"):
        if price is None or str(price).strip() == "":
            raise ValidationError(f"Price is mandatory for '{order_type}' orders.")
            
        try:
            price_float = float(price)
        except (ValueError, TypeError):
            raise ValidationError(f"Price must be a valid number, got '{price}'.")
            
        if price_float <= 0:
            raise ValidationError(f"Price must be a positive number greater than zero, got {price_float}.")
            
        return price_float
        
    # For MARKET orders, price is not required
    if price is not None and str(price).strip() != "":
        # We can issue a minor warning or just return None
        pass
        
    return None


def validate_stop_price(stop_price: Any, order_type: str) -> float | None:
    """
    Validates stop price requirements for advanced Stop-Limit orders.
    
    Args:
        stop_price: Stop price input (required for STOP_LIMIT).
        order_type: The validated uppercase order type string.
        
    Returns:
        Float value of stop price, or None.
        
    Raises:
        ValidationError: If stop price is missing or non-positive for STOP_LIMIT.
    """
    if order_type == "STOP_LIMIT":
        if stop_price is None or str(stop_price).strip() == "":
            raise ValidationError("Stop Price is mandatory for 'STOP_LIMIT' orders.")
            
        try:
            stop_float = float(stop_price)
        except (ValueError, TypeError):
            raise ValidationError(f"Stop Price must be a valid number, got '{stop_price}'.")
            
        if stop_float <= 0:
            raise ValidationError(f"Stop Price must be a positive number greater than zero, got {stop_float}.")
            
        return stop_float
        
    return None
