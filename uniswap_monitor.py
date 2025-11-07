import json
from web3 import Web3
import requests
from datetime import datetime
import time

# === V3 ABI (без изменений) ===
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
    {
        "inputs": [],
        "name": "liquidity",
        "outputs": [{"internalType": "uint128", "name": "", "type": "uint128"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "feeGrowthGlobal0X128",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "feeGrowthGlobal1X128",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "int24", "name": "tick", "type": "int24"}],
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
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

POSITION_MANAGER_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "balance", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "owner", "type": "address"},
            {"internalType": "uint256", "name": "index", "type": "uint256"}
        ],
        "name": "tokenOfOwnerByIndex",
        "outputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "positions",
        "outputs": [
            {"internalType": "uint96", "name": "nonce", "type": "uint96"},
            {"internalType": "address", "name": "operator", "type": "address"},
            {"internalType": "address", "name": "token0", "type": "address"},
            {"internalType": "address", "name": "token1", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"},
            {"internalType": "int24", "name": "tickLower", "type": "int24"},
            {"internalType": "int24", "name": "tickUpper", "type": "int24"},
            {"internalType": "uint128", "name": "liquidity", "type": "uint128"},
            {"internalType": "uint256", "name": "feeGrowthInside0LastX128", "type": "uint256"},
            {"internalType": "uint256", "name": "feeGrowthInside1LastX128", "type": "uint256"},
            {"internalType": "uint128", "name": "tokensOwed0", "type": "uint128"},
            {"internalType": "uint128", "name": "tokensOwed1", "type": "uint128"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# === V4 ABI для PancakeSwap V4 на BNB ===
# V4 использует PoolManager + CLPositionManager
POOL_MANAGER_V4_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "poolId", "type": "bytes32"}
        ],
        "name": "getSlot0",
        "outputs": [
            {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
            {"internalType": "int24", "name": "tick", "type": "int24"},
            {"internalType": "uint24", "name": "protocolFee", "type": "uint24"},
            {"internalType": "uint24", "name": "lpFee", "type": "uint24"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "poolId", "type": "bytes32"}
        ],
        "name": "getLiquidity",
        "outputs": [{"internalType": "uint128", "name": "liquidity", "type": "uint128"}],
        "stateMutability": "view",
        "type": "function"
    }
]

CL_POSITION_MANAGER_V4_ABI = [
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "positions",
        "outputs": [
            {"internalType": "bytes32", "name": "poolId", "type": "bytes32"},
            {"internalType": "address", "name": "currency0", "type": "address"},
            {"internalType": "address", "name": "currency1", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"},
            {"internalType": "int24", "name": "tickLower", "type": "int24"},
            {"internalType": "int24", "name": "tickUpper", "type": "int24"},
            {"internalType": "uint128", "name": "liquidity", "type": "uint128"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "owner", "type": "address"},
            {"internalType": "uint256", "name": "index", "type": "uint256"}
        ],
        "name": "tokenOfOwnerByIndex",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    }
]

