import asyncio
import os
import requests
import re
import json
from dotenv import load_dotenv
from rich.console import Console
from telethon import TelegramClient, events
from datetime import datetime
import pandas as pd

load_dotenv()
console = Console()

# ─── Constants ──────────────────────────────────────────────────────────────
BROKER = "DHAN"  # Options: "DHAN", "ZERODHA", "GROWW", etc.
FASTAPI_URL = "http://34.225.241.76:8000"

# ─── Config ──────────────────────────────────────────────────────────────────
API_ID = 12345
API_HASH = '*********'
CHANNEL = '@EQSIS_Alert_Bot'

# ─── Read security mapping ──────────────────────────────────────────────────
df = pd.read_csv("security_mapping.csv")
console.print(f"[green]✅ Loaded {len(df)} securities[/green]")
symbol_to_security = dict(zip(df['SEM_TRADING_SYMBOL'], df['SEM_SMST_SECURITY_ID']))
console.print(f"[green]✅ Created lookup for {len(symbol_to_security)} symbols[/green]")

# ─── Active Trades Dictionary (Duplicate Prevention) ──────────────────────
active_trades = {}

def get_trade_date() -> str:
    """Return current date in DDMM format (e.g., 0907 for 9 July)"""
    return datetime.now().strftime("%d%m")

def log_trade(symbol: str, trade_data: dict) -> None:
    """Log a trade in the active_trades dictionary"""
    trade_date = get_trade_date()
    key = f"{symbol}_{trade_date}"
    active_trades[key] = trade_data
    console.print(f"[green]✅ Trade logged: {key}[/green]")

def is_duplicate(symbol: str) -> bool:
    """Check if a trade already exists for today"""
    trade_date = get_trade_date()
    key = f"{symbol}_{trade_date}"
    
    if key in active_trades:
        console.print(f"[yellow]⚠️ Duplicate found for {symbol}[/yellow]")
        return True
    
    for k, v in active_trades.items():
        if k.startswith(f"{symbol}_") and v.get('trade') == 'EXIT':
            console.print(f"[yellow]⚠️ {symbol} already exited today[/yellow]")
            return True
    
    return False

def remove_trade(symbol: str) -> None:
    """Remove trade from active_trades after exit"""
    trade_date = get_trade_date()
    key = f"{symbol}_{trade_date}"
    if key in active_trades:
        del active_trades[key]
        console.print(f"[dim]🗑️ Removed trade: {key}[/dim]")

# ─── Extract Signal using Regex ──────────────────────────────────────────
def extract_signal(msg: str) -> dict:
    """
    Extract trade signal from EQSIS messages using regex.
    
    Returns:
        Complete signal: {"trade": "BUY/SELL", "symbol": "...", "entry": 0.0, "stop_loss": 0.0, "target": 0.0}
        Exit signal: {"trade": "EXIT", "symbol": "..."}
        Invalid/Update: {"signal": False}
    """
    
    # ─── 1. CHECK FOR EXIT ──────────────────────────────────────────────────
    exit_pattern = r"Exit\s+(\w+)\s+at current price"
    exit_match = re.search(exit_pattern, msg, re.IGNORECASE)
    if exit_match:
        return {
            "trade": "EXIT",
            "symbol": exit_match.group(1).upper()
        }
    
    # ─── 2. CHECK FOR TARGET REACHED / STOPLOSS REACHED ──────────────────
    if any(keyword in msg for keyword in ["Target reached", "Book Profit", "Stoploss reached", "Book Loss"]):
        return {"signal": False}
    
    # ─── 3. CHECK FOR SIGNAL UPDATE (initiated and active) ────────────────
    if "Call Update:" in msg and "recommendation is initiated" in msg:
        return {"signal": False}
    
    # ─── 4. CHECK FOR IGNORE MESSAGES ──────────────────────────────────────
    if "Ignore" in msg or "not initiated" in msg:
        return {"signal": False}
    
    # ─── 5. CHECK FOR NEW SIGNAL ────────────────────────────────────────────
    def clean_price(price_str: str) -> float:
        """Remove extra dots and convert to float"""
        if not price_str:
            return 0.0
        cleaned = re.sub(r'\.+$', '', price_str.strip())
        cleaned = re.sub(r'[^\d.]', '', cleaned)
        return float(cleaned) if cleaned else 0.0
    
    # Pattern: Buy SYMBOL above ENTRY Target TARGET Stoploss SL
    buy_above_pattern = r"Buy\s+(\w+)\s+above\s+([\d.]+)\s+Target\s+([\d.]+)\s+Stoploss\s+([\d.]+)"
    buy_above_match = re.search(buy_above_pattern, msg, re.IGNORECASE)
    
    if buy_above_match:
        return {
            "trade": "BUY",
            "symbol": buy_above_match.group(1).upper(),
            "entry": clean_price(buy_above_match.group(2)),
            "target": clean_price(buy_above_match.group(3)),
            "stop_loss": clean_price(buy_above_match.group(4))
        }
    
    # Pattern: Buy SYMBOL around ENTRY Target TARGET Stoploss SL
    buy_around_pattern = r"Buy\s+(\w+)\s+around\s+([\d.]+)\s+Target\s+([\d.]+)\s+Stoploss\s+([\d.]+)"
    buy_around_match = re.search(buy_around_pattern, msg, re.IGNORECASE)
    
    if buy_around_match:
        return {
            "trade": "BUY",
            "symbol": buy_around_match.group(1).upper(),
            "entry": clean_price(buy_around_match.group(2)),
            "target": clean_price(buy_around_match.group(3)),
            "stop_loss": clean_price(buy_around_match.group(4))
        }
    
    # Pattern: Sell SYMBOL below ENTRY Target TARGET Stoploss SL
    sell_below_pattern = r"Sell\s+(\w+)\s+below\s+([\d.]+)\s+Target\s+([\d.]+)\s+Stoploss\s+([\d.]+)"
    sell_below_match = re.search(sell_below_pattern, msg, re.IGNORECASE)
    
    if sell_below_match:
        return {
            "trade": "SELL",
            "symbol": sell_below_match.group(1).upper(),
            "entry": clean_price(sell_below_match.group(2)),
            "target": clean_price(sell_below_match.group(3)),
            "stop_loss": clean_price(sell_below_match.group(4))
        }
    
    # ─── 6. DEFAULT: INVALID MESSAGE ───────────────────────────────────────
    return {"signal": False}

