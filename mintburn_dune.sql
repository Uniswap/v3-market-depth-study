--GET ALL MINT AND BURN SUCCESSEFUL CALLS (could also use evt table)
         SELECT                          --get all mint calls
         call_block_time,
         call_tx_hash,
             "tickLower" AS lowerTick,   --range lower limit
             "tickUpper" AS UpperTick,   --range upper limit
             amount                      --Liquidity added to each tick
         FROM uniswap_v3."Pair_call_mint"
         WHERE call_success = true       --exclude fail calls
         AND contract_address =  '\x8ad599c3a0ff1de082011efddc58f1908eb6e6d8' --pool address

         UNION ALL

         SELECT                          -- same to burn liquidity calls
         call_block_time,
         call_tx_hash,
             "tickLower" AS lowerTick,
             "tickUpper" AS UpperTick,
             -amount AS amount
         FROM uniswap_v3."Pair_call_burn"
         WHERE call_success = true
         AND contract_address = '\x8ad599c3a0ff1de082011efddc58f1908eb6e6d8'


-- 0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8 EHT/USDC 0.3
-- 0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640 ETH/USDC 0.05
-- 0x4e68ccd3e89f51c3074ca5072bbac773960dfa36  ETH/USDT 0.3
-- 0xc2e9f25be6257c210d7adf0d4cd6e3e881ba25f8  Dai/Eth 0.3
-- 0x11b815efb8f581194ae79006d24e0d814b7697f6  Eth/usdt 0.05