# === TickMath functions (без изменений) ===
def get_sqrt_ratio_at_tick(tick):
    MAX_TICK = 887272
    abs_tick = abs(tick)
    if abs_tick > MAX_TICK:
        raise ValueError("Tick out of range")
    ratio = 0xfffcb933bd6fad37aa2d162d1a594001 if (abs_tick & 0x1) != 0 else 0x100000000000000000000000000000000
    if (abs_tick & 0x2) != 0:
        ratio = (ratio * 0xfff97272373d413259a46990580e213a) >> 128
    if (abs_tick & 0x4) != 0:
        ratio = (ratio * 0xfff2e50f5f656932ef12357cf3c7fdcc) >> 128
    if (abs_tick & 0x8) != 0:
        ratio = (ratio * 0xffe5caca7e10e4e61c3624eaa0941cd0) >> 128
    if (abs_tick & 0x10) != 0:
        ratio = (ratio * 0xffcb9843d60f6159c9db58835c926644) >> 128
    if (abs_tick & 0x20) != 0:
        ratio = (ratio * 0xff973b41fa98c081472e6896dfb254c0) >> 128
    if (abs_tick & 0x40) != 0:
        ratio = (ratio * 0xff2ea16466c96a3843ec78b326b52861) >> 128
    if (abs_tick & 0x80) != 0:
        ratio = (ratio * 0xfe5dee046a99a2a811c461f1969c3053) >> 128
    if (abs_tick & 0x100) != 0:
        ratio = (ratio * 0xfcbe86c7900a88aedcffc83b479aa3a4) >> 128
    if (abs_tick & 0x200) != 0:
        ratio = (ratio * 0xf987a7253ac413176f2b074cf7815e54) >> 128
    if (abs_tick & 0x400) != 0:
        ratio = (ratio * 0xf3392b0822b70005940c7a398e4b70f3) >> 128
    if (abs_tick & 0x800) != 0:
        ratio = (ratio * 0xe7159475a2c29b7443b29c7fa6e889d9) >> 128
    if (abs_tick & 0x1000) != 0:
        ratio = (ratio * 0xd097f3bdfd2022b8845ad8f792aa5825) >> 128
    if (abs_tick & 0x2000) != 0:
        ratio = (ratio * 0xa9f746462d870fdf8a65dc1f90e061e5) >> 128
    if (abs_tick & 0x4000) != 0:
        ratio = (ratio * 0x70d869a156d2a1b890bb3df62baf32f7) >> 128
    if (abs_tick & 0x8000) != 0:
        ratio = (ratio * 0x31be135f97d08fd981231505542fcfa6) >> 128
    if (abs_tick & 0x10000) != 0:
        ratio = (ratio * 0x9aa508b5b7a84e1c677de54f3e99bc9) >> 128
    if (abs_tick & 0x20000) != 0:
        ratio = (ratio * 0x5d6af8dedb81196699c329225ee604) >> 128
    if (abs_tick & 0x40000) != 0:
        ratio = (ratio * 0x2216e584f5fa1ea926041bedfe98) >> 128
    if (abs_tick & 0x80000) != 0:
        ratio = (ratio * 0x48a170391f7dc42444e8fa2) >> 128

    if tick > 0:
        ratio = ((1 << 256) - 1) // ratio

    sqrt_price_x96 = (ratio >> 32) + (0 if ratio % (1 << 32) == 0 else 1)
    return sqrt_price_x96

