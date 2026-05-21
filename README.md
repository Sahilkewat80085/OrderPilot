# TradeForge - Binance Futures Testnet Trading Bot

TradeForge is a production-grade, highly modular, and professional command-line trading bot designed for executing trades on the **Binance Futures Testnet (USDT-M)**. Written in Python 3.11+ using zero external heavy trading dependencies, it leverages modern packages like `httpx` for lightweight HTTP REST requests, `Typer` for powerful CLI command structures, and `Rich` to deliver a stunning terminal-driven interactive dashboard experience.

---

## Key Features

- **Standard Order Operations:** Full support for placing `MARKET` and `LIMIT` orders.
- **Advanced Order Logic:** Support for placing `STOP_LIMIT` conditional orders.
- **Flexible Order Sides:** Fully supports `BUY` (Long) and `SELL` (Short) operations.
- **Dual Execution Modes:**
  1. **Direct CLI mode:** Perfect for scripting, cron tasks, or immediate execution.
  2. **Bonus Interactive terminal dashboard:** Beautiful, step-by-step UI with connection monitoring, live visual inputs, summary cards, and confirmation alerts.
- **Enterprise-Grade Architecture:** Decoupled design structure with custom logging, config, utility, and domain exception layers.
- **Precision Validation:** Strict parameters validation (symbol format, positive quantities/prices, missing limits) running locally before sending requests.
- **Professional Logging:** Structured dual logging that prints clean logs to the console and detailed traces (with rotation limits) to `logs/trading.log`.

---

## Project Directory Architecture

The repository layout is organized logically to separate utility, config, domain modeling, and user presentation concern:

```
tradeforge/
│
├── bot/
│   ├── __init__.py           # Package-level exports
│   ├── client.py             # HTTPX-based REST client with auto cryptographic signatures
│   ├── orders.py             # Order Manager, OrderRequest/Response dataclasses
│   ├── validators.py         # Strong business rules validators
│   ├── config.py             # Dotenv loader & validation settings
│   ├── exceptions.py         # Custom structured domain exception classes
│   ├── logging_config.py     # Dual file & console logger with RotatingFileHandler
│   └── utils.py              # HMAC-SHA256 signature & timestamp calculators
│
├── logs/
│   └── trading.log           # Rotation-based logs file
│
├── examples/
│   ├── market_order.txt      # Execution template output for MARKET orders
│   └── limit_order.txt       # Execution template output for LIMIT orders
│
├── tests/
│   ├── __init__.py
│   └── test_validators.py    # Pytest unit tests for local inputs validation
│
├── cli.py                    # Core application executable (Typer + Rich CLI / Menu)
├── .env.example              # Sample settings config template
├── requirements.txt          # Third-party dependency definitions
├── README.md                 # Production document guide
└── .gitignore                # Git exclusions configuration
```

---

## Installation & Setup

### 1. Prerequisites
- **Python 3.11 or higher** installed on your system.
- Standard internet connection (unrestricted access to Binance API endpoints).

### 2. Clone and Setup Environment
Clone the repository, enter the directory, and prepare your virtual environment:

```bash
# Protip: Setup a clean virtual environment
python -m venv venv
venv\Scripts\activate       # On Windows (cmd/PowerShell)
source venv/bin/activate    # On Unix/macOS
```

### 3. Install Dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Create and Configure Environment Variables
Copy `.env.example` to a new file named `.env`:
```bash
cp .env.example .env
```
Open `.env` in a text editor and fill in your API credentials.

---

## Binance Futures Testnet Account Setup

To test order placement safely without using real money, TradeForge relies on the Binance Futures Testnet environment.

1. Go to the [Binance Futures Testnet Portal](https://testnet.binancefuture.com/).
2. Log in using a standard email, Google account, or Apple account.
3. Once logged in, locate your **API Key** and **Secret Key** in the API Key box on the dashboard (typically located in the middle of the screen).
4. Copy those keys and paste them into your local `.env` file:
   ```env
   BINANCE_API_KEY=your_copied_api_key
   BINANCE_API_SECRET=your_copied_secret_key
   ```
5. You can also monitor your simulated USDT balance and open positions on this portal as the bot executes trades!

---

## How to Run TradeForge

TradeForge dynamically adjusts how it runs depending on the arguments you pass to the command line:

### Mode A: Standard Direct CLI Argument Execution
Use direct parameters to quickly place orders without visual dialogs.

#### 1. Place a MARKET BUY Order:
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

#### 2. Place a LIMIT SELL Order:
```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.002 --price 95000
```

#### 3. Place a STOP_LIMIT SELL Order:
```bash
python cli.py --symbol BTCUSDT --side SELL --type STOP_LIMIT --quantity 0.005 --price 93000 --stop-price 94000
```

---

### Mode B: Premium Interactive Dashboard Menu (Bonus Feature)
If you run the CLI with no arguments or pass the `--interactive` flag, TradeForge opens an interactive console interface:

```bash
python cli.py
# OR
python cli.py --interactive
```

**Interactive Highlights:**
1. Automatically pings Binance Futures matching engine to verify testnet latency and connectivity.
2. Prompts you with an elegant list of popular symbol presets (BTCUSDT, ETHUSDT, SOLUSDT) or permits custom typing.
3. Guides you sequentially through choosing Side, Order Type, and Numeric quantities.
4. Renders a glowing **CONFIRM ORDER CARD** illustrating symbols, estimated contract sizes, total trade value, and warning symbols.
5. Runs your order within a visual loading spinner, prints the final execution details inside structured cards, and renders the raw API JSON response for developer reference.

---

## Quality Assurance & Testing

We provide a comprehensive unit testing suite covering parameter sanitation, domain restrictions, positive boundary constraints, and error raising inside `tests/test_validators.py`.

Run tests using `pytest`:
```bash
pytest tests/ -v
```

---

## Robust Error Handling & Logging

### Exceptions Handled
- **`ConfigurationError`:** Raised if the bot detects default placeholders or blank API keys in `.env`.
- **`ValidationError`:** Raised if inputs are malformed (e.g. `BUY` on side is spelled `HOLD`, or price is missing on a `LIMIT` order). This occurs locally **before** contacting Binance, preventing wasted rate-limit consumption.
- **`APIConnectionError`:** Raised if a connection time-out, DNS resolution error, or unreachable network socket is encountered.
- **`APIResponseError`:** Raised if Binance matching engine rejects the request. The client parses the JSON response body and extracts the matching code (e.g., `-2019` for insufficient funds) for a clean explanation.

### Log Outputs
All requests, responses, raw payloads, connection health checks, and full call tracebacks are written securely to:
`logs/trading.log`

The logger utilizes `RotatingFileHandler` configured at 5MB limits and up to 5 automatic backups to guarantee logs never fill local disk space.
