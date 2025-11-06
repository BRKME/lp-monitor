import json
from web3 import Web3
import requests
from datetime import datetime
import time  # Для задержек

# Минимальные ABI для V3 (Arbitrum)
FACTORY_ABI_V3 = [  # ... (твой оригинальный FACTORY_ABI)
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

POOL_ABI_V3 = [  # ... (твой оригинальный POOL_ABI)
    # slot0, liquidity, feeGrowthGlobal0X128, feeGrowthGlobal1X128, ticks
]

POSITION_MANAGER_ABI_V3 = [  # ... (твой оригинальный POSITION_MANAGER_ABI)
    # balanceOf, tokenOfOwnerByIndex, positions (V3 format)
]

# ABI для V4 PoolManager (BNB)
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

# V4 PositionManager ABI (positions returns PoolKey struct)
POSITION_MANAGER_ABI_V4 = [
    # ... (V3-like, but positions includes PoolKey)
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
    },
    # balanceOf and tokenOfOwnerByIndex same as V3
    # ... (добавь из POSITION_MANAGER_ABI_V3)
]

ERC20_ABI = [  # ... (твой оригинальный)
]

# ... (TickMath and LiquidityAmounts functions remain the same)

# Конфиг сетей
chains = {
    'arbitrum': {
        'rpc': 'https://arb1.arbitrum.io/rpc',
        'factory': '0x1F98431c8aD98523631AE4a59f267346ea31F984',  # V3 Factory
        'position_manager': '0xC36442b4a4522E871399CD717aBDD847Ab11FE88',  # V3 NonfungiblePositionManager
        'platform': 'arbitrum-one',
        'version': 'v3'
    },
    'bnb': {
        'rpc': 'https://bsc-dataseed.binance.org/',
        'pool_manager': '0x46a15B0b27311cEdF172AB29E4F4766fBe7f4364',  # PoolManager for V4 (from search)
        'position_manager': '0x55f4c8abA71A1e923edC303eb4fEfF14608cC226',  # CLPositionManager
        'platform': 'binance-smart-chain',
        'version': 'v4'
    }
}

# ... (addresses, short_names, get_token_price, send_to_telegram remain the same)

def encode_pool_key(w3, pool_key):
    # PoolKey: (currency0, currency1, fee, tickSpacing, hooks)
    encoded = w3.codec.encode(['address', 'address', 'uint24', 'int24', 'address'], pool_key)
    return encoded

def get_pool_id(w3, pool_key):
    encoded = encode_pool_key(w3, pool_key)
    return w3.keccak(encoded)

def get_fee_growth_inside_v4(pool_contract, pool_id, tick_lower, tick_upper, current_tick, fee_growth_global0, fee_growth_global1):
    # Use getTickInfo for below and above
    time.sleep(1)  # Delay for rate limit
    tick_info_lower = pool_contract.functions.getTickInfo(pool_id, tick_lower).call()
    time.sleep(1)
    tick_info_upper = pool_contract.functions.getTickInfo(pool_id, tick_upper).call()
    
    fee_growth_below0 = tick_info_lower[2] if current_tick >= tick_lower else fee_growth_global0 - tick_info_lower[2]
    fee_growth_below1 = tick_info_lower[3] if current_tick >= tick_lower else fee_growth_global1 - tick_info_lower[3]
    
    fee_growth_above0 = tick_info_upper[2] if current_tick < tick_upper else fee_growth_global0 - tick_info_upper[2]
    fee_growth_above1 = tick_info_upper[3] if current_tick < tick_upper else fee_growth_global1 - tick_info_upper[3]
    
    fee_growth_inside0 = fee_growth_global0 - fee_growth_below0 - fee_growth_above0
    fee_growth_inside1 = fee_growth_global1 - fee_growth_below1 - fee_growth_above1
    
    return fee_growth_inside0, fee_growth_inside1

