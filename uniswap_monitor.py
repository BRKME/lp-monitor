import json
from web3 import Web3
import requests
from datetime import datetime
import time

# Минимальные ABI для Uniswap V3 (общий для Arbitrum/BSC)
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

# ABI for V4 PoolManager (BNB)
POOL_MANAGER_ABI_V4 = [
    {
        "inputs": [{"internalType": "bytes32", "name": "poolId", "type": "bytes32"}],
        "name": "getSlot0",
        "outputs": [
            {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
            {"internalType": "int24", "name": "tick", "type": "int24"},
            {"internalType": "uint8", "name": "protocolFee", "type": "uint8"},
            {"internalType": "uint8", "name": "lpFee", "type": "uint8"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "poolId", "type": "bytes32"}],
        "name": "getLiquidity",
        "outputs": [{"internalType": "uint128", "name": "", "type": "uint128"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "poolId", "type": "bytes32"}],
        "name": "getFeeGrowthGlobal0X128",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "poolId", "type": "bytes32"}],
        "name": "getFeeGrowthGlobal1X128",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "poolId", "type": "bytes32"},
            {"internalType": "int24", "name": "tick", "type": "int24"}
        ],
        "name": "getTickInfo",
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

POSITION_MANAGER_ABI_V4 = [
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
            {"components": [
                {"internalType": "address", "name": "currency0", "type": "address"},
                {"internalType": "address", "name": "currency1", "type": "address"},
                {"internalType": "uint24", "name": "fee", "type": "uint24"},
                {"internalType": "int24", "name": "tickSpacing", "type": "int24"},
                {"internalType": "address", "name": "hooks", "type": "address"}
            ], "internalType": "struct PoolKey", "name": "poolKey", "type": "tuple"},
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

# Функции для TickMath (полный порт из оригинала)
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

    # Округление вверх если нужно
    sqrt_price_x96 = (ratio >> 32) + (0 if ratio % (1 << 32) == 0 else 1)
    return sqrt_price_x96

# Функции для LiquidityAmounts (полный порт)
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

# Функция для расчета feeGrowthInside (V3)
def get_fee_growth_inside(pool_contract, tick_lower, tick_upper, current_tick, fee_growth_global0, fee_growth_global1):
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

# V4 functions
def get_pool_id(w3, pool_key):
    # pool_key = (currency0, currency1, fee, tickSpacing, hooks)
    encoded = w3.codec.encode(['address', 'address', 'uint24', 'int24', 'address'], pool_key)
    return w3.keccak(encoded)

def get_fee_growth_inside_v4(pool_contract, pool_id, tick_lower, tick_upper, current_tick, fee_growth_global0, fee_growth_global1):
    time.sleep(0.2)
    tick_info_lower = pool_contract.functions.getTickInfo(pool_id, tick_lower).call()
    time.sleep(0.2)
    tick_info_upper = pool_contract.functions.getTickInfo(pool_id, tick_upper).call()
    
    fee_growth_below0 = tick_info_lower[2] if current_tick >= tick_lower else fee_growth_global0 - tick_info_lower[2]
    fee_growth_below1 = tick_info_lower[3] if current_tick >= tick_lower else fee_growth_global1 - tick_info_lower[3]
    
    fee_growth_above0 = tick_info_upper[2] if current_tick < tick_upper else fee_growth_global0 - tick_info_upper[2]
    fee_growth_above1 = tick_info_upper[3] if current_tick < tick_upper else fee_growth_global1 - tick_info_upper[3]
    
    fee_growth_inside0 = fee_growth_global0 - fee_growth_below0 - fee_growth_above0
    fee_growth_inside1 = fee_growth_global1 - fee_growth_below1 - fee_growth_above1
    
    return fee_growth_inside0, fee_growth_inside1

# Конфиг сетей
chains = {
    'arbitrum': {
        'rpc': 'https://arb1.arbitrum.io/rpc',
        'factory': '0x1F98431c8aD98523631AE4a59f267346ea31F984',
        'position_manager': '0xC36442b4a4522E871399CD717aBDD847Ab11FE88',
        'platform': 'arbitrum-one',
        'version': 'v3'
    },
    'bnb': {
        'rpc': 'https://bsc-dataseed.binance.org/',
        'pool_manager': '0x28e2ea090877bf75740558f6bfb36a5ffee9e9df',
        'position_manager': '0x7a4a5c919ae2541aed11041a1aeee68f1287f95b',
        'platform': 'binance-smart-chain',
        'version': 'v4'
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
    '0x5a51f62d86f5ccb8c747
