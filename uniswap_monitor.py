import json
from web3 import Web3
import requests
from datetime import datetime
import time

# Конфигурация
ARBITRUM_RPC = "https://arb1.arbitrum.io/rpc"
BSC_RPC = "https://bsc-dataseed.binance.org/"
TELEGRAM_BOT_TOKEN = "8442392037:AAEiM_b4QfdFLqbmmc1PXNvA99yxmFVLEp8"
TELEGRAM_CHAT_ID = "350766421"

# Контракты Uniswap V3
UNISWAP_V3_FACTORY_ARBITRUM = "0x1F98431c8aD98523631AE4a59f267346ea31F984"
NONFUNGIBLE_POSITION_MANAGER_ARBITRUM = "0xC36442b4a4522E871399CD717aBDD847Ab11FE88"

# Контракты PancakeSwap V3 (BSC)
PANCAKE_V3_FACTORY_BSC = "0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865"
PANCAKE_V3_POSITION_MANAGER_BSC = "0x46A15B0b27311cedF172AB29E4f4766fbE7F4364"

# Ваши кошельки
WALLETS = {
    "MMW": "0x17e6D71D30d260e30BB7721C63539694aB02b036",
    "MMS": "0x91dad140AF2800B2D660e530B9F42500Eee474a0", 
    "MMA": "0x4e7240952C21C811d9e1237a328b927685A21418",
    "EXODUS": "0x3c2c34B9bB0b00145142FFeE68475E1AC01C92bA",
    "MMA Tester": "0x5A51f62D86F5CCB8C7470Cea2AC982762049c53c"
}

# ABI
FACTORY_ABI_V3 = [
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

POOL_ABI_V3 = [
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
    }
]

POSITION_MANAGER_ABI_V3 = [
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
        ratio = (2**256 - 1) // ratio
    
    return ratio // (2 ** 32)

def get_token_info(web3, token_address):
    """Получить информацию о токене"""
    try:
        token_contract = web3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=ERC20_ABI
        )
        symbol = token_contract.functions.symbol().call()
        decimals = token_contract.functions.decimals().call()
        return symbol, decimals
    except:
        return "UNKNOWN", 18

def get_pool_info(web3, factory_address, token0, token1, fee):
    """Получить информацию о пуле"""
    try:
        factory = web3.eth.contract(
            address=Web3.to_checksum_address(factory_address),
            abi=FACTORY_ABI_V3
        )
        pool_address = factory.functions.getPool(
            Web3.to_checksum_address(token0),
            Web3.to_checksum_address(token1),
            fee
        ).call()
        
        if pool_address == "0x0000000000000000000000000000000000000000":
            return None
        
        pool = web3.eth.contract(
            address=Web3.to_checksum_address(pool_address),
            abi=POOL_ABI_V3
        )
        
        slot0 = pool.functions.slot0().call()
        liquidity = pool.functions.liquidity().call()
        
        return {
            'address': pool_address,
            'sqrtPriceX96': slot0[0],
            'tick': slot0[1],
            'liquidity': liquidity
        }
    except Exception as e:
        print(f"❌ Ошибка получения информации о пуле: {e}")
        return None

def get_position_info(web3, position_manager, token_id):
    """Получить информацию о позиции"""
    try:
        position_manager_contract = web3.eth.contract(
            address=Web3.to_checksum_address(position_manager),
            abi=POSITION_MANAGER_ABI_V3
        )
        
        position = position_manager_contract.functions.positions(token_id).call()
        
        return {
            'token0': position[2],
            'token1': position[3],
            'fee': position[4],
            'tickLower': position[5],
            'tickUpper': position[6],
            'liquidity': position[7]
        }
    except Exception as e:
        print(f"❌ Ошибка получения информации о позиции: {e}")
        return None