def monitor_positions():
    output = []
    
    # Header (same)
    # ...
    
    for chain_name, config in chains.items():
        w3 = Web3(Web3.HTTPProvider(config['rpc']))
        if not w3.is_connected():
            output.append(f"Error connecting to {chain_name}")
            continue
        
        if config.get('version') == 'v3':
            # V3 logic (Arbitrum)
            pm_address = w3.to_checksum_address(config['position_manager'])
            factory_address = w3.to_checksum_address(config['factory'])
            pm_contract = w3.eth.contract(address=pm_address, abi=POSITION_MANAGER_ABI_V3)
            factory_contract = w3.eth.contract(address=factory_address, abi=FACTORY_ABI_V3)
            pool_abi = POOL_ABI_V3
            get_fee_growth_func = get_fee_growth_inside  # V3 func
        else:  # V4 (BNB)
            pm_address = w3.to_checksum_address(config['position_manager'])
            pool_manager_address = w3.to_checksum_address(config['pool_manager'])
            pm_contract = w3.eth.contract(address=pm_address, abi=POSITION_MANAGER_ABI_V4)
            pool_contract = w3.eth.contract(address=pool_manager_address, abi=POOL_MANAGER_ABI_V4)
            pool_abi = POOL_MANAGER_ABI_V4  # Not used directly
            get_fee_growth_func = get_fee_growth_inside_v4  # V4 func
        
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
                    time.sleep(1)  # Delay per position
                    token_id = pm_contract.functions.tokenOfOwnerByIndex(owner_checksum, i).call()
                    pos = pm_contract.functions.positions(token_id).call()
                    liquidity = pos[6] if config.get('version') == 'v4' else pos[7]  # Adjust index for V4 (poolKey shifts)
                    if liquidity == 0:
                        continue
                    
                    if config.get('version') == 'v3':
                        # V3 logic (same as before)
                        token0 = pos[2]
                        token1 = pos[3]
                        fee = pos[4]
                        tick_lower = pos[5]
                        tick_upper = pos[6]
                        # ... (rest V3)
                        pool_addr = factory_contract.functions.getPool(token0_checksum, token1_checksum, fee).call()
                        if pool_addr == '0x0000000000000000000000000000000000000000':
                            continue
                        pool_contract_local = w3.eth.contract(address=w3.to_checksum_address(pool_addr), abi=POOL_ABI_V3)
                        slot0 = pool_contract_local.functions.slot0().call()
                        # ... (amounts, fees, etc.)
                    else:  # V4 logic
                        pool_key = pos[2]  # PoolKey tuple: (currency0, currency1, fee, tickSpacing, hooks)
                        token0, token1, fee, tick_spacing, hooks = pool_key
                        token0_checksum = w3.to_checksum_address(token0)
                        token1_checksum = w3.to_checksum_address(token1)
                        tick_lower = pos[3]
                        tick_upper = pos[4]
                        fee_growth_inside0_last = pos[6]
                        fee_growth_inside1_last = pos[7]
                        tokens_owed0 = pos[8]
                        tokens_owed1 = pos[9]
                        
                        pool_id = get_pool_id(w3, pool_key)
                        time.sleep(1)
                        slot0 = pool_contract.functions.getSlot0(pool_id).call()
                        sqrt_price_x96 = slot0[0]
                        current_tick = slot0[1]
                        
                        # ... (in_range, amounts same)
                        
                        # Fees
                        time.sleep(1)
                        fee_growth_global0 = pool_contract.functions.getFeeGrowthGlobal0X128(pool_id).call()
                        time.sleep(1)
                        fee_growth_global1 = pool_contract.functions.getFeeGrowthGlobal1X128(pool_id).call()
                        fee_growth_inside0, fee_growth_inside1 = get_fee_growth_func(pool_contract, pool_id, tick_lower, tick_upper, current_tick, fee_growth_global0, fee_growth_global1)
                        
                        # ... (accrued, uncollected same)
                    
                    # Common output
                    # ... (sym0, sym1, balance_usd, etc.)
                
                if has_positions:
                    output.append("---")
                time.sleep(3)  # Delay between owners
            except Exception as e:
                output.append(f"Error for {short_name} on {chain_name}: {e}")
    
    # Send message (same)
    # ...

if __name__ == "__main__":
    monitor_positions()
