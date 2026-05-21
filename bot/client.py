"""
Custom HTTPX Client for Binance Futures Testnet REST API.
Handles automatic signing of requests, headers, logging, and error mapping.
"""

from typing import Any, Dict
from urllib.parse import urlencode
import httpx

from bot.config import settings
from bot.exceptions import APIConnectionError, APIResponseError, ConfigurationError
from bot.logging_config import logger
from bot.utils import generate_signature, get_timestamp_ms


class BinanceFuturesClient:
    """Synchronous client to communicate with the Binance Futures (USDT-M) Testnet API."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        base_url: str | None = None,
        recv_window: int | None = None,
    ) -> None:
        """
        Initializes the Binance Futures Client.
        Defaults to settings loaded from .env if not specified.
        """
        self.api_key = api_key or settings.api_key
        self.api_secret = api_secret or settings.api_secret
        
        # Determine the base URL. If configured base URL points to testnet,
        # ensure it's mapped to the REST API endpoint (demo-fapi.binance.com is reliable)
        configured_url = base_url or settings.base_url
        if "testnet.binancefuture.com" in configured_url:
            self.base_url = "https://demo-fapi.binance.com"
        else:
            self.base_url = configured_url.rstrip("/")
            
        self.recv_window = recv_window or settings.recv_window

    def _headers(self, signed: bool) -> Dict[str, str]:
        """Generates the necessary headers for the API request."""
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "TradeForge/1.0.0 (Python Trading Bot)",
        }
        if signed:
            if not self.api_key:
                raise ConfigurationError("API Key is required for signed requests but is missing.")
            headers["X-MBX-APIKEY"] = self.api_key
        return headers

    def _sign_payload(self, params: Dict[str, Any]) -> str:
        """
        Constructs and signs the payload with timestamp and recvWindow.
        
        Args:
            params: Dictionary of request parameters.
            
        Returns:
            The signed query string including timestamp, recvWindow, and signature.
        """
        if not self.api_secret:
            raise ConfigurationError("API Secret is required for signed requests but is missing.")
            
        payload = params.copy()
        
        # Inject standard signed endpoint parameters
        if "timestamp" not in payload:
            payload["timestamp"] = get_timestamp_ms()
        if "recvWindow" not in payload:
            payload["recvWindow"] = self.recv_window

        # Convert to query string (standard URL encoding)
        query_string = urlencode(payload)
        
        # Create HMAC-SHA256 signature
        signature = generate_signature(self.api_secret, query_string)
        
        # Append signature to the end of the query string as required by Binance
        signed_query_string = f"{query_string}&signature={signature}"
        return signed_query_string

    def request(
        self,
        method: str,
        endpoint: str,
        params: Dict[str, Any] | None = None,
        signed: bool = True,
    ) -> Dict[str, Any]:
        """
        Sends an HTTP request to the Binance Futures REST API.
        
        Args:
            method: HTTP verb (GET, POST, DELETE, etc.).
            endpoint: API endpoint path (e.g. '/fapi/v1/order').
            params: Dictionary of parameters to include in the request.
            signed: Whether the endpoint requires authentication and signature.
            
        Returns:
            Decoded JSON response from Binance.
            
        Raises:
            APIConnectionError: Network timeout, resolution, or socket errors.
            APIResponseError: Non-200 responses from Binance.
        """
        method = method.upper()
        params = params or {}
        headers = self._headers(signed)

        # Prepare request URL and query parameters
        if signed:
            # For signed requests, sign the parameters and pass as query string
            signed_query = self._sign_payload(params)
            url = f"{self.base_url}{endpoint}?{signed_query}"
            log_params = {k: v for k, v in params.items() if k not in ("signature", "timestamp")}
            logger.debug(f"SIGNED {method} {endpoint} | Params (excl. signature): {log_params}")
        else:
            # For public requests, pass standard parameters
            query_string = urlencode(params) if params else ""
            url = f"{self.base_url}{endpoint}"
            if query_string:
                url = f"{url}?{query_string}"
            logger.debug(f"PUBLIC {method} {endpoint} | Params: {params}")

        try:
            # Issue the request with a strict 10s connection & read timeout
            with httpx.Client(timeout=10.0) as client:
                response = client.request(method, url, headers=headers)
                
            logger.debug(f"Response Received | Status Code: {response.status_code}")
            
        except httpx.RequestError as exc:
            err_msg = f"Network request to Binance failed: {str(exc)}"
            logger.error(err_msg, exc_info=True)
            raise APIConnectionError(err_msg) from exc

        # Handle API Error Responses
        if response.status_code != 200:
            try:
                error_data = response.json()
                binance_msg = error_data.get("msg", "Unknown error")
                binance_code = error_data.get("code")
            except Exception:
                binance_msg = response.text
                binance_code = None
                
            logger.error(
                f"Binance API Refused Request | HTTP Status: {response.status_code} | "
                f"Error Code: {binance_code} | Message: {binance_msg}"
            )
            raise APIResponseError(
                message=binance_msg,
                status_code=response.status_code,
                binance_code=binance_code,
                response_text=response.text,
            )

        # Return successful parsed JSON
        try:
            return response.json()
        except ValueError as exc:
            err_msg = f"Received invalid JSON response from Binance: {response.text}"
            logger.error(err_msg)
            raise APIResponseError(err_msg, status_code=200) from exc

    def ping(self) -> bool:
        """
        Pings the Binance Futures API to test network connectivity and latency.
        
        Returns:
            True if connectivity is successful, False otherwise.
        """
        try:
            self.request("GET", "/fapi/v1/ping", signed=False)
            return True
        except APIError:
            return False

    def get_exchange_info(self) -> Dict[str, Any]:
        """
        Retrieves exchange information, including symbols, tick sizes, and precision limits.
        
        Returns:
            Exchange info dictionary.
        """
        return self.request("GET", "/fapi/v1/exchangeInfo", signed=False)