def calculate_position_value(position_info, pool_info, token0_decimals, token1_decimals):
    """Рассчитать стоимость позиции"""
    try:
        tick_lower = position_info['tickLower']
        tick_upper = position_info['tickUpper']
        liquidity = position_info['liquidity']
        current_tick = pool_info['tick']
        sqrt_price_x96 = pool_info['sqrtPriceX96']
        
        sqrt_ratio_a = get_sqrt_ratio_at_tick(tick_lower)
        sqrt_ratio_b = get_sqrt_ratio_at_tick(tick_upper)
        sqrt_price = sqrt_price_x96 / (2 ** 96)
        
        # Упрощенный расчет стоимости
        if current_tick < tick_lower:
            # Только token0
            amount0 = liquidity * (sqrt_ratio_b - sqrt_ratio_a) / (sqrt_ratio_a * sqrt_ratio_b)
            amount1 = 0
        elif current_tick >= tick_upper:
            # Только token1
            amount0 = 0
            amount1 = liquidity * (sqrt_ratio_b - sqrt_ratio_a)
        else:
            # Оба токена
            amount0 = liquidity * (sqrt_ratio_b - sqrt_price) / (sqrt_price * sqrt_ratio_b)
            amount1 = liquidity * (sqrt_price - sqrt_ratio_a)
        
        # Приведение к правильным decimal
        amount0_adjusted = amount0 / (10 ** token0_decimals)
        amount1_adjusted = amount1 / (10 ** token1_decimals)
        
        return amount0_adjusted, amount1_adjusted
    except Exception as e:
        print(f"❌ Ошибка расчета стоимости позиции: {e}")
        return 0, 0