def get_amount0_for_liquidity(sqrt_ratio_a, sqrt_ratio_b, liquidity):
    if sqrt_ratio_a > sqrt_ratio_b:
        sqrt_ratio_a, sqrt_ratio_b = sqrt_ratio_b, sqrt_ratio_a
    return (((liquidity << 96) * (sqrt_ratio_b - sqrt_ratio_a)) // sqrt_ratio_b) // sqrt_ratio_a

def get_amount1_for_liquidity(sqrt_ratio_a, sqrt_ratio_b, liquidity):
    if sqrt_ratio_a > sqrt_ratio_b:
        sqrt_ratio_a, sqrt_ratio_b = sqrt_ratio_b, sqrt_ratio_a
    return liquidity * (sqrt_ratio_b - sqrt_ratio_a) // (1 << 96)

def get_amounts_for_liquidity(sqrt_ratio, sqrt_a, sqrt_b, liquidity):
    if sqrt_a > sqrt_b:
        sqrt_a, sqrt_b = sqrt_b, sqrt_a

    if sqrt_ratio <= sqrt_a:
        return get_amount0_for_liquidity(sqrt_a, sqrt_b, liquidity), 0
    elif sqrt_ratio < sqrt_b:
        amount0 = get_amount0_for_liquidity(sqrt_ratio, sqrt_b, liquidity)
        amount1 = get_amount1_for_liquidity(sqrt_a, sqrt_ratio, liquidity)
        return amount0, amount1
    else:
        return 0, get_amount1_for_liquidity(sqrt_a, sqrt_b, liquidity)

def get_fee_growth_inside(pool_contract, tick_lower, tick_upper, current_tick, fee_growth_global0, fee_growth_global1):
    if current_tick >= tick_lower:
        fee_growth_below0 = pool_contract.functions.ticks(tick_lower).call()[2]
        fee_growth_below1 = pool_contract.functions.ticks(tick_lower).call()[3]
    else:
        fee_growth_below0 = fee_growth_global0 - pool_contract.functions.ticks(tick_lower).call()[2]
        fee_growth_below1 = fee_growth_global1 - pool_contract.functions.ticks(tick_lower).call()[3]

    if current_tick < tick_upper:
        fee_growth_above0 = pool_contract.functions.ticks(tick_upper).call()[2]
        fee_growth_above1 = pool_contract.functions.ticks(tick_upper).call()[3]
    else:
        fee_growth_above0 = fee_growth_global0 - pool_contract.functions.ticks(tick_upper).call()[2]
        fee_growth_above1 = fee_growth_global1 - pool_contract.functions.ticks(tick_upper).call()[3]

    fee_growth_inside0 = fee_growth_global0 - fee_growth_below0 - fee_growth_above0
    fee_growth_inside1 = fee_growth_global1 - fee_growth_below1 - fee_growth_above1

    return fee_growth_inside0, fee_growth_inside1

# === Конфиг сетей ===
chains = {
    'arbitrum': {
        'rpc': 'https://arb1.arbitrum.io/rpc',
        'factory': '0x1F98431c8aD98523631AE4a59f267346ea31F984',
        'position_manager': '0xC36442b4a4522E871399CD717aBDD847Ab11FE88',
        'platform': 'arbitrum-one',
        'version': 'v3'
    },
    'bnb_v3': {
        'rpc': 'https://bsc-dataseed.binance.org/',
        'factory': '0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865',  # PancakeSwap V3 Factory
        'position_manager': '0x46A15B0b27311cedF172AB29E4f4766fbE7F4364',  # V3 Position Manager
        'platform': 'binance-smart-chain',
        'version': 'v3'
    },
    'bnb_v4': {
        'rpc': 'https://bsc-dataseed.binance.org/',
        'pool_manager': '0x969D90aC74A1a5228b66440f8C8326a8dA47A5F9',  # PoolManager V4
        'position_manager': '0xF78031CBCA409F2FB6876BDFDBc1b2df24cF9bEf',  # CLPositionManager V4
        'platform': 'binance-smart-chain',
        'version': 'v4'
    }
}

addresses = [
    '0x17e6D71D30d260e30BB7721C63539694aB02b036',
    '0x91dad140AF2800B2D660e530B9F42500Eee474a0',
    '0x4e7240952C21C811d9e1237a328b927685a21418',
    '0x3c2c34B9bB0b00145142FFeE68475E1AC01C92bA',
    '0x5A51f62D86F5CCB8C7470Cea2AC982762049c53c'
]

short_names = {
    '0x17e6d71d30d260e30bb7721c63539694ab02b036': '1F_MMW',
    '0x91dad140af2800b2d660e530b9f42500eee474a0': '2F_MMS',
    '0x4e7240952c21c811d9e1237a328b927685a21418': '3F_BNB',
    '0x3c2c34b9bb0b00145142ffee68475e1ac01c92ba': '4F_Exodus',
    '0x5a51f62d86f5ccb8c7470cea2ac982762049c53c': '5F_BNB'
}

def get_token_price(platform, token_addr):
    url = f'https://api.coingecko.com/api/v3/simple/token_price/{platform}?contract_addresses={token_addr}&vs_currencies=usd'
    try:
        resp = requests.get(url, timeout=10).json()
        return resp.get(token_addr.lower(), {}).get('usd', 0)
    except:
        return 0

# Telegram config
BOT_TOKEN = '8442392037:AAEiM_b4QfdFLqbmmc1PXNvA99yxmFVLEp8'
CHAT_ID = '350766421'

def send_to_telegram(message):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
    }
    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Сообщение отправлено в Telegram")
        else:
            print(f"❌ Ошибка Telegram: {response.text}")
    except Exception as e:
        print(f"❌ Исключение Telegram: {e}")

