
# from langchain_ollama import ChatOllama
# from prompt import PROMPT


# # Ollama model
# llm = ChatOllama(model='qwen2.5-coder:7b', temperature=0.5)

# msgs = [
#     "EQSIS Intraday : Buy HDFCBANK above 825.3 Target 830.8 Stoploss 820.7. LTP Rs.824.25 Rationale:Breakout",
#     "EQSIS Intraday : Buy RADICO above 4090 Target 4145 Stoploss 4044. LTP Rs.4069.4 Rationale:Breakout",
#     "EQSIS Intraday : Buy ENRIN above 3435 Target 3471 Stoploss 3405. LTP Rs.3420.6 Rationale:Breakout",
#     "EQSIS Intraday Call Update: RADICO Buy recommendation is initiated and active.",
#     "EQSIS Intraday Call Update: HDFCBANK Buy recommendation is initiated and active.",
#     "EQSIS Intraday Call Update: Stoploss triggered for RADICO long position. Exit Now.",
#     "EQSIS Intraday Call Update: Target reached for HDFCBANK long position. Book Profit",
#     "EQSIS Intraday Call Update: Ignore ENRIN Buy recommendation. It is not initiated as of now."
# ]
# import pandas as pd
# from datetime import datetime as dt
# import json

# # ─── Read security mapping ──────────────────────────────────────────────────
# df = pd.read_csv("security_mapping.csv")
# print(f"✅ Loaded {len(df)} securities")

# # ─── Create lookup dict for faster search ──────────────────────────────────
# symbol_to_security = dict(zip(df['SEM_TRADING_SYMBOL'], df['SEM_SMST_SECURITY_ID']))
# print(f"✅ Created lookup for {len(symbol_to_security)} symbols")

# # ─── Process messages ──────────────────────────────────────────────────────
# for msg in msgs:
#     prompt = PROMPT.replace("{message}", msg)  # ✅ FIX: use {message} not message_call
#     start = dt.now()
#     response = llm.invoke(prompt)
    
#     try:
#         signal = json.loads(response.content)
#     except json.JSONDecodeError:
#         print(f"❌ Invalid JSON: {response.content}")
#         continue
    
#     print("\n" + "="*60)
#     print(f"Passed msg : {msg}")
#     print(f"Extracted Signal: {response.content}")
    
#     # ✅ If complete signal has trade and symbol
#     if signal.get('trade') and signal.get('symbol'):
#         symbol = signal['symbol']
        
#         # ✅ Lookup security_id from DataFrame
#         security_id = symbol_to_security.get(symbol)
        
#         if security_id:
#             signal['security_id'] = str(security_id)
#             print(f"✅ Found security_id: {security_id} for symbol: {symbol}")
#         else:
#             print(f"⚠️ Symbol '{symbol}' not found in security mapping")
#             signal['security_id'] = None
    
#     # ✅ Print final signal with security_id
#     print(f"Final Signal: {json.dumps(signal, indent=2)}")
    
#     end = dt.now()
#     print(f"Time taken: {end-start}")
#     print("="*60 + "\n")

test_messages = ["EQSIS Intraday Call Update: Target reached for HDFCBANK long position. Book Profit",
"EQSIS Intraday Call Update: Ignore ENRIN Buy recommendation. It is not initiated as of now.",
"EQSIS Intraday : Buy SWIGGY above 255.5 Target 258.7 Stoploss 252.8. LTP Rs.254.4 Rationale:Breakout",
"EQSIS Intraday Call Update: SWIGGY Buy recommendation is initiated and active.",
"EQSIS Intraday : Buy HCLTECH around 1158 Target 1174 Stoploss 1144. LTP Rs.1158.8 Rationale:Breakout",
"EQSIS Intraday : Buy HCLTECH around 1158 Target 1174 Stoploss 1144. LTP Rs.1158.8 Rationale:Breakout",
"EQSIS Intraday Call Update: HCLTECH Buy recommendation is initiated and active.",
"EQSIS Intraday : Sell RECLTD below 357.5 Target 355 Stoploss 359.5. LTP Rs.358.15 Rationale:Breakout",
"EQSIS Intraday : Sell RECLTD below 357.5 Target 355 Stoploss 359.5. LTP Rs.358.15 Rationale:Breakout",
"EQSIS Intraday Call Update: Target reached for SWIGGY long position. Book Profit",
"EQSIS Intraday Call Update: Exit HCLTECH at current price Rs.1164.6",
"EQSIS Intraday Call Update: RECLTD Sell recommendation is initiated and active.",
"EQSIS Intraday Call Update: Exit RECLTD at current price Rs.356.45",
"EQSIS Intraday : Buy ATGL above 715.2 Target 722.6 Stoploss 709. LTP Rs.713.75 Rationale:Breakout",
"EQSIS Intraday : Buy ATGL above 715.2 Target 722.6 Stoploss 709. LTP Rs.713.75 Rationale:Breakout",
"EQSIS Intraday Call Update: ATGL Buy recommendation is initiated and active.",
"EQSIS Intraday : Sell DRREDDY below 1361 Target 1349 Stoploss 1371. LTP Rs.1366.9 Rationale:Breakout",
"EQSIS Intraday Call Update: Target reached for ATGL long position. Book Profit",
"EQSIS Intraday : Buy HDFCBANK above 825.3 Target 830.8 Stoploss 820.7. LTP Rs.824.25 Rationale:Breakout",
"EQSIS Intraday : Buy HDFCBANK above 825.3 Target 830.8 Stoploss 820.7. LTP Rs.824.25 Rationale:Breakout",
"EQSIS Intraday : Buy RADICO above 4090 Target 4145 Stoploss 4044. LTP Rs.4069.4 Rationale:Breakout",
"EQSIS Intraday : Buy RADICO above 4090 Target 4145 Stoploss 4044. LTP Rs.4069.4 Rationale:Breakout",
"EQSIS Intraday : Buy ENRIN above 3435 Target 3471 Stoploss 3405. LTP Rs.3420.6 Rationale:Breakout",
"EQSIS Intraday : Buy ENRIN above 3435 Target 3471 Stoploss 3405. LTP Rs.3420.6 Rationale:Breakout",
"EQSIS Intraday Call Update: RADICO Buy recommendation is initiated and active.",
"EQSIS Intraday Call Update: HDFCBANK Buy recommendation is initiated and active.",
"EQSIS Intraday Call Update: Stoploss triggered for RADICO long position. Exit"]


import re
import json

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


# ─── TEST WITH YOUR MESSAGES ────────────────────────────────────────────────
if __name__ == "__main__":
    test_messages = test_messages
    
    results = []
    for msg in test_messages:
        result = extract_signal(msg)
        results.append(result)
        print("="*50)
        print(f"📩 {msg}")
        print(f"📊 {json.dumps(result, indent=2)}")
        print("-"*50)
    
    # ─── Summary ──────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print(f"📊 SUMMARY")
    print("="*60)
    
    entries = [r for r in results if r.get('trade') in ['BUY', 'SELL']]
    exits = [r for r in results if r.get('trade') == 'EXIT']
    ignored = [r for r in results if r.get('signal') is False]
    
    print(f"✅ Trade Signals: {len(entries)}")
    print(f"🚪 Exit Signals: {len(exits)}")
    print(f"⏭️ Ignored: {len(ignored)}")
    print("="*60)