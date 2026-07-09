import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from rich.console import Console

console = Console()

# Config
API_ID = 37079063
API_HASH = '3936d3b05c17ced6d29da7c814358426'
CHANNEL = '@SAMARTHZURALE_52'

# Config
API_ID = 37079063
API_HASH = '3936d3b05c17ced6d29da7c814358426'
CHANNEL = '@EQSIS_Alert_Bot'

# ✅ APNI SESSION STRING YAHAN PASTE KARO (jo abhi nikali thi)
SESSION_STRING = "1BVtsOLwBu6Yj8UctlblFhnPbF_9MsQxuRL3l4wQXzNNzwGwMGXMQmVRVzK-OBndMhYmJuwiKaChTBpRZVpC0vCyCyIkDd0_JI2Hoi5cvP8D2XDFT2jAlTblZBygTjRtITAJR331AuxoW3QHlYh3FIoWrJHnM0LCPiGJNfR_Ltx3v9W_EaOTbyZ_a_GgRZWpg9QZbyDDfqZpfK0SxRcLVGZyBwLKnjdhdffW4WPswAskLsM-nwNF6njLPxFSFlwrLxaUvN1lR6KWxuk2pkhijBs6ItyUERjJqU3ALVTOs7ONVLFFniB-mlTF9c7JkS8bCU2_clm4p5lrkfAnfBqUx67aCpZdFVGw="

PROMPT = """You are a trading assistant. You will receive a -----  message_call. ------ from a Telegram channel. Your task is to analyze the message and determine if it contains a trade signal. If it does, you should extract the relevant information and provide it in a structured format. If it does not contain a trade signal, you should respond with "No trade signal found."""

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

async def handle_message(event):
    msg = event.message.text
    prompt = PROMPT.replace("message_call", msg)
    print(f"[bold yellow]Message received:[/bold yellow] {prompt}")

async def main():
    await client.start()
    console.print(f"[green]✅ Listening: {CHANNEL}[/green]\n")
    @client.on(events.NewMessage(chats=CHANNEL))
    async def handler(e):
        await handle_message(e)
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())





# python3 -c "
# import boto3
# s3 = boto3.client('s3')
# s3.download_file('tradebot01', 'trade-agent/test.py', 'test.py')
# print('✅ Downloaded successfully!')
# "





{"trade": "BUY","symbol": "HDFCBANK","security_id": "1333","entry": 840,"stop_loss": 830,"target": 850}




# Msg:"EQSIS Intraday : Buy SWIGGY above 255.5 Target 258.7 Stoploss 252.8"
# outpu:{"trade": "BUY","symbol": "HDFCBANK", "entry": 840,"stop_loss": 830,"target": 850}

# Msg:"EQSIS Intraday Call Update: SWIGGY Buy recommendation is initiated and active."
# outpu:{'signal': False}

# Msg:"EQSIS Intraday Call Update: Target reached for SWIGGY long position. Book Profit"
# outpu:{'signal': False}

# Msg:"EQSIS Intraday : SELL RECL above 255.5 Target 258.7 Stoploss 252.8"
# outpu:{"trade": "BUY","symbol": "HDFCBANK","entry": 840,"stop_loss": 830,"target": 850}

# Msg:"EQSIS Intraday Call Update: RECL Sell recommendation is initiated and active."
# outpu:{'signal': False}

# Msg:"EQSIS Intraday Call Update: Target reached for RECL long position. Book Profit"
# outpu:{'signal': False}

# Msg:"EQSIS Intraday Call Update: Stoploss reached for HDFCBANK short position. Book Loss"
# outpu:{'signal': False}

# Msg:"EQSIS Intraday Call Update: Exit HCLTECH at current price Rs.1164.6"
# outpu:{"trade": "EXIT","symbol": "HDFCBANK"}




["EQSIS Intraday Call Update: Target reached for HDFCBANK long position. Book Profit",

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




