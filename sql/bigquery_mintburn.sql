CREATE TEMP FUNCTION
  PARSE_BURN_LOG(data STRING, topics ARRAY<STRING>)
  RETURNS STRUCT<`owner` STRING, `tickLower` STRING, `tickUpper` STRING, `amount` STRING, `amount0` STRING, `amount1` STRING>
  LANGUAGE js AS """
    var parsedEvent = {"anonymous": false, "inputs": [{"indexed": true, "internalType": "address", "name": "owner", "type": "address"}, {"indexed": true, "internalType": "int24", "name": "tickLower", "type": "int24"}, {"indexed": true, "internalType": "int24", "name": "tickUpper", "type": "int24"}, {"indexed": false, "internalType": "uint128", "name": "amount", "type": "uint128"}, {"indexed": false, "internalType": "uint256", "name": "amount0", "type": "uint256"}, {"indexed": false, "internalType": "uint256", "name": "amount1", "type": "uint256"}], "name": "Burn", "type": "event"}
    return abi.decodeEvent(parsedEvent, data, topics, false);
"""
OPTIONS
  ( library="https://storage.googleapis.com/ethlab-183014.appspot.com/ethjs-abi.js" );

CREATE TEMP FUNCTION
  PARSE_MINT_LOG(data STRING, topics ARRAY<STRING>)
  RETURNS STRUCT<`sender` STRING, `owner` STRING, `tickLower` STRING, `tickUpper` STRING, `amount` STRING, `amount0` STRING, `amount1` STRING>
  LANGUAGE js AS """
    var parsedEvent = {"anonymous": false, "inputs": [{"indexed": false, "internalType": "address", "name": "sender", "type": "address"}, {"indexed": true, "internalType": "address", "name": "owner", "type": "address"}, {"indexed": true, "internalType": "int24", "name": "tickLower", "type": "int24"}, {"indexed": true, "internalType": "int24", "name": "tickUpper", "type": "int24"}, {"indexed": false, "internalType": "uint128", "name": "amount", "type": "uint128"}, {"indexed": false, "internalType": "uint256", "name": "amount0", "type": "uint256"}, {"indexed": false, "internalType": "uint256", "name": "amount1", "type": "uint256"}], "name": "Mint", "type": "event"}
    return abi.decodeEvent(parsedEvent, data, topics, false);
"""
OPTIONS
  ( library="https://storage.googleapis.com/ethlab-183014.appspot.com/ethjs-abi.js" );

WITH parsed_burn_logs AS
(SELECT
    logs.block_timestamp AS block_timestamp
    ,logs.block_number AS block_number
    ,logs.transaction_hash AS transaction_hash
    ,logs.log_index AS log_index
    ,PARSE_BURN_LOG(logs.data, logs.topics) AS parsed
FROM `bigquery-public-data.crypto_ethereum.logs` AS logs
WHERE address IN ('0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8')
  AND topics[SAFE_OFFSET(0)] = '0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c'
)
,parsed_mint_logs AS
  (SELECT
    logs.block_timestamp AS block_timestamp
    ,logs.block_number AS block_number
    ,logs.transaction_hash AS transaction_hash
    ,logs.log_index AS log_index
    ,PARSE_MINT_LOG(logs.data, logs.topics) AS parsed
FROM `bigquery-public-data.crypto_ethereum.logs` AS logs
WHERE address IN ('0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8')
  AND topics[SAFE_OFFSET(0)] = '0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde'
)
SELECT
     block_timestamp
     ,block_number
     ,transaction_hash
     ,log_index
    ,parsed.owner AS `owner`
    ,parsed.tickLower AS `tickLower`
    ,parsed.tickUpper AS `tickUpper`
    ,parsed.amount AS `amount`
    ,parsed.amount0 AS `amount0`
    ,parsed.amount1 AS `amount1`
    ,1 AS  `type`
FROM parsed_mint_logs
UNION ALL
SELECT
     block_timestamp
     ,block_number
     ,transaction_hash
     ,log_index
    ,parsed.owner AS `owner`
    ,parsed.tickLower AS `tickLower`
    ,parsed.tickUpper AS `tickUpper`
    ,parsed.amount AS `amount`
    ,parsed.amount0 AS `amount0`
    ,parsed.amount1 AS `amount1`
    ,-1 AS `type`
FROM parsed_burn_logs
