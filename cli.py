"""
TradeForge CLI - Command Line Interface and Interactive Terminal.
Built with Typer and Rich to deliver an exceptional, premium user experience.
"""

from typing import Any, Dict, Optional
import sys
import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.status import Status
from rich.pretty import Pretty
from rich.prompt import Prompt, Confirm, FloatPrompt

from bot.config import settings
from bot.exceptions import TradeForgeError, ValidationError, APIResponseError, APIConnectionError, ConfigurationError
from bot.logging_config import logger
from bot.client import BinanceFuturesClient
from bot.orders import OrderManager, OrderRequest, OrderResponse

app = typer.Typer(
    name="TradeForge",
    help="Enterprise-grade Binance Futures Testnet Trading Bot CLI",
    add_completion=False,
)
console = Console()


def display_welcome_banner() -> None:
    """Renders a beautiful, modern banner for the interactive terminal."""
    banner_text = Text()
    banner_text.append("^ TRADEFORGE TERMINAL ^\n", style="bold cyan")
    banner_text.append("Binance Futures USDT-M Testnet client", style="italic dim white")
    
    panel = Panel(
        banner_text,
        border_style="cyan",
        expand=False,
        padding=(1, 5),
        title="[bold magenta]v1.0.0[/bold magenta]",
        title_align="right",
    )
    console.print(panel)


def display_error(title: str, message: str) -> None:
    """Renders an error message in a styled crimson panel."""
    err_text = Text()
    err_text.append(f"[X] {message}", style="bold red")
    panel = Panel(
        err_text,
        border_style="red",
        title=f"[bold white]{title}[/bold white]",
        expand=False,
        padding=(1, 3),
    )
    console.print(panel)


def display_order_response_card(response: OrderResponse, title: str = "ORDER RECEIPT") -> None:
    """Renders a beautiful grid details panel displaying the order execution results."""
    # Status coloring logic
    status_colors = {
        "FILLED": "bold green",
        "NEW": "bold cyan",
        "PARTIALLY_FILLED": "bold yellow",
        "CANCELED": "bold red",
        "REJECTED": "bold red",
        "EXPIRED": "bold red",
    }
    status_str = response.status.upper()
    status_style = status_colors.get(status_str, "bold white")
    
    grid = Table.grid(expand=False, padding=(0, 2))
    grid.add_column(style="bold dim white", justify="right")
    grid.add_column(style="bold white", justify="left")
    
    grid.add_row("Symbol:", response.symbol)
    grid.add_row("Side:", f"[bold green]BUY[/bold green]" if response.side == "BUY" else f"[bold red]SELL[/bold red]")
    grid.add_row("Type:", response.order_type)
    grid.add_row("Order ID:", str(response.order_id))
    grid.add_row("Client Ref:", response.client_order_id)
    grid.add_row("Status:", f"[{status_style}]{status_str}[/{status_style}]")
    
    # Quantities and Prices
    grid.add_row("Executed Qty:", f"{response.executed_qty:.4f}")
    grid.add_row("Average Fill Price:", f"${response.avg_price:,.4f}" if response.avg_price > 0 else "N/A")
    
    if response.limit_price:
        grid.add_row("Limit Price:", f"${response.limit_price:,.4f}")
    if response.stop_price:
        grid.add_row("Stop Price:", f"${response.stop_price:,.4f}")
        
    # Render final card
    panel = Panel(
        grid,
        title=f"[bold green][OK] {title}[/bold green]",
        border_style="green",
        expand=False,
        padding=(1, 4),
    )
    console.print(panel)


