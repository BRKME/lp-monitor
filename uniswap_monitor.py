#!/usr/bin/env python3
"""
monitor_uniswap_all.py
Монитор Uniswap V3 (Arbitrum) + попытка прочитать Uniswap V4 позиции (BSC).
Подставь свои ключи в переменные конфигурации ниже или используй переменные окружения.

Требования:
pip install web3 requests python-dotenv

Запуск:
python monitor_uniswap_all.py
"""

import os
import time
import math
import json
import requests
from datetime import datetime
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# ----------------- CONFIG -----------------
# Сеть Arbitrum (Uniswap V3)
ARBITRUM_RPC = os.getenv("ARBITRUM_RPC", "https://arb1.arbitrum.io/rpc")
ARBITRUM_POSITION_MANAGER = os.getenv("ARBITRUM_POSITION_MANAGER", "0xC36442b4a4522E871399CD717aBDD847Ab11FE88")
ARBITRUM_FACTORY = os.getenv("ARBITRUM_FACTORY", "0x1F98431c8aD98523631AE4a59f267346ea31F984")
ARBITRUM_PLATFORM = os.getenv("ARBITRUM_PLATFORM", "arbitrum-one")

ARBITRUM_ADDRESSES = [
    "0x17e6D71D30d260e30BB7721C63539694aB02b036",
    "0x91dad140AF2800B2D660e530B9F42500Eee474a0",
    "0x3c2c34B9bB0b00145142FFeE68475E1AC01C92bA",
]

# Сеть BNB (для V4 detection / reading)
BSC_RPC = os.getenv("BSC_RPC", "https://bsc-dataseed.binance.org/")
BSCSCAN_API_KEY = "2U12DECNS5JQPTNP5Y5PC4V5T3J3CVSACV"  # Прямо в код
BNB_ADDRESSES = [
    "0x4e7240952C21C811d9e1237a328b927685A21418",
    "0x5A51f62D86F5CCB8C7470Cea2AC982762049c53c"
]

# Telegram
BOT_TOKEN = "8442392037:AAEiM_b4QfdFLqbmmc1PXNvA99yxmFVLEp8"  # Прямо в код
CHAT_ID = "350766421"  # Прямо в код

# Интервал проверки в секундах
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 60 * 10))  # 10 минут по умолчанию

# CoinGecko rate-limit friendly
COINGECKO_BASE = "https://api.coingecko.com/api/v3"
COINGECKO_SLEEP = 1.1

