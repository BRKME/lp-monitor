import json
from web3 import Web3
import requests
from datetime import datetime
import time

# Минимальные ABI для Uniswap V3 (общий для Arbitrum/BSC)
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

# Функции для TickMath и LiquidityAmounts (без изменений)
def get_sqrt_ratio_at_tick(tick):
    # ... (твой оригинальный код)
    pass  # Placeholder - вставь полный

def get_amount0_for_liquidity(sqrt_ratio_a, sqrt_ratio_b, liquidity):
    # ... (твой оригинальный)
    pass

def get_amount1_for_liquidity(sqrt_ratio_a, sqrt_ratio_b, liquidity):
    # ... 
    pass

def get_amounts_for_liquidity(sqrt_ratio, sqrt_a, sqrt_b, liquidity):
    # ...
    pass

def get_fee_growth_inside(pool_contract, tick_lower, tick_upper, current_tick, fee_growth_global0, fee_growth_global1):
    # Добавлена задержка перед ticks.call()
    time.sleep(0.2)
    if current_tick >= tick_lower:
        fee_growth_below0 = pool_contract.functions.ticks(tick_lower).call()[2]
        fee_growth_below1 = pool_contract.functions.ticks(tick_lower).call()[3]
    else:
        time.sleep(0.2)
        fee_growth_below0 = fee_growth_global0 - pool_contract.functions.ticks(tick_lower).call()[2]
        fee_growth_below1 = fee_growth_global1 - pool_contract.functions.ticks(tick_lower).call()[3]

    time.sleep(0.2)
    if current_tick < tick_upper:
        fee_growth_above0 = pool_contract.functions.ticks(tick_upper).call()[2]
        fee_growth_above1 = pool_contract.functions.ticks(tick_upper).call()[3]
    else:
        time.sleep(0.2)
        fee_growth_above0 = fee_growth_global0 - pool_contract.functions.ticks(tick_upper).call()[2]
        fee_growth_above1 = fee_growth_global1 - pool_contract.functions.ticks(tick_upper).call()[3]

    fee_growth_inside0 = fee_growth_global0 - fee_growth_below0 - fee_growth_above0
    fee_growth_inside1 = fee_growth_global1 - fee_growth_below1 - fee_growth_above1

    return fee_growth_inside0, fee_growth_inside1

# Конфиг сетей (только Uniswap V3)
chains = {
    'arbitrum': {
        'rpc': 'https://arb1.arbitrum.io/rpc',
        'factory': '0x1F98431c8aD98523631AE4a59f267346ea31F984',
        'position_manager': '0xC36442b4a4522E871399CD717aBDD847Ab11FE88',
        'platform': 'arbitrum-one',
    },
    'bnb': {
        'rpc': 'https://bsc-dataseed.binance.org/',
        'factory': '0x1F98431c8aD98523631AE4a59f267346ea31F984',  # Uniswap V3 Factory on BSC
        'position_manager': '0xC36442b4a4522E871399CD717aBDD847Ab11FE88',  # Uniswap V3 NPM on BSC
        'platform': 'binance-smart-chain',
    }
}

