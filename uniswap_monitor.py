# ... (imports, ABIs as before, but add V4 ABIs from previous messages)

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
        'pool_manager': '0x28e2ea090877bf75740558f6bfb36a5ffee9e9df',  # V4 PoolManager
        'position_manager': '0x7a4a5c919ae2541aed11041a1aeee68f1287f95b',  # V4 PositionManager
        'platform': 'binance-smart-chain',
        'version': 'v4'
    }
}

# Add V4-specific functions (from previous)
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
    
    return fee_growth_global0 - fee_growth_below0 - fee_growth_above0, fee_growth_global1 - fee_growth_below1 - fee_growth_above1

# In monitor_positions() loop:
for chain_name, config in chains.items():
    # ... (connect w3)
    
    if config.get('version') == 'v3':
        # V3 logic (as before)
        # ...
    else:  # v4
        pm_address = w3.to_checksum_address(config['position_manager'])
        pool_manager_address = w3.to_checksum_address(config['pool_manager'])
        pm_contract = w3.eth.contract(address=pm_address, abi=POSITION_MANAGER_ABI_V4)  # Use V4 ABI
        pool_contract = w3.eth.contract(address=pool_manager_address, abi=POOL_MANAGER_ABI_V4)
        
        # ... (balanceOf, tokenOfOwnerByIndex same)
        for i in range(num_pos):
            # ... (token_id, pos = pm_contract.functions.positions(token_id).call())
            liquidity = pos[7]  # Adjust index if needed for V4
            if liquidity == 0: continue
            
            pool_key = pos[2]  # (currency0, currency1, fee, tickSpacing, hooks)
            currency0, currency1, fee, tick_spacing, hooks = pool_key
            token0_checksum = w3.to_checksum_address(currency0)
            token1_checksum = w3.to_checksum_address(currency1)
            tick_lower = pos[5]
            tick_upper = pos[6]
            # ... (fee_growth_inside0_last = pos[8], etc.)
            
            pool_id = get_pool_id(w3, pool_key)
            slot0 = pool_contract.functions.getSlot0(pool_id).call()
            sqrt_price_x96 = slot0[0]
            current_tick = slot0[1]
            
            # ... (in_range, amounts same as V3)
            
            # Fees
            fee_growth_global0 = pool_contract.functions.getFeeGrowthGlobal0X128(pool_id).call()
            fee_growth_global1 = pool_contract.functions.getFeeGrowthGlobal1X128(pool_id).call()
            fee_growth_inside0, fee_growth_inside1 = get_fee_growth_inside_v4(pool_contract, pool_id, tick_lower, tick_upper, current_tick, fee_growth_global0, fee_growth_global1)
            
            # ... (rest same: decimals, symbols, prices, output)
    
    # ... (end loop)
