"""
Configuration management for TradeForge.
Loads, validates, and manages environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from bot.exceptions import ConfigurationError

# Auto-load .env from workspace/project root
project_root = Path(__file__).resolve().parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)


class Settings:
    """Read-only container for TradeForge configuration settings."""
    
    def __init__(self) -> None:
        self.api_key = os.getenv("BINANCE_API_KEY", "").strip()
        self.api_secret = os.getenv("BINANCE_API_SECRET", "").strip()
        
        # Binance base URL defaults to the USD(S)-M Futures Testnet
        # Using testnet.binancefuture.com as the user configuration default
        self.base_url = os.getenv("BINANCE_BASE_URL", "https://testnet.binancefuture.com").strip().rstrip("/")
        
        # Parse receiving window (default 5000ms)
        try:
            self.recv_window = int(os.getenv("RECV_WINDOW", "5000"))
        except ValueError:
            self.recv_window = 5000
            
        # Logging configurations
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.log_file = project_root / "logs" / "trading.log"

    def validate(self) -> None:
        """
        Validates that mandatory variables (API keys) are configured.
        Raises ConfigurationError if invalid.
        """
        missing = []
        if not self.api_key or "your_testnet_api_key_here" in self.api_key:
            missing.append("BINANCE_API_KEY")
        if not self.api_secret or "your_testnet_api_secret_here" in self.api_secret:
            missing.append("BINANCE_API_SECRET")
            
        if missing:
            raise ConfigurationError(
                f"Missing or placeholder configuration for required keys: {', '.join(missing)}. "
                f"Please update the '.env' file located at: {env_path}"
            )


# Singleton settings instance
settings = Settings()