addresses = [
    '0x17e6D71D30d260e30BB7721C63539694aB02b036',
    '0x91dad140AF2800B2D660e530B9F42500Eee474a0',
    '0x4e7240952C21C811d9e1237a328b927685A21418',
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
        resp = requests.get(url).json()
        return resp.get(token_addr.lower(), {}).get('usd', 0)
    except:
        return 0

# Telegram bot config
BOT_TOKEN = '8442392037:AAEiM_b4QfdFLqbmmc1PXNvA99yxmFVLEp8'
CHAT_ID = '350766421'

def send_to_telegram(message):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("Message sent to Telegram successfully.")
        else:
            print(f"Error sending to Telegram: {response.text}")
    except Exception as e:
        print(f"Exception sending to Telegram: {e}")

def monitor_positions():
    output = []
    
    # Заголовок
    days_ru = {
        'Monday': 'понедельник',
        'Tuesday': 'вторник',
        'Wednesday': 'среда',
        'Thursday': 'четверг',
        'Friday': 'пятница',
        'Saturday': 'суббота',
        'Sunday': 'воскресенье'
    }
    day_name = days_ru.get(datetime.now().strftime('%A'), 'день')
    hour = datetime.now().hour
    time_of_day = "утренний" if hour < 12 else "вечерний"
    header = f"Привет сегодня {day_name} твой {time_of_day} LP обзор (Uniswap V3 only)"
    output.append(header)
    
    for chain_name, config in chains.items():
        w3 = Web3(Web3.HTTPProvider(config['rpc']))
        if not w3.is_connected():
            output.append(f"Error connecting to {chain_name}")
            continue
        
        pm_address = w3.to_checksum_address(config['position_manager'])
        factory_address = w3.to_checksum_address(config['factory'])
        
        pm_contract = w3.eth.contract(address=pm_address, abi=POSITION_MANAGER_ABI)
        factory_contract = w3.eth.contract(address=factory_address, abi=FACTORY_ABI)
        
        for owner in addresses:
            short_name = short_names.get(owner.lower(), 'Unknown')
            has_positions = False
            try:
                owner_checksum = w3.to_checksum_address(owner)
                num_pos = pm_contract.functions.balanceOf(owner_checksum).call()
                if num_pos > 0:
                    output.append(f"{short_name} on {chain_name.capitalize()}:")
                    has_positions = True
                for i in range(num_pos):
                    time.sleep(0.5)  # Задержка между позициями
                    token_id = pm_contract.functions.tokenOfOwnerByIndex(owner_checksum, i).call()
                    pos = pm_contract.functions.positions(token_id).call()
                    liquidity = pos[7]
                    if liquidity == 0:
                        continue
                    token0 = pos[2]
                    token1 = pos[3]
                    fee = pos[4]
                    tick_lower = pos[5]
                    tick_upper = pos[6]
                    fee_growth_inside0_last = pos[8]
                    fee_growth_inside1_last = pos[9]
                    tokens_owed0 = pos[10]
                    tokens_owed1 = pos[11]
                    
                    token0_checksum = w3.to_checksum_address(token0)
                    token1_checksum = w3.to_checksum_address(token1)
                    
                    pool_addr = factory_contract.functions.getPool(token0_checksum, token1_checksum, fee).call()
                    if pool_addr == '0x0000000000000000000000000000000000000000':
                        continue
                    
                    pool_addr_checksum = w3.to_checksum_address(pool_addr)
                    pool_contract = w3.eth.contract(address=pool_addr_checksum, abi=POOL_ABI)
                    slot0 = pool_contract.functions.slot0().call()
                    sqrt_price_x96 = slot0[0]
                    current_tick = slot0[1]
                    
                    in_range = tick_lower <= current_tick < tick_upper
                    emoji = '🟢' if in_range else '🔴'
                    
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
                    owed0 = tokens_owed0 / 10 ** dec0
                    owed1 = tokens_owed1 / 10 ** dec1
                    
                    # Расчет accrued fees
                    fee_growth_global0 = pool_contract.functions.feeGrowthGlobal0X128().call()
                    fee_growth_global1 = pool_contract.functions.feeGrowthGlobal1X128().call()
                    fee_growth_inside0, fee_growth_inside1 = get_fee_growth_inside(pool_contract, tick_lower, tick_upper, current_tick, fee_growth_global0, fee_growth_global1)
                    
                    delta_fee0 = fee_growth_inside0 - fee_growth_inside0_last
                    delta_fee1 = fee_growth_inside1 - fee_growth_inside1_last
                    
                    accrued0 = max(0, liquidity * delta_fee0 // (1 << 128)) / 10 ** dec0
                    accrued1 = max(0, liquidity * delta_fee1 // (1 << 128)) / 10 ** dec1
                    
                    uncollected0 = max(0, owed0 + accrued0)
                    uncollected1 = max(0, owed1 + accrued1)
                    
                    price0 = get_token_price(config['platform'], token0)
                    price1 = get_token_price(config['platform'], token1)
                    
                    balance_usd = amount0 * price0 + amount1 * price1 + uncollected0 * price0 + uncollected1 * price1
                    uncollected_fees_usd = uncollected0 * price0 + uncollected1 * price1
                    
                    output.append(f"  Position: {sym0}-{sym1}, (fee {fee/10000}%): {emoji}")
                    output.append(f"  Balance USD: ${balance_usd:.0f}")
                    output.append(f"  My Salary: ${uncollected_fees_usd:.0f}")
                if has_positions:
                    output.append("---")
                time.sleep(3)  # Задержка между адресами
            except Exception as e:
                output.append(f"Error for {short_name} on {chain_name}: {e}")
    
    message_text = "\n".join(output)
    send_to_telegram(message_text)
    print(message_text)

if __name__ == "__main__":
    monitor_positions()