def run_interactive_menu(manager: OrderManager) -> None:
    """Runs the step-by-step interactive command-line onboarding flow."""
    display_welcome_banner()
    
    # 1. Connection Health Check
    rprint("\n[dim cyan]* Initiating API health-check connection...[/dim cyan]")
    with console.status("[bold cyan]Pinging Binance Futures Testnet matching engine...", spinner="dots") as status:
        connected = manager.client.ping()
        
    if connected:
        rprint("[bold green][OK] API Connection: ONLINE (demo-fapi.binance.com)[/bold green]\n")
    else:
        rprint("[bold yellow][!] API Connection: UNSTABLE (Unable to ping testnet)[/bold yellow]")
        rprint("[yellow]Please check your internet connection. Proceeding...[/yellow]\n")

    # 2. Select Symbol
    table = Table(title="Select Symbol", border_style="dim", box=None, show_header=True)
    table.add_column("Key", style="bold cyan", justify="center")
    table.add_column("Symbol Pair", style="white")
    table.add_row("1", "BTCUSDT (Bitcoin / Tether)")
    table.add_row("2", "ETHUSDT (Ethereum / Tether)")
    table.add_row("3", "SOLUSDT (Solana / Tether)")
    table.add_row("4", "Custom Symbol")
    console.print(table)
    
    symbol_choice = Prompt.ask("Choose a symbol option", choices=["1", "2", "3", "4"], default="1")
    if symbol_choice == "1":
        symbol = "BTCUSDT"
    elif symbol_choice == "2":
        symbol = "ETHUSDT"
    elif symbol_choice == "3":
        symbol = "SOLUSDT"
    else:
        symbol = Prompt.ask("Enter custom trading symbol (e.g. BNBUSDT, DOGEUSDT)")
        
    # 3. Select Side
    console.print("\n[bold]Select Side:[/bold]")
    side = Prompt.ask("Order Side", choices=["BUY", "SELL"], default="BUY").upper()
    
    # 4. Select Order Type
    console.print("\n[bold]Select Order Type:[/bold]")
    order_type = Prompt.ask("Order Type", choices=["MARKET", "LIMIT", "STOP_LIMIT"], default="MARKET").upper()
    
    # 5. Select Quantity
    console.print("")
    quantity = FloatPrompt.ask(f"Enter Order Quantity for {symbol} (e.g. 0.001)")
    
    # 6. Select Prices
    price = None
    stop_price = None
    if order_type in ("LIMIT", "STOP_LIMIT"):
        price = FloatPrompt.ask(f"Enter Limit Price for {symbol} ($)")
        
    if order_type == "STOP_LIMIT":
        stop_price = FloatPrompt.ask(f"Enter Activation Stop Price for {symbol} ($)")

    # 7. Parameter validation using business logic
    try:
        req = manager.prepare_request(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price
        )
    except ValidationError as val_err:
        display_error("Validation Failure", val_err.message)
        sys.exit(1)
        
    # 8. Render Confirmation Card
    confirm_grid = Table.grid(expand=False, padding=(0, 2))
    confirm_grid.add_column(style="bold dim white", justify="right")
    confirm_grid.add_column(style="bold white", justify="left")
    
    confirm_grid.add_row("Symbol:", req.symbol)
    confirm_grid.add_row("Side:", "[bold green]BUY[/bold green]" if req.side == "BUY" else "[bold red]SELL[/bold red]")
    confirm_grid.add_row("Type:", req.order_type)
    confirm_grid.add_row("Quantity:", f"{req.quantity}")
    if req.price:
        confirm_grid.add_row("Limit Price:", f"${req.price:,.4f}")
    if req.stop_price:
        confirm_grid.add_row("Stop Price:", f"${req.stop_price:,.4f}")
        
    if req.price:
        est_val = req.quantity * req.price
        confirm_grid.add_row("Estimated Value:", f"${est_val:,.2f} USDT")
        
    confirm_panel = Panel(
        confirm_grid,
        title="[bold yellow]^ CONFIRM ORDER EXECUTION ^[/bold yellow]",
        border_style="yellow",
        expand=False,
        padding=(1, 4),
    )
    console.print("\n")
    console.print(confirm_panel)
    
    confirmed = Confirm.ask("Do you want to dispatch this order to Binance Futures Testnet?", default=True)
    if not confirmed:
        rprint("\n[bold yellow]Order aborted by user.[/bold yellow]")
        sys.exit(0)
        
    # 9. Dispatch Request
    rprint("\n[dim cyan]* Dispatching order to Binance Futures Testnet...[/dim cyan]")
    try:
        with console.status("[bold green]Executing matching engine order...", spinner="dots") as status:
            res = manager.place_order(req)
            
        rprint("\n")
        display_order_response_card(res, title="INTERACTIVE ORDER COMPLETED")
        
        # Output the highlighted JSON block
        console.print("\n[bold dim white]--- [Raw API JSON Response] ---[/bold dim white]")
        console.print(Pretty(res.raw_response, expand=False, max_depth=2))
        
    except APIResponseError as resp_err:
        display_error("Binance Matching Engine Error", resp_err.message)
    except APIConnectionError as conn_err:
        display_error("Network Connectivity Failure", conn_err.message)
    except TradeForgeError as general_err:
        display_error("Execution Failure", general_err.message)
    except Exception as exc:
        display_error("Unexpected Exception", str(exc))


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    symbol: Optional[str] = typer.Option(None, "--symbol", "-s", help="Trading pair symbol (e.g. BTCUSDT)"),
    side: Optional[str] = typer.Option(None, "--side", "-d", help="Order side: BUY or SELL"),
    order_type: Optional[str] = typer.Option(None, "--type", "-t", help="Order type: MARKET, LIMIT, STOP_LIMIT"),
    quantity: Optional[float] = typer.Option(None, "--quantity", "-q", help="Order quantity"),
    price: Optional[float] = typer.Option(None, "--price", "-p", help="Price (required for LIMIT & STOP_LIMIT)"),
    stop_price: Optional[float] = typer.Option(None, "--stop-price", "-x", help="Stop activation price (required for STOP_LIMIT)"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Launch the gorgeous interactive menu terminal"),
) -> None:
    """
    TradeForge CLI Entrypoint.
    If no arguments are provided, automatically launches the premium interactive menu.
    """
    # 1. Settings validation (checks API Key availability)
    try:
        settings.validate()
    except ConfigurationError as config_err:
        display_error("Configuration Error", config_err.message)
        sys.exit(1)

    client = BinanceFuturesClient()
    manager = OrderManager(client=client)

    # If --interactive is set or NO argument values are supplied, default to interactive shell
    is_direct_run = any(v is not None for v in (symbol, side, order_type, quantity))
    
    if interactive or not is_direct_run:
        run_interactive_menu(manager)
        return

    # Direct Command Mode validation
    assert symbol is not None
    assert side is not None
    assert order_type is not None
    assert quantity is not None

    rprint(
        f"[cyan]>> Preparing Direct Order:[/cyan] "
        f"[bold white]{side} {quantity} {symbol} {order_type}[/bold white]"
    )

    try:
        # Validate CLI parameters
        req = manager.prepare_request(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )
        
        # Place order
        rprint("[cyan]>> Submitting signed API payload...[/cyan]")
        res = manager.place_order(req)
        
        rprint("\n")
        display_order_response_card(res, title="CLI ORDER PLACED SUCCESSFULLY")
        
        # Output the highlighted JSON block
        console.print("\n[bold dim white]--- [Raw API JSON Response] ---[/bold dim white]")
        console.print(Pretty(res.raw_response, expand=False))
        
    except ValidationError as val_err:
        display_error("Validation Failure", val_err.message)
        sys.exit(1)
    except APIResponseError as resp_err:
        display_error("Binance Matching Engine Refusal", resp_err.message)
        sys.exit(1)
    except APIConnectionError as conn_err:
        display_error("Network Connectivity Failure", conn_err.message)
        sys.exit(1)
    except TradeForgeError as general_err:
        display_error("Execution Failure", general_err.message)
        sys.exit(1)
    except Exception as exc:
        display_error("Unexpected Exception", str(exc))
        sys.exit(1)


if __name__ == "__main__":
    app()