# ─── Process Signal with Duplicate Prevention ────────────────────────────
def process_signal(signal: dict) -> dict:
    """
    Process trade signal with duplicate prevention and API calls.
    Maintains exact payload structure for both endpoints.
    """
    
    # ─── 1. Check if signal is valid ──────────────────────────────────────
    if signal.get("signal") is False:
        console.print("[red]⏭️ No valid signal[/red]")
        return {"status": "ignored", "reason": "no_signal"}
    
    # ─── 2. Handle EXIT signal ────────────────────────────────────────────
    if signal.get("trade") == "EXIT":
        symbol = signal.get("symbol")
        if not symbol:
            return {"status": "failed", "reason": "no_symbol"}
        
        trade_date = get_trade_date()
        key = f"{symbol}_{trade_date}"
        
        if key not in active_trades:
            console.print(f"[yellow]⚠️ No active trade found for {symbol}[/yellow]")
            return {"status": "failed", "reason": "no_active_trade"}
        
        # ✅ EXACT payload for /trade-exit
        exit_payload = {
            "symbol": symbol,
            "security_id": active_trades[key].get("security_id"),
            "transaction_type": active_trades[key].get("trade", "BUY")
        }
        
        console.print(f"[yellow]🚪 Exiting {symbol}...[/yellow]")
        
        try:
            res = requests.post(
                f"{FASTAPI_URL}/trade-exit",
                json=exit_payload,
                timeout=10
            )
            
            if res.status_code == 200:
                response_data = res.json()
                if response_data.get("status") == "success":
                    remove_trade(symbol)
                    console.print(f"[green]✅ Exited {symbol}[/green]")
                    return {"status": "success", "action": "exit", "symbol": symbol, "response": response_data}
                else:
                    console.print(f"[red]❌ Exit failed: {response_data}[/red]")
                    return {"status": "failed", "action": "exit", "symbol": symbol, "response": response_data}
            else:
                console.print(f"[red]❌ HTTP Error: {res.status_code} {res.text}[/red]")
                return {"status": "failed", "action": "exit", "symbol": symbol, "error": res.text}
                
        except Exception as e:
            console.print(f"[red]❌ Exception: {e}[/red]")
            return {"status": "failed", "action": "exit", "symbol": symbol, "error": str(e)}
    
    # ─── 3. Handle BUY/SELL signal ────────────────────────────────────────
    if signal.get("trade") in ["BUY", "SELL"]:
        symbol = signal.get("symbol")
        if not symbol:
            return {"status": "failed", "reason": "no_symbol"}
        
        # Get security_id from mapping
        security_id = symbol_to_security.get(symbol)
        if not security_id:
            console.print(f"[red]⚠️ Symbol '{symbol}' not found in security mapping[/red]")
            return {"status": "failed", "reason": "symbol_not_found"}
        
        signal['security_id'] = str(security_id)
        
        # Check duplicate
        if is_duplicate(symbol):
            console.print(f"[yellow]⏭️ Duplicate signal for {symbol}, ignoring...[/yellow]")
            return {"status": "ignored", "reason": "duplicate"}
        
        # ✅ EXACT payload for /trade
        trade_payload = {
            "trade": signal["trade"],
            "symbol": signal["symbol"],
            "security_id": signal["security_id"],
            "entry": signal["entry"],
            "stop_loss": signal["stop_loss"],
            "target": signal["target"]
        }
        
        console.print(f"[yellow]📈 Placing {signal['trade']} order for {symbol}...[/yellow]")
        
        try:
            res = requests.post(
                f"{FASTAPI_URL}/trade",
                json=trade_payload,
                timeout=10
            )
            
            if res.status_code == 200:
                response_data = res.json()
                
                if response_data.get("status") == "failed":
                    error_msg = response_data.get("error", "")
                    if "Market is Closed" in error_msg:
                        console.print(f"[red]⚠️ Market closed for {symbol}[/red]")
                        return {"status": "failed", "reason": "market_closed", "response": response_data}
                    else:
                        console.print(f"[red]⚠️ Order failed: {error_msg}[/red]")
                        return {"status": "failed", "reason": "order_failed", "response": response_data}
                
                if response_data.get("status") == "success":
                    trade_data = {
                        "trade": signal["trade"],
                        "symbol": symbol,
                        "security_id": security_id,
                        "entry": signal.get("entry"),
                        "target": signal.get("target"),
                        "stop_loss": signal.get("stop_loss"),
                        "timestamp": datetime.now().isoformat()
                    }
                    log_trade(symbol, trade_data)
                    console.print(f"[green]✅ {signal['trade']} order placed for {symbol}[/green]")
                    return {"status": "success", "action": "entry", "symbol": symbol, "response": response_data}
                else:
                    console.print(f"[red]❌ Unknown response: {response_data}[/red]")
                    return {"status": "failed", "reason": "unknown_response", "response": response_data}
            else:
                console.print(f"[red]❌ HTTP Error: {res.status_code} {res.text}[/red]")
                return {"status": "failed", "reason": "http_error", "status_code": res.status_code}
                
        except Exception as e:
            console.print(f"[red]❌ Exception: {e}[/red]")
            return {"status": "failed", "reason": "exception", "error": str(e)}
    
    # ─── 4. Unknown signal type ────────────────────────────────────────────
    return {"status": "ignored", "reason": "unknown_signal"}

