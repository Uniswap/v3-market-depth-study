with trades as (SELECT
    CASE
        WHEN "token_a_address"='\xe4ab53ac2f495c0ac210ddf01a5f7b598809c3bc' then 'DOGE'
        WHEN "token_a_address"='\xf65b5c5104c4fafd4b709d9d60a185eae063276c' then 'TRU'
        WHEN "token_a_symbol"<>'' THEN "token_a_symbol"
        ELSE CONCAT('0x',encode(token_a_address::bytea,'hex'))
    END as "token_a",
    CASE
        WHEN "token_b_address" = '\xe4ab53ac2f495c0ac210ddf01a5f7b598809c3bc' then 'DOGE'
        WHEN "token_b_address"='\xf65b5c5104c4fafd4b709d9d60a185eae063276c' then 'TRU'
        WHEN "token_b_symbol"<>'' THEN "token_b_symbol"
        ELSE CONCAT('0x',encode(token_b_address::bytea,'hex'))
    END as "token_b",
    "usd_amount",
    block_time,
    exchange_contract_address
FROM dex.trades
WHERE project = 'Uniswap'
AND version = '3')

SELECT
    token_a, token_b,
    sum("usd_amount") as "usd_amount",
    exchange_contract_address
FROM trades
WHERE block_time >= date_trunc('day', now()) - interval '356 days'
AND usd_amount>0
GROUP BY token_a,token_b, exchange_contract_address
ORDER BY sum("usd_amount") DESC
;