def process_v3_positions(w3, config, owner, short_name, output):
    """Обработка V3 позиций"""
    try:
        pm_address = w3.to_checksum_address(config['position_manager'])
        factory_address = w3.to_checksum_address(config['factory'])
        
        pm_contract = w3.eth.contract(address=pm_address, abi=POSITION_MANAGER_ABI)
        factory_contract = w3.eth.contract(address=factory_address, abi=FACTORY_ABI)
        
        owner_checksum = w3.to_checksum_address(owner)
        num_pos = pm_contract.functions.balanceOf(owner_checksum).call()
        
        if num_pos == 0:
            return False
        
        has_positions = False
        for i in range(num_pos):
            time.sleep(0.5)
            token_id = pm_contract.functions.tokenOfOwnerByIndex(owner_checksum, i).call()
            pos = pm_contract.functions.positions(token_id).call()
            liquidity = pos[7]
            
            if liquidity == 0:
                continue
                
            has_positions = True
            token0, token1, fee = pos[2], pos[3], pos[4]
            tick_lower, tick_upper = pos[5], pos[6]
            
            token0_checksum = w3.to_checksum_address(token0)
            token1_checksum = w3.to_checksum_address(token1)
            
            pool_addr = factory_contract.functions.getPool(token0_checksum, token1_checksum, fee).call()
            if pool_addr == '0x0000000000000000000000000000000000000000':
                continue
            
            pool_contract = w3.eth.contract(address=w3.to_checksum_address(pool_addr), abi=POOL_ABI)
            slot0 = pool_contract.functions.slot0().call()
            current_tick = slot0[1]
            
            in_range = tick_lower <= current_tick < tick_upper
            emoji = '🟢' if in_range else '🔴'
            
            sqrt_price_x96 = slot0[0]
            sqrt_lower = get_sqrt_ratio_at_tick(tick_lower)
            sqrt_upper = get_sqrt_ratio_at_tick(tick_upper)
            
            amount0, amount1 = get_amounts_for_liquidity(sqrt_price_x96, sqrt_lower, sqrt_upper, liquidity)
            
            token0_contract = w3.eth.contract(token0_checksum, abi=ERC20_ABI)
            token1_contract = w3.eth.contract(token1_checksum, abi=ERC20_ABI)
            dec0 = token0_contract.functions.decimals().call()
            dec1 = token1_contract.functions.decimals().call()
            sym0 = token0_contract.functions.symbol().call()
            sym1 = token1_contract.functions.symbol().call()
            
            amount0 = abs(amount0) / 10 ** dec0
            amount1 = abs(amount1) / 10 ** dec1
            
            # Расчет uncollected fees (упрощенная версия)
            tokens_owed0 = pos[10] / 10 ** dec0
            tokens_owed1 = pos[11] / 10 ** dec1
            
            price0 = get_token_price(config['platform'], token0.lower())
            price1 = get_token_price(config['platform'], token1.lower())
            
            balance_usd = amount0 * price0 + amount1 * price1
            fees_usd = tokens_owed0 * price0 + tokens_owed1 * price1
            
            output.append(f"  Position: {sym0}-{sym1} (fee {fee/10000}%): {emoji}")
            output.append(f"  Balance USD: ${balance_usd:.0f}")
            output.append(f"  My Salary: ${fees_usd:.0f}")
        
        return has_positions
    except Exception as e:
        output.append(f"  ❌ Ошибка V3: {e}")
        return False