# ─── Telegram Client ───────────────────────────────────────────────────────
client = TelegramClient('session', API_ID, API_HASH)

# ─── Handle Message ────────────────────────────────────────────────────────
async def handle_message(event):
    msg = event.message.text
    console.print(f"[dim]📩 Message: {msg[:80]}...[/dim]")
    
    # ─── Step 1: Extract signal using regex ──────────────────────────────
    signal = extract_signal(msg)
    console.print(f"[dim]Signal: {signal}[/dim]")
    
    # ─── Step 2: Process signal ───────────────────────────────────────────
    result = process_signal(signal)
    
    # ─── Step 3: Log summary ──────────────────────────────────────────────
    if result.get("status") == "success":
        console.print(f"[green]✅ {result['action']} {result['symbol']}[/green]")
    elif result.get("status") == "ignored":
        console.print(f"[yellow]⏭️ {result['reason']}[/yellow]")
    else:
        console.print(f"[red]❌ {result.get('reason', 'unknown')}[/red]")
    
    console.print("━" * 50, style="dim")


# ─── Main Loop with Auto-Reconnect & Retries ──────────────────────────────
MAX_RETRIES = 5
RETRY_DELAY = 10

async def main():
    retry_count = 0
    
    while True:
        try:
            console.print(f"[bold cyan]🚀 Connecting to Telegram...[/bold cyan]")
            
            await client.start()
            console.print(f"[green]✅ Connected! Listening: {CHANNEL}[/green]")
            
            # Reset retry count on success
            retry_count = 0
            
            @client.on(events.NewMessage(chats=CHANNEL))
            async def handler(e):
                await handle_message(e)
            
            await client.run_until_disconnected()
            
            console.print("[yellow]⚠️ Connection lost. Reconnecting...[/yellow]")
            
        except (ConnectionError, TimeoutError, OSError) as e:
            retry_count += 1
            console.print(f"[red]❌ Connection error: {e}[/red]")
            
            if retry_count >= MAX_RETRIES:
                console.print(f"[red]❌ Max retries reached. Waiting {RETRY_DELAY * 3}s...[/red]")
                await asyncio.sleep(RETRY_DELAY * 3)
                retry_count = 0
            else:
                delay = RETRY_DELAY * retry_count
                console.print(f"[yellow]🔄 Retry {retry_count}/{MAX_RETRIES} in {delay}s...[/yellow]")
                await asyncio.sleep(delay)
                
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")
            console.print(f"[yellow]🔄 Retrying in {RETRY_DELAY}s...[/yellow]")
            await asyncio.sleep(RETRY_DELAY)

if __name__ == "__main__":
    console.print("[bold cyan]🚀 Starting bot[/bold cyan]")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("[yellow]⏹️ Bot stopped[/yellow]")