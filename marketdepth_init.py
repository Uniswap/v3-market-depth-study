import numpy as np
import os

import requests
import pandas as pd
import time

from web3 import Web3

import sqlite3

from tqdm import tqdm
from itertools import combinations

import depthutil as dpu
import depthutil2 as dpu2
import graphql_getpoolstat

class sql_connector():
    def __init__(self, path):
        if not os.path.exists(f'{path}/sql'):
            os.mkdir(f'{path}/sql/')

        conn = sqlite3.connect(f"{path}/sql/market_depth.db")
        cursor = conn.cursor()
        
        self._conn = conn
        self._cursor = cursor
    
    def execute(self, query):
        _ = self._cursor.execute(query)
        
        self._conn.commit()
        
    def read(self, query):
        res = pd.read_sql(query, self._conn)
        
        return res
    
    def write(self, data, query):
        self._cursor.executemany(query, data)
        
        self._conn.commit()

'''
Hard-coded tokens to search over
'''
tokens = ["0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", "0x6B175474E89094C44Da98b954EedeAC495271d0F",
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599", "0x514910771AF9Ca656af840dff83E8264EcF986CA",
            "0xc00e94Cb662C3520282E6f5717214004A7f26888", "0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0",
            "0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2", "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
            "0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e"]
        
tokens_to_decimals = {
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2": 18,
    "0x6B175474E89094C44Da98b954EedeAC495271d0F": 18,
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": 6,
    "0xdAC17F958D2ee523a2206206994597C13D831ec7": 6,
    "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599": 8,
    "0x514910771AF9Ca656af840dff83E8264EcF986CA": 18,
    "0xc00e94Cb662C3520282E6f5717214004A7f26888": 18,
    "0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0": 18,
    "0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2": 18,
    "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9": 18,
    "0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e": 18   
}

addr_to_name = {
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2": "weth",
    "0x6B175474E89094C44Da98b954EedeAC495271d0F": "dai",
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": "usdc",
    "0xdAC17F958D2ee523a2206206994597C13D831ec7": "usdt",
    "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599": "wbtc",
    "0x514910771AF9Ca656af840dff83E8264EcF986CA": "link",
    "0xc00e94Cb662C3520282E6f5717214004A7f26888": "comp",
    "0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0": "matic",
    "0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2": "mkr",
    "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9": "aave",
    "0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e": "yfi"
}

path = os.getcwd()
conn = sql_connector(path)

rerun = False
print(f"Drop and rerun: {rerun}")
if rerun:
    query = '''DROP TABLE IF EXISTS market_depth'''
    conn.execute(query)

    query = '''CREATE TABLE IF NOT EXISTS market_depth (market_depth real, pct real, date text,
                                                block_number text, pool text, token0 text,
                                                token1 text, token0Name text, token1Name text,
                                                fee_tier real)'''
    conn.execute(query)

tracked_pools = pd.read_csv("tracked_pools.csv")

pcts = [-.06, -.04, -.02, -.01, -.005, -.004, -.003, -.002, -.001, -.00075, -.00050, -.00025, 
        .001, .00025, .00050, .00075, .002, .003, .004, .005, .01, .02, .04, .06]

for pool in tracked_pools['pool']:
    pool_info = tracked_pools[tracked_pools['pool'] == pool]
    
    token0_addr, token1_addr = pool_info['token0'].item(), pool_info['token1'].item()
    token0_name, token1_name = pool_info['token0Name'].item(), pool_info['token1Name'].item()
    tier = pool_info['fee_tier'].item()
    
    md=dpu2.pipeMarketDepth(address=pool.lower(),pctchg=pcts)

    # clean and add s
    md['pool'] = pool
    md['token0'] = token0_addr
    md['token1'] = token1_addr
    md['token0Name'] = token0_name
    md['token1Name'] = token1_name

    md['fee_tier'] = tier
    md['block_number'] = md['block_number'].astype(str)
    md['date'] = md['date'].apply(lambda x: x.strftime("%m-%d-%Y"))

    query = "INSERT into market_depth values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
    _data = [[*arr] for arr in md.values]

    conn.write(_data, query)
    