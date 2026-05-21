"""
Order management and abstraction layer for TradeForge.
Validates inputs, maps parameters to Binance REST schema, and builds response models.
"""

from dataclasses import dataclass
from typing import Any, Dict

from bot.client import BinanceFuturesClient
from bot.exceptions import ValidationError
from bot.logging_config import logger
from bot.validators import (
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)


@dataclass(frozen=True)
class OrderRequest:
    """Structure representing a validated trade request."""
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: float | None = None
    stop_price: float | None = None
    time_in_force: str = "GTC"


@dataclass(frozen=True)
class OrderResponse:
    """Standardized representation of a successfully executed or placed order."""
    order_id: int
    symbol: str
    status: str
    client_order_id: str
    side: str
    order_type: str
    executed_qty: float
    avg_price: float
    limit_price: float | None
    stop_price: float | None
    raw_response: Dict[str, Any]

    @classmethod
    def from_binance_response(cls, data: Dict[str, Any]) -> "OrderResponse":
        """
        Parses raw Binance REST response dictionary into a clean OrderResponse.
        
        Args:
            data: Raw JSON dictionary from Binance fapi order endpoint.
        """
        # Binance fields are returned as strings in JSON.
        # Parse safe float conversions.
        try:
            executed_qty = float(data.get("executedQty", "0"))
        except (ValueError, TypeError):
            executed_qty = 0.0

        try:
            # For some statuses or orders, avgPrice might be zero or missing,
            # fallback to "price" or standard extraction
            avg_price = float(data.get("avgPrice", "0"))
        except (ValueError, TypeError):
            avg_price = 0.0

        try:
            limit_price = float(data.get("price", "0")) if data.get("price") else None
            if limit_price == 0.0:
                limit_price = None
        except (ValueError, TypeError):
            limit_price = None

        try:
            stop_price = float(data.get("stopPrice", "0")) if data.get("stopPrice") else None
            if stop_price == 0.0:
                stop_price = None
        except (ValueError, TypeError):
            stop_price = None

        return cls(
            order_id=int(data.get("orderId", 0)),
            symbol=data.get("symbol", "UNKNOWN"),
            status=data.get("status", "UNKNOWN"),
            client_order_id=data.get("clientOrderId", "UNKNOWN"),
            side=data.get("side", "UNKNOWN"),
            order_type=data.get("type", "UNKNOWN"),
            executed_qty=executed_qty,
            avg_price=avg_price,
            limit_price=limit_price,
            stop_price=stop_price,
            raw_response=data,
        )


class OrderManager:
    """Orchestrates validation and order submission on Binance Futures Testnet."""

    def __init__(self, client: BinanceFuturesClient | None = None) -> None:
        """Initializes the manager. If client is omitted, spawns a default settings client."""
        self.client = client or BinanceFuturesClient()
        self._exchange_info = None

    def get_precisions(self, symbol: str) -> tuple[int, int]:
        """Fetches the price and quantity precision limits for a symbol from the exchange."""
        if not self._exchange_info:
            try:
                self._exchange_info = self.client.get_exchange_info()
            except Exception as exc:
                logger.warning(f"Could not fetch exchange info: {exc}")
                return 2, 3  # Fallback defaults

        for s in self._exchange_info.get("symbols", []):
            if s.get("symbol") == symbol:
                return int(s.get("pricePrecision", 2)), int(s.get("quantityPrecision", 3))
        return 2, 3

    def prepare_request(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Any,
        price: Any = None,
        stop_price: Any = None,
        time_in_force: str = "GTC",
    ) -> OrderRequest:
        """
        Validates all input variables sequentially using validators module.
        Raises ValidationError if checks fail.
        
        Returns:
            An OrderRequest object representing fully validated parameters.
        """
        logger.info(f"Validating order params | Symbol: {symbol}, Side: {side}, Type: {order_type}, Qty: {quantity}")
        
        try:
            v_symbol = validate_symbol(symbol)
            v_side = validate_side(side)
            v_type = validate_order_type(order_type)
            v_qty = validate_quantity(quantity)
            v_price = validate_price(price, v_type)
            v_stop_price = validate_stop_price(stop_price, v_type)
        except ValidationError as exc:
            logger.warning(f"Validation failed: {exc.message}")
            raise exc

        logger.debug("Validation succeeded.")
        return OrderRequest(
            symbol=v_symbol,
            side=v_side,
            order_type=v_type,
            quantity=v_qty,
            price=v_price,
            stop_price=v_stop_price,
            time_in_force=time_in_force,
        )

    def place_order(self, request: OrderRequest) -> OrderResponse:
        """
        Transmits a validated OrderRequest to the Binance Futures Testnet matching engine.
        
        Args:
            request: Validated OrderRequest.
            
        Returns:
            An OrderResponse object containing order receipt details.
            
        Raises:
            APIError: If the server returns connectivity or application issues.
        """
        logger.info(
            f"Placing order request -> {request.side} {request.quantity} {request.symbol} [{request.order_type}]"
        )
        
        # Dynamically fetch asset precision
        price_prec, qty_prec = self.get_precisions(request.symbol)
        
        # Build API payload mapping with exact precisions to prevent Binance -1111 errors
        payload: Dict[str, Any] = {
            "symbol": request.symbol,
            "side": request.side,
            "type": request.order_type,
            "quantity": f"{request.quantity:.{qty_prec}f}",
        }

        # Inject Limit-specific or Stop-Limit-specific parameters
        if request.order_type == "LIMIT":
            payload["price"] = f"{request.price:.{price_prec}f}"
            payload["timeInForce"] = request.time_in_force
            
        elif request.order_type == "STOP_LIMIT":
            payload["price"] = f"{request.price:.{price_prec}f}"
            payload["stopPrice"] = f"{request.stop_price:.{price_prec}f}"
            payload["timeInForce"] = request.time_in_force

        try:
            raw_res = self.client.request("POST", "/fapi/v1/order", params=payload, signed=True)
            logger.info(
                f"Order placed successfully | OrderID: {raw_res.get('orderId')} | Status: {raw_res.get('status')}"
            )
            return OrderResponse.from_binance_response(raw_res)
            
        except Exception as exc:
            logger.error(f"Failed to place order: {str(exc)}")
            raise exc