def process_v4_positions(w3, config, owner, short_name, output):
    """Обработка V4 позиций (PancakeSwap V4)"""
    try:
        pm_address = w3.to_checksum_address(config['position_manager'])
        pool_manager_address = w3.to_checksum_address(config['pool_manager'])
        
        pm_contract = w3.eth.contract(address=pm_address, abi=CL_POSITION_MANAGER_V4_ABI)
        pool_manager_contract = w3.eth.contract(address=pool_manager_address, abi=POOL_MANAGER_V4_ABI)
        
        owner_checksum = w3.to_checksum_address(owner)
        num_pos = pm_contract.functions.balanceOf(owner_checksum).call()
        
        if num_pos == 0:
            return False
        
        has_positions = False
        for i in range(num_pos):
            time.sleep(0.5)
            token_id = pm_contract.functions.tokenOfOwnerByIndex(owner_checksum, i).call()
            pos = pm_contract.functions.positions(token_id).call()
            
            # V4 structure: poolId, currency0, currency1, fee, tickLower, tickUpper, liquidity
            pool_id, currency0, currency1, fee, tick_lower, tick_upper, liquidity = pos
            
            if liquidity == 0:
                continue
            
            has_positions = True
            
            # Получаем данные пула через PoolManager
            slot0 = pool_manager_contract.functions.getSlot0(pool_id).call()
            sqrt_price_x96, current_tick = slot0[0], slot0[1]
            
            in_range = tick_lower <= current_tick < tick_upper
            emoji = '🟢' if in_range else '🔴'
            
            sqrt_lower = get_sqrt_ratio_at_tick(tick_lower)
            sqrt_upper = get_sqrt_ratio_at_tick(tick_upper)
            
            amount0, amount1 = get_amounts_for_liquidity(sqrt_price_x96, sqrt_lower, sqrt_upper, liquidity)
            
            currency0_checksum = w3.to_checksum_address(currency0)
            currency1_checksum = w3.to_checksum_address(currency1)
            
            token0_contract = w3.eth.contract(currency0_checksum, abi=ERC20_ABI)
            token1_contract = w3.eth.contract(currency1_checksum, abi=ERC20_ABI)
            dec0 = token0_contract.functions.decimals().call()
            dec1 = token1_contract.functions.decimals().call()
            sym0 = token0_contract.functions.symbol().call()
            sym1 = token1_contract.functions.symbol().call()
            
            amount0 = abs(amount0) / 10 ** dec0
            amount1 = abs(amount1) / 10 ** dec1
            
            price0 = get_token_price(config['platform'], currency0.lower())
            price1 = get_token_price(config['platform'], currency1.lower())
            
            balance_usd = amount0 * price0 + amount1 * price1
            
            output.append(f"  Position V4: {sym0}-{sym1} (fee {fee/10000}%): {emoji}")
            output.append(f"  Balance USD: ${balance_usd:.0f}")
            output.append(f"  My Salary: $0 (V4 fees not implemented)")  # V4 fees требуют сложной логики
        
        return has_positions
    except Exception as e:
        output.append(f"  ❌ Ошибка V4: {e}")
        import traceback
        traceback.print_exc()
        return False

def monitor_positions():
    output = []
    
    # Заголовок
    days_ru = {
        'Monday': 'понедельник', 'Tuesday': 'вторник', 'Wednesday': 'среда',
        'Thursday': 'четверг', 'Friday': 'пятница', 'Saturday': 'суббота', 'Sunday': 'воскресенье'
    }
    day_name = days_ru.get(datetime.now().strftime('%A'), 'день')
    hour = datetime.now().hour
    time_of_day = "утренний" if hour < 12 else "вечерний"
    header = f"Привет сегодня {day_name} твой {time_of_day} LP обзор"
    output.append(header)
    
    for chain_name, config in chains.items():
        w3 = Web3(Web3.HTTPProvider(config['r