def send_telegram_message(message):
    """Отправить сообщение в Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("✅ Сообщение отправлено в Telegram")
            return True
        else:
            print(f"❌ Ошибка отправки в Telegram: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка отправки в Telegram: {e}")
        return False

def monitor_wallet_positions(wallet_address, wallet_name, networks):
    """Мониторинг позиций для одного кошелька"""
    wallet_positions = []
    
    for network in networks:
        print(f"🔍 Проверяем {network['name']} для {wallet_name}...")
        
        web3 = Web3(Web3.HTTPProvider(network['rpc']))
        if not web3.is_connected():
            print(f"❌ Не удалось подключиться к {network['name']}")
            continue
        
        # Получаем количество позиций
        position_manager = web3.eth.contract(
            address=Web3.to_checksum_address(network['position_manager']),
            abi=POSITION_MANAGER_ABI_V3
        )
        
        try:
            balance = position_manager.functions.balanceOf(
                Web3.to_checksum_address(wallet_address)
            ).call()
            
            print(f"📊 Найдено {balance} позиций в {network['name']} для {wallet_name}")
            
            for i in range(balance):
                try:
                    token_id = position_manager.functions.tokenOfOwnerByIndex(
                        Web3.to_checksum_address(wallet_address), i
                    ).call()
                    
                    print(f"🔄 Обрабатываем позицию {token_id}...")
                    
                    position_info = get_position_info(web3, network['position_manager'], token_id)
                    if not position_info:
                        continue
                    
                    pool_info = get_pool_info(
                        web3, 
                        network['factory'],
                        position_info['token0'],
                        position_info['token1'],
                        position_info['fee']
                    )
                    
                    if not pool_info:
                        continue
                    
                    token0_symbol, token0_decimals = get_token_info(web3, position_info['token0'])
                    token1_symbol, token1_decimals = get_token_info(web3, position_info['token1'])
                    
                    amount0, amount1 = calculate_position_value(
                        position_info, pool_info, token0_decimals, token1_decimals
                    )
                    
                    position_data = {
                        'wallet_name': wallet_name,
                        'wallet_address': wallet_address,
                        'network': network['name'],
                        'token_id': token_id,
                        'pair': f"{token0_symbol}/{token1_symbol}",
                        'amount0': amount0,
                        'amount1': amount1,
                        'liquidity': position_info['liquidity'],
                        'fee_tier': position_info['fee'] / 10000
                    }
                    
                    wallet_positions.append(position_data)
                    print(f"✅ Позиция {token_id} обработана")
                    
                except Exception as e:
                    print(f"❌ Ошибка обработки позиции {i} в {network['name']}: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ Ошибка получения баланса в {network['name']}: {e}")
            continue
    
    return wallet_positions

def main():
    # Конфигурация сетей
    NETWORKS = [
        {
            'name': 'Arbitrum',
            'rpc': ARBITRUM_RPC,
            'factory': UNISWAP_V3_FACTORY_ARBITRUM,
            'position_manager': NONFUNGIBLE_POSITION_MANAGER_ARBITRUM
        },
        {
            'name': 'BSC',
            'rpc': BSC_RPC,
            'factory': PANCAKE_V3_FACTORY_BSC,
            'position_manager': PANCAKE_V3_POSITION_MANAGER_BSC
        }
    ]
    
    print("🚀 Запуск монитора LP позиций для всех кошельков...")
    print(f"📊 Всего кошельков: {len(WALLETS)}")
    print(f"🤖 Telegram бот: {TELEGRAM_BOT_TOKEN}")
    print(f"💬 Chat ID: {TELEGRAM_CHAT_ID}")
    
    # Проверка подключения к Telegram
    test_message = "🤖 Бот LP монитора запущен и работает!\n📊 Мониторинг 5 кошельков..."
    if send_telegram_message(test_message):
        print("✅ Тестовое сообщение отправлено успешно")
    else:
        print("❌ Не удалось отправить тестовое сообщение")
    
    all_positions = []
    total_wallets_with_positions = 0
    
    # Мониторинг всех кошельков
    for wallet_name, wallet_address in WALLETS.items():
        print(f"\n🎯 Проверяем кошелек: {wallet_name}")
        print(f"📍 Адрес: {wallet_address}")
        
        wallet_positions = monitor_wallet_positions(wallet_address, wallet_name, NETWORKS)
        
        if wallet_positions:
            all_positions.extend(wallet_positions)
            total_wallets_with_positions += 1
            print(f"✅ Найдено {len(wallet_positions)} позиций в кошельке {wallet_name}")
        else:
            print(f"ℹ️ В кошельке {wallet_name} позиций не найдено")
    
    # Формирование отчета
    if all_positions:
        message = "💰 <b>ОТЧЕТ ПО LP ПОЗИЦИЯМ</b>\n\n"
        message += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        message += f"👛 Кошельков с позициями: {total_wallets_with_positions}/{len(WALLETS)}\n"
        message += f"📈 Всего позиций: {len(all_positions)}\n\n"
        
        total_global_value = 0
        
        # Группируем по кошелькам
        wallets_summary = {}
        for pos in all_positions:
            wallet_key = pos['wallet_name']
            if wallet_key not in wallets_summary:
                wallets_summary[wallet_key] = {
                    'positions': [],
                    'total_value': 0
                }
            
            value_estimate = pos['amount0'] + pos['amount1']
            wallets_summary[wallet_key]['positions'].append(pos)
            wallets_summary[wallet_key]['total_value'] += value_estimate
            total_global_value += value_estimate
        
        # Формируем сообщение по кошелькам
        for wallet_name, wallet_data in wallets_summary.items():
            message += f"👛 <b>{wallet_name}</b>\n"
            message += f"💵 Стоимость: ${wallet_data['total_value']:.2f}\n"
            message += f"📊 Позиций: {len(wallet_data['positions'])}\n"
            
            for pos in wallet_data['positions']:
                message += f"  └ {pos['network']} | {pos['pair']} | ID: {pos['token_id']}\n"
            
            message += "\n"
        
        message += f"💎 <b>ОБЩАЯ СТОИМОСТЬ: ${total_global_value:.2f}</b>\n"
        message += f"🏦 <b>Всего кошельков: {len(WALLETS)}</b>"
        
        # Отправка в Telegram
        send_telegram_message(message)
        
        print(f"\n✅ Отчет отправлен! Всего позиций: {len(all_positions)}")
        print(f"💰 Общая стоимость: ${total_global_value:.2f}")
        
    else:
        message = "❌ <b>LP ПОЗИЦИИ НЕ НАЙДЕНЫ</b>\n\n"
        message += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        message += f"👛 Проверено кошельков: {len(WALLETS)}\n"
        message += "ℹ️ На указанных кошельках не найдено LP позиций в Uniswap V3/PancakeSwap V3"
        
        send_telegram_message(message)
        print("❌ LP позиции не найдены на всех кошельках")

if __name__ == "__main__":
    main()
