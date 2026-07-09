from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from dhanhq import dhanhq, DhanContext
from dhanhq import SuperOrder
import math
import traceback
import logging
import json
import boto3
import requests
from datetime import datetime, timedelta, timezone
import time
import os
from dotenv import load_dotenv

load_dotenv()

# ─── Logging Setup ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ─── Configuration ───────────────────────────────────────────────────────────
DHAN_CLIENT_ID = os.getenv("DHAN_CLIENT_ID")
DHAN_ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN")
RENEW_TOKEN_URL = "https://api.dhan.co/v2/RenewToken"
TOKEN_EXPIRY_HOURS = int(os.getenv("TOKEN_EXPIRY_HOURS", 10))

S3_BUCKET = os.getenv("S3_BUCKET", "tradebot01")
S3_KEY = os.getenv("S3_KEY", "dhan/token_store.json")

PER_TRADE_AMOUNT = int(os.getenv("PER_TRADE_AMOUNT", 10000))
MARGIN_BUFFER = int(os.getenv("MARGIN_BUFFER", 1000))

app = FastAPI(title="Dhan Trade Bot", version="2.0.0")
s3_client = boto3.client('s3')


# ─── Token Manager ──────────────────────────────────────────────────────────
def read_token_from_s3():
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
        return json.loads(response["Body"].read().decode("utf-8"))
    except:
        return {}

def write_token_to_s3(token_data):
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=S3_KEY,
            Body=json.dumps(token_data, indent=2),
            ContentType="application/json"
        )
        logger.info("✅ Token saved to S3")
    except Exception as e:
        logger.error(f"Error writing token to S3: {e}")
        raise