# ----------------- ABIs (минимальные) -----------------
FACTORY_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "tokenA", "type": "address"},
            {"internalType": "address", "name": "tokenB", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"}
        ],
        "name": "getPool",
        "outputs": [{"internalType": "address", "name": "pool", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]

POOL_ABI = [
    {
        "inputs": [],
        "name": "slot0",
        "outputs": [
            {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
            {"internalType": "int24", "name": "tick", "type": "int24"},
            {"internalType": "uint16", "name": "observationIndex", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"},
            {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"},
            {"internalType": "bool", "name": "unlocked", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {"inputs": [], "name": "liquidity", "outputs": [{"internalType": "uint128", "name": "", "type": "uint128"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "feeGrowthGlobal0X128", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "feeGrowthGlobal1X128", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "int24", "name": "tick", "type": "int24"}],
     "name": "ticks",
     "outputs": [
         {"internalType": "uint128", "name": "liquidityGross", "type": "uint128"},
         {"internalType": "int128", "name": "liquidityNet", "type": "int128"},
         {"internalType": "uint256", "name": "feeGrowthOutside0X128", "type": "uint256"},
         {"internalType": "uint256", "name": "feeGrowthOutside1X128", "type": "uint256"},
         {"internalType": "int56", "name": "tickCumulativeOutside", "type": "int56"},
         {"internalType": "uint160", "name": "secondsPerLiquidityOutsideX128", "type": "uint160"},
         {"internalType": "uint32", "name": "secondsOutside", "type": "uint32"},
         {"internalType": "bool", "name": "initialized", "type": "bool"}
     ], "stateMutability": "view", "type": "function"}
]

POSITION_MANAGER_ABI = [
    {"inputs": [{"internalType":"address","name":"owner","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"balance","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"uint256","name":"index","type":"uint256"}],"name":"tokenOfOwnerByIndex","outputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"positions","outputs":[
        {"internalType":"uint96","name":"nonce","type":"uint96"},
        {"internalType":"address","name":"operator","type":"address"},
        {"internalType":"address","name":"token0","type":"address"},
        {"internalType":"address","name":"token1","type":"address"},
        {"internalType":"uint24","name":"fee","type":"uint24"},
        {"internalType":"int24","name":"tickLower","type":"int24"},
        {"internalType":"int24","name":"tickUpper","type":"int24"},
        {"internalType":"uint128","name":"liquidity","type":"uint128"},
        {"internalType":"uint256","name":"feeGrowthInside0LastX128","type":"uint256"},
        {"internalType":"uint256","name":"feeGrowthInside1LastX128","type":"uint256"},
        {"internalType":"uint128","name":"tokensOwed0","type":"uint128"},
        {"internalType":"uint128","name":"tokensOwed1","type":"uint128"}
    ],"stateMutability":"view","type":"function"}
]

ERC20_ABI = [
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}
]

ERC721_MIN_ABI = [
    {"constant":True, "inputs":[{"name":"owner","type":"address"}], "name":"balanceOf", "outputs":[{"name":"balance","type":"uint256"}], "type":"function"},
    {"constant":True, "inputs":[{"name":"owner","type":"address"},{"name":"index","type":"uint256"}], "name":"tokenOfOwnerByIndex", "outputs":[{"name":"tokenId","type":"uint256"}], "type":"function"},
    {"constant":True, "inputs":[{"name":"tokenId","type":"uint256"}], "name":"positions", "outputs":[{"name":"out","type":"uint256"}], "type":"function"}
]

# ----------------- MATH (V3) -----------------
Q96 = 2 ** 96

def get_sqrt_ratio_at_tick(tick: int) -> int:
    # approximation using float — fine for monitor/alerts
    sqrt_price = math.sqrt((1.0001) ** tick)
    return int(sqrt_price * Q96)

def get_amount0_for_liquidity(sqrt_ratio_ax96, sqrt_ratio_bx96, liquidity):
    sa = sqrt_ratio_ax96
    sb = sqrt_ratio_bx96
    if sa > sb:
        sa, sb = sb, sa
    # amount0 = L * (sb - sa) / (sb * sa) * Q96
    # do integer-ish calc with float fallback
    denom = (sb * sa) / Q96
    if denom == 0:
        return 0
    return int(liquidity * (sb - sa) / denom)

def get_amount1_for_liquidity(sqrt_ratio_ax96, sqrt_ratio_bx96, liquidity):
    sa = sqrt_ratio_ax96
    sb = sqrt_ratio_bx96
    if sa > sb:
        sa, sb = sb, sa
    return int(liquidity * (sb - sa) / Q96)

def get_amounts_for_liquidity(sqrt_price_x96, sqrt_a, sqrt_b, liquidity):
    if sqrt_a > sqrt_b:
        sqrt_a, sqrt_b = sqrt_b, sqrt_a
    if sqrt_price_x96 <= sqrt_a:
        amount0 = get_amount0_for_liquidity(sqrt_a, sqrt_b, liquidity)
        amount1 = 0
    elif sqrt_price_x96 >= sqrt_b:
        amount0 = 0
        amount1 = get_amount1_for_liquidity(sqrt_a, sqrt_b, liquidity)
    else:
        amount0 = get_amount0_for_liquidity(sqrt_price_x96, sqrt_b, liquidity)
        amount1 = get_amount1_for_liquidity(sqrt_a, sqrt_price_x96, liquidity)
    return amount0, amount1

# ----------------- Helpers -----------------
def coingecko_token_price(platform, token_addr):
    """
    platform example: 'arbitrum-one' or 'binance-smart-chain'
    token_addr - checksum or lowercase contract address
    """
    try:
        url = f"{COINGECKO_BASE}/simple/token_price/{platform}?contract_addresses={token_addr}&vs_currencies=usd"
        r = requests.get(url, timeout=10)
        data = r.json()
        time.sleep(COINGECKO_SLEEP)
        return data.get(token_addr.lower(), {}).get("usd", 0)
    except Exception:
        return 0

def send_to_telegram(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram not configured - skipping sending. Message:\n", text[:400])
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": text}
        r = requests.post(url, data=payload, timeout=15)
        if r.status_code != 200:
            print("Telegram send error:", r.status_code, r.text)
    except Exception as e:
        print("Exception sending Telegram:", e)

# ----------------- V3 Monitor (Arbitrum) -----------------
def monitor_v3_arbitrum(w3):
    out_lines = []
    try:
        pm = w3.eth.contract(address=w3.toChecksumAddress(ARBITRUM_POSITION_MANAGER), abi=POSITION_MANAGER_ABI)
        factory = w3.eth.contract(address=w3.toChecksumAddress(ARBITRUM_FACTORY), abi=FACTORY_ABI)
    except Exception as e:
        return [f"Error creating contracts for V3: {e}"]

    out_lines.append(f"--- Uniswap V3 Arbitrum report: {datetime.utcnow().isoformat()}Z ---")
    for owner in ARBITRUM_ADDRESSES:
        try:
            owner_ch = w3.toChecksumAddress(owner)
            balance = pm.functions.balanceOf(owner_ch).call()
            out_lines.append(f"Owner {owner} positions: {balance}")
            for idx in range(balance):
                time.sleep(0.15)
                token_id = pm.functions.tokenOfOwnerByIndex(owner_ch, idx).call()
                pos = pm.functions.positions(token_id).call()
                liquidity = pos[7]
                if liquidity == 0:
                    out_lines.append(f"  tokenId {token_id} — zero liquidity")
                    continue
                token0 = pos[2]; token1 = pos[3]; fee = pos[4]
                tick_lower = pos[5]; tick_upper = pos[6]
                feeGrowthInside0Last = pos[8]; feeGrowthInside1Last = pos[9]
                tokensOwed0 = pos[10]; tokensOwed1 = pos[11]

                pool_addr = factory.functions.getPool(w3.toChecksumAddress(token0), w3.toChecksumAddress(token1), fee).call()
                if int(pool_addr, 16) == 0:
                    out_lines.append(f"  tokenId {token_id} — pool not found")
                    continue
                pool = w3.eth.contract(address=w3.toChecksumAddress(pool_addr), abi=POOL_ABI)
                slot0 = pool.functions.slot0().call()
                sqrt_price_x96 = slot0[0]
                current_tick = slot0[1]

                sqrt_lower = get_sqrt_ratio_at_tick(tick_lower)
                sqrt_upper = get_sqrt_ratio_at_tick(tick_upper)
                amount0_raw, amount1_raw = get_amounts_for_liquidity(sqrt_price_x96, sqrt_lower, sqrt_upper, liquidity)

                token0c = w3.eth.contract(address=w3.toChecksumAddress(token0), abi=ERC20_ABI)
                token1c = w3.eth.contract(address=w3.toChecksumAddress(token1), abi=ERC20_ABI)
                try:
                    dec0 = token0c.functions.decimals().call()
                except:
                    dec0 = 18
                try:
                    dec1 = token1c.functions.decimals().call()
                except:
                    dec1 = 18
                try:
                    sym0 = token0c.functions.symbol().call()
                except:
                    sym0 = token0[:6]
                try:
                    sym1 = token1c.functions.symbol().call()
                except:
                    sym1 = token1[:6]

                amount0 = abs(amount0_raw) / (10 ** dec0)
                amount1 = abs(amount1_raw) / (10 ** dec1)
                owed0 = tokensOwed0 / (10 ** dec0)
                owed1 = tokensOwed1 / (10 ** dec1)

                # fee accrual (approx)
                try:
                    fee_growth_global0 = pool.functions.feeGrowthGlobal0X128().call()
                    fee_growth_global1 = pool.functions.feeGrowthGlobal1X128().call()
                    tick_lower_struct = pool.functions.ticks(tick_lower).call()
                    tick_upper_struct = pool.functions.ticks(tick_upper).call()
                    feeGrowthBelow0 = tick_lower_struct[2] if current_tick >= tick_lower else fee_growth_global0 - tick_lower_struct[2]
                    feeGrowthBelow1 = tick_lower_struct[3] if current_tick >= tick_lower else fee_growth_global1 - tick_lower_struct[3]
                    feeGrowthAbove0 = tick_upper_struct[2] if current_tick < tick_upper else fee_growth_global0 - tick_upper_struct[2]
                    feeGrowthAbove1 = tick_upper_struct[3] if current_tick < tick_upper else fee_growth_global1 - tick_upper_struct[3]
                    feeGrowthInside0 = fee_growth_global0 - feeGrowthBelow0 - feeGrowthAbove0
                    feeGrowthInside1 = fee_growth_global1 - feeGrowthBelow1 - feeGrowthAbove1
                    delta_fee0 = feeGrowthInside0 - feeGrowthInside0Last
                    delta_fee1 = feeGrowthInside1 - feeGrowthInside1Last
                    accrued0 = max(0, (liquidity * delta_fee0) // (1 << 128)) / (10 ** dec0)
                    accrued1 = max(0, (liquidity * delta_fee1) // (1 << 128)) / (10 ** dec1)
                except Exception:
                    accrued0 = 0
                    accrued1 = 0

                uncollected0 = max(0, owed0 + accrued0)
                uncollected1 = max(0, owed1 + accrued1)

                price0 = coingecko_token_price(ARBITRUM_PLATFORM, token0)
                price1 = coingecko_token_price(ARBITRUM_PLATFORM, token1)
                balance_usd = amount0 * price0 + amount1 * price1 + uncollected0 * price0 + uncollected1 * price1
                fees_usd = uncollected0 * price0 + uncollected1 * price1

                in_range = (tick_lower <= current_tick < tick_upper)
                emoji = "🟢" if in_range else "🔴"

                out_lines.append(f"  [{token_id}] {sym0}/{sym1} fee:{fee/10000:.4f}% tick:{current_tick} range[{tick_lower},{tick_upper}] {emoji}")
                out_lines.append(f"    LP: {amount0:.6f} {sym0} + {amount1:.6f} {sym1} | uncollected fees: {uncollected0:.6f} {sym0}, {uncollected1:.6f} {sym1}")
                out_lines.append(f"    Est USD: ${balance_usd:.2f} (fees ${fees_usd:.2f})")
        except Exception as e:
            out_lines.append(f"Error for owner {owner}: {e}")
    return out_lines

# ----------------- V4 detection + read (BSC) -----------------
BSCSCAN_BASE = "https://api.bscscan.com/api"

def bscscan_call(module, action, params):
    base = {"module": module, "action": action, "apikey": BSCSCAN_API_KEY}
    base.update(params)
    r = requests.get(BSCSCAN_BASE, params=base, timeout=15)
    time.sleep(0.2)
    try:
        return r.json()
    except:
        return {}

def find_erc721_contracts_for_owner(owner, page=1, offset=200):
    params = {"address": owner, "page": page, "offset": offset, "sort": "desc"}
    res = bscscan_call("account", "tokennfttx", params)
    items = []
    if res.get("status") != "1":
        return items
    seen = {}
    for tx in res.get("result", []):
        ca = tx.get("contractAddress")
        if not ca:
            continue
        if ca.lower() not in seen:
            seen[ca.lower()] = True
            items.append({
                "contract": ca,
                "tokenId": tx.get("tokenID"),
                "timestamp": tx.get("timeStamp"),
                "name": tx.get("tokenName"),
                "symbol": tx.get("tokenSymbol")
            })
    return items

def try_position_manager_bsc(w3_bsc, contract_addr, owner):
    try:
        c = w3_bsc.eth.contract(address=w3_bsc.toChecksumAddress(contract_addr), abi=ERC721_MIN_ABI)
        balance = c.functions.balanceOf(w3_bsc.toChecksumAddress(owner)).call()
        if balance == 0:
            return None
        token_id = None
        try:
            token_id = c.functions.tokenOfOwnerByIndex(w3_bsc.toChecksumAddress(owner), 0).call()
        except Exception:
            # maybe contract not enumerable, try to fetch from BscScan tx list (not implemented here)
            token_id = None
        pos_raw = None
        try:
            if token_id is not None:
                pos_raw = c.functions.positions(token_id).call()
            else:
                # try positions on tokenId from tx list might be available elsewhere
                pass
        except Exception:
            pos_raw = None
        return {"contract": contract_addr, "balance": balance, "tokenId": token_id, "positions_raw": pos_raw}
    except Exception:
        return None

def monitor_v4_bsc():
    out = []
    w3_bsc = Web3(Web3.HTTPProvider(BSC_RPC))
    if not w3_bsc.isConnected():
        out.append("Cannot connect to BSC RPC")
        return out
    out.append(f"--- Uniswap V4 (BSC) probe: {datetime.utcnow().isoformat()}Z ---")
    for owner in BNB_ADDRESSES:
        out.append(f"Owner {owner} scan (BscScan tokesnfttx)...")
        try:
            candidates = find_erc721_contracts_for_owner(owner)
            if not candidates:
                out.append("  No ERC721 transfers found (BscScan).")
                continue
            for cand in candidates[:30]:
                ca = cand["contract"]
                out.append(f"  Candidate: {ca} name:{cand.get('name')} sym:{cand.get('symbol')}")
                res = try_position_manager_bsc(w3_bsc, ca, owner)
                if res:
                    out.append(f"    Callable: balance={res['balance']} tokenId={res['tokenId']} positions_raw={str(res['positions_raw'])[:200]}")
                    # If positions_raw is not None and contains recognizable fields, you can extend parsing here.
                else:
                    out.append("    Not callable as PositionManager or zero balance.")
                time.sleep(0.15)
        except Exception as e:
            out.append(f"  Error scanning owner {owner}: {e}")
    out.append("Note: V4 PositionManager ABI can differ — если нашёл контракт с токенами, пришли мне его адрес и сырой positions() output, я помогу распарсить.")
    return out

# ----------------- Main loop -----------------
def build_report():
    report_lines = []
    # prepare web3
    w3_arb = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
    if not w3_arb.isConnected():
        report_lines.append("Cannot connect to Arbitrum RPC")
    else:
        try:
            v3_lines = monitor_v3_arbitrum(w3_arb)
            report_lines.extend(v3_lines)
        except Exception as e:
            report_lines.append(f"Exception in V3 monitor: {e}")

    # V4 / BSC probe
    try:
        v4_lines = monitor_v4_bsc()
        report_lines.extend(v4_lines)
    except Exception as e:
        report_lines.append(f"Exception in V4 probe: {e}")

    return "\n".join(report_lines)

def main_loop():
    while True:
        report = build_report()
        # shorten message if too long for Telegram (4096 chars limit)
        if len(report) > 3800:
            # send as file + summary
            summary = report[:3800] + "\n\n[Truncated full report saved locally]"
            send_to_telegram(summary)
            # also save to local file
            filename = f"uniswap_report_{int(time.time())}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(report)
            # optionally send the file via Telegram (not implemented here) or upload elsewhere
            print("Full report saved to", filename)
        else:
            send_to_telegram(report)
        print(f"[{datetime.utcnow().isoformat()}Z] Report sent. Sleeping {CHECK_INTERVAL}s.")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    # If you want single run, replace main_loop() with print(build_report())
    print("Starting monitor (single run). To loop continuously, call main_loop().")
    # single run:
    print(build_report())
    # Uncomment next line to enable continuous monitoring:
    # main_loop()