def renew_dhan_token(current_token):
    logger.info("🔄 Renewing Dhan token...")
    headers = {
        "access-token": current_token,
        "dhanClientId": DHAN_CLIENT_ID,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(RENEW_TOKEN_URL, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        new_token = data.get("accessToken")
        
        if not new_token:
            raise Exception("No access token in response")
        
        token_store = {
            "accessToken": new_token,
            "dhanClientId": data.get("dhanClientId", DHAN_CLIENT_ID),
            "expiry": (datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS)).isoformat(),
            "renewedAt": datetime.now(timezone.utc).isoformat()
        }
        
        write_token_to_s3(token_store)
        logger.info(f"✅ Token renewed successfully")
        return new_token
    except Exception as e:
        logger.error(f"Token renewal failed: {e}")
        raise

def get_valid_token():
    token_store = read_token_from_s3()
    
    if not token_store or not token_store.get("accessToken"):
        logger.info("📝 No valid token found, creating new...")
        return renew_dhan_token(DHAN_ACCESS_TOKEN)
    
    try:
        expiry_str = token_store.get("expiry")
        if not expiry_str:
            return renew_dhan_token(token_store.get("accessToken"))
        
        expiry_dt = datetime.fromisoformat(expiry_str)
        current_dt = datetime.now(timezone.utc)
        
        if current_dt > expiry_dt:
            logger.info("⏰ Token expired, renewing...")
            return renew_dhan_token(token_store.get("accessToken"))
        
        remaining = expiry_dt - current_dt
        logger.info(f"✅ Token valid for {remaining.seconds//3600}h {(remaining.seconds%3600)//60}m")
        return token_store["accessToken"]
    except Exception as e:
        logger.error(f"Error checking token expiry: {e}")
        return renew_dhan_token(token_store.get("accessToken"))


# ✅ SIMPLIFIED: Ek hi function sab ke liye
def get_dhan_context():
    """Get DhanContext with valid token"""
    token = get_valid_token()
    return DhanContext(DHAN_CLIENT_ID, token)


# ─── Models ──────────────────────────────────────────────────────────────────
class TradeSignal(BaseModel):
    trade: str
    symbol: str
    security_id: str
    entry: float
    stop_loss: float
    target: float
    
    @validator('trade')
    def validate_trade(cls, v):
        if v.lower() not in ['buy', 'sell']:
            raise ValueError('trade must be "buy" or "sell"')
        return v.lower()
    
    @validator('entry', 'stop_loss', 'target')
    def validate_positive(cls, v):
        if v <= 0:
            raise ValueError(f'Value must be greater than 0: {v}')
        return v
    
# ─── Trade Exit Endpoint (Dhan AI Chatbot Code) ────────────────────────────
class TradeExitRequest(BaseModel):
    symbol: str
    security_id: str
    transaction_type: str  # "BUY" or "SELL"

@app.post("/trade-exit")
def exit_trade(request: TradeExitRequest):
    """
    Exit a trade safely using Dhan AI Chatbot's logic.
    """
    logger.info("="*60)
    logger.info("🚪 EXIT TRADE REQUESTED")
    logger.info("="*60)
    
    try:
        symbol = request.symbol.upper()
        security_id = request.security_id
        transaction_type = request.transaction_type.upper()
        
        logger.info(f"Symbol: {symbol} | SecurityId: {security_id} | Side: {transaction_type}")
        
        # ─── Get Dhan Context ──────────────────────────────────────────────
        dhan_context = get_dhan_context()
        dhan = dhanhq(dhan_context)
        
        # ─── Step 1: Find matching open positions ─────────────────────────
        def get_matching_positions(security_id: str, transaction_type: str) -> list:
            """
            Fetch all open positions matching the given security ID
            and original transaction type.
            """
            try:
                response = dhan.get_positions()
                positions = response.get("data", [])

                matching = [
                    pos for pos in positions
                    if str(pos.get("securityId")) == str(security_id)
                    and pos.get("positionType") == ("LONG" if transaction_type == "BUY" else "SHORT")
                    and pos.get("netQty", 0) != 0
                ]

                logger.info(f"[Positions] Found {len(matching)} matching open position(s) for {symbol}")
                return matching

            except Exception as e:
                logger.error(f"[Error] Failed to fetch positions: {e}")
                return []

        # ─── Step 2: Find matching pending orders ─────────────────────────
        def get_matching_orders(security_id: str, transaction_type: str) -> list:
            """
            Fetch all pending orders matching the given security ID
            and transaction type.
            """
            PENDING_STATUSES = {"PENDING", "TRANSIT", "PART_TRADED"}

            try:
                response = dhan.get_order_list()
                orders = response.get("data", [])

                matching = [
                    order for order in orders
                    if str(order.get("securityId")) == str(security_id)
                    and order.get("transactionType") == transaction_type
                    and order.get("orderStatus", "").upper() in PENDING_STATUSES
                ]

                logger.info(f"[Orders] Found {len(matching)} matching pending order(s) for {symbol}")
                return matching

            except Exception as e:
                logger.error(f"[Error] Failed to fetch orders: {e}")
                return []

        # ─── Step 3: Cancel orders ────────────────────────────────────────
        def cancel_orders(orders: list) -> None:
            """
            Cancel all pending orders matching the given security ID.
            """
            if not orders:
                logger.info("[Cancel] No matching orders to cancel.")
                return

            for order in orders:
                order_id = order.get("orderId")
                logger.info(f"[Cancel] Cancelling OrderId: {order_id} | Status: {order.get('orderStatus')}")

                try:
                    response = dhan.cancel_order(order_id=order_id)
                    logger.info(f"[Cancel] Response: {response}")
                except Exception as e:
                    logger.error(f"[Error] Failed to cancel OrderId {order_id}: {e}")

        # ─── Step 4: Exit positions ───────────────────────────────────────
        def exit_positions(positions: list) -> None:
            """
            Exit all open positions at market price.
            """
            if not positions:
                logger.info("[Exit] No matching positions to exit.")
                return

            for pos in positions:
                security_id    = pos.get("securityId")
                exchange_seg   = pos.get("exchangeSegment")
                net_qty        = abs(int(pos.get("netQty", 0)))
                position_type  = pos.get("positionType")
                product_type   = pos.get("productType", "INTRADAY")

                close_side = "SELL" if position_type == "LONG" else "BUY"

                logger.info(f"[Exit] Placing reverse {close_side} MARKET order | SecurityId: {security_id} | Qty: {net_qty}")

                try:
                    response = dhan.place_order(
                        security_id=str(security_id),
                        exchange_segment=exchange_seg,
                        transaction_type=close_side,
                        quantity=net_qty,
                        order_type="MARKET",
                        product_type=product_type,
                        price=0
                    )
                    logger.info(f"[Exit] Response: {response}")
                except Exception as e:
                    logger.error(f"[Error] Failed to exit position for SecurityId {security_id}: {e}")

        # ─── Main Execution ────────────────────────────────────────────────
        # Step 1 — Find matching open positions
        open_positions = get_matching_positions(security_id, transaction_type)

        # Step 2 — Find matching pending orders
        pending_orders = get_matching_orders(security_id, transaction_type)

        # Step 3 — Cancel pending orders
        cancel_orders(pending_orders)

        # Step 4 — Exit open positions
        exit_positions(open_positions)

        logger.info(f"✅ Exit completed for {symbol}")

        return {
            "status": "success",
            "symbol": symbol,
            "security_id": security_id,
            "positions_exited": len(open_positions),
            "orders_cancelled": len(pending_orders),
            "message": f"Exit completed for {symbol}"
        }

    except Exception as e:
        logger.error(f"❌ Exit failed: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# ─── Trade Endpoint ──────────────────────────────────────────────────────────
@app.post("/trade")
def place_oco_trade(signal: TradeSignal):
    logger.info("="*60)
    logger.info("📩 RECEIVED TRADE SIGNAL")
    logger.info("="*60)
    
    try:
        symbol = signal.symbol.upper()
        security_id = signal.security_id
        trade_type = signal.trade.lower()
        entry = signal.entry
        stop_loss = signal.stop_loss
        target = signal.target
        
        logger.info(f"Symbol: {symbol} (ID: {security_id})")
        logger.info(f"Trade: {trade_type.upper()} | Entry: {entry} | Target: {target} | SL: {stop_loss}")
        
        # ✅ EK HI BAAR CONTEXT LO
        dhan_context = get_dhan_context()
        
        # ✅ SAME CONTEXT SE DONO BANAO
        dhan = dhanhq(dhan_context)
        super_order = SuperOrder(dhan_context)
        
        # Get margin
        logger.info("💰 Fetching margin details...")
        try:
            fund_response = dhan.get_fund_limits()
            logger.info(f"Fund response: {fund_response}")
            
            fund_details = fund_response.get("data", {})
            available_margin = fund_details.get('availableBalance', 0)
            if available_margin == 0:
                available_margin = fund_details.get('availabelBalance', 0)
            logger.info(f"Available margin: {available_margin}")
        except Exception as e:
            logger.error(f"Failed to fetch margin: {e}")
            return {"status": "failed", "error": f"Margin fetch failed: {str(e)}"}
        
        # Calculate quantity
        margin_to_use = available_margin - MARGIN_BUFFER
        logger.info(f"Margin to use: {margin_to_use}")
        
        if margin_to_use < PER_TRADE_AMOUNT:
            return {
                "status": "failed",
                "error": f"Insufficient margin. Available: {margin_to_use}, Required: {PER_TRADE_AMOUNT}"
            }
        
        quantity = math.ceil(PER_TRADE_AMOUNT / entry)
        logger.info(f"💰 Calculated quantity: {quantity}")
        
        if quantity < 1:
            return {"status": "failed", "error": "Insufficient margin for 1 share"}
        
        # Place Super Order
        logger.info("📈 Placing Super Order...")
        transaction_type = 'BUY' if trade_type == 'buy' else 'SELL'
        
        logger.info(f"Transaction: {transaction_type}")
        logger.info(f"Quantity: {quantity}")
        logger.info(f"Entry Price: {entry}")
        logger.info(f"Target Price: {target}")
        logger.info(f"Stop Loss: {stop_loss}")
        
        try:
            # ✅ Sahi tarika

            response = super_order.place_super_order(
                security_id=security_id,
                exchange_segment="NSE_EQ",
                transaction_type=transaction_type,
                quantity=quantity,
                order_type="LIMIT",
                product_type="INTRADAY",          # ✅ Use "MIS" for intraday
                price=entry,
                targetPrice=target,          # ✅ CamelCase
                stopLossPrice=stop_loss,     # ✅ CamelCase
                trailingJump=0.0,
                tag=f"{symbol}-{int(time.time())}"
            )

            logger.info(f"Order response: {response}")
            
            # Agar response mein 'status' key hai aur uski value 'failure' hai
            if isinstance(response, dict) and response.get('status') == 'failure':
                error_msg = response.get('remarks', {})
                error_message = error_msg.get('error_message', 'Unknown error')
                error_code = error_msg.get('error_code', 'Unknown')
                logger.error(f"❌ Order failed: {error_code} - {error_message}")
                return {
                    "status": "failed",
                    "error": error_message,
                    "error_code": error_code,
                    "details": response
                }
            
            logger.info(f"✅ Order placed successfully: {response}")
            
            return {
                "status": "success",
                "symbol": symbol,
                "security_id": security_id,
                "quantity": quantity,
                "entry_price": entry,
                "target_price": target,
                "stop_loss": stop_loss,
                "response": response
            }
            
        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            logger.error(traceback.format_exc())
            return {"status": "failed", "error": f"Order placement failed: {str(e)}"}
        
    except Exception as e:
        logger.error(f"❌ Unhandled error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# ─── Health Check ────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Dhan Trade Bot"
    }


# ─── Token Status ────────────────────────────────────────────────────────────
@app.get("/token_status")
def token_status():
    try:
        token_store = read_token_from_s3()
        if not token_store or not token_store.get("accessToken"):
            return {"status": "no_token", "message": "No token found"}
        
        expiry_str = token_store.get("expiry")
        if not expiry_str:
            return {"status": "no_expiry", "message": "No expiry date"}
        
        expiry_dt = datetime.fromisoformat(expiry_str)
        current_dt = datetime.now(timezone.utc)
        is_valid = current_dt < expiry_dt
        
        return {
            "status": "valid" if is_valid else "expired",
            "expiry": expiry_dt.isoformat(),
            "remaining": str(expiry_dt - current_dt) if is_valid else "expired",
            "renewed_at": token_store.get("renewedAt")
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ─── Manual Token Renew ─────────────────────────────────────────────────────
@app.post("/renew_token")
def renew_token():
    try:
        token_store = read_token_from_s3()
        current_token = token_store.get("accessToken", DHAN_ACCESS_TOKEN)
        new_token = renew_dhan_token(current_token)
        return {
            "status": "success",
            "message": "Token renewed successfully",
            "token_preview": new_token[:20] + "..."
        }
    except Exception as e:
        logger.error(f"Manual token renewal failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── Margin Status ──────────────────────────────────────────────────────────
@app.get("/margin")
def get_margin():
    try:
        dhan_context = get_dhan_context()
        dhan = dhanhq(dhan_context)
        
        fund_response = dhan.get_fund_limits()
        fund_details = fund_response.get("data", {})
        available_margin = fund_details.get('availableBalance', 0)
        if available_margin == 0:
            available_margin = fund_details.get('availabelBalance', 0)
        
        margin_to_use = available_margin - MARGIN_BUFFER
        
        return {
            "status": "success",
            "available_margin": available_margin,
            "margin_buffer": MARGIN_BUFFER,
            "usable_margin": margin_to_use,
            "per_trade_amount": PER_TRADE_AMOUNT,
            "max_trades_possible": math.floor(margin_to_use / PER_TRADE_AMOUNT) if margin_to_use > 0 else 0
        }
    except Exception as e:
        logger.error(f"Failed to fetch margin: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── Order Status ──────────────────────────────────────────────────────────
@app.get("/order_status/{order_id}")
def get_order_status(order_id: str):
    try:
        dhan_context = get_dhan_context()
        dhan = dhanhq(dhan_context)
        status = dhan.get_order_by_id(order_id)
        return {"status": "success", "order_id": order_id, "order_status": status}
    except Exception as e:
        logger.error(f"Failed to fetch order status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    logger.info(f"🚀 Starting Dhan Trade Bot on {host}:{port}")
    uvicorn.run(app, host=host, port=port)