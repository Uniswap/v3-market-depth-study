import pandas as pd

def getpricefromswap(address='0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8',decimals0=6,decimals1=18):
    from google.cloud import bigquery
    project_id='mimetic-design-338620'
    q=f'''with px as (SELECT block_timestamp,block_number,address, tick, sqrtPriceX96, row_number() over
    (partition by block_number, address order by log_index desc) as rn  FROM `mimetic-design-338620.uniswap.swap`
    where address="{address}"
    )
    select block_timestamp,block_number,tick, sqrtPriceX96 from px where rn=1;'''
    df = pd.io.gbq.read_gbq(q, project_id=project_id, dialect='standard')
    df['p']=list(map(lambda x: 10**(decimals1-decimals0)/(float(x)**2/(2**192)),df.sqrtPriceX96))
    df['date']=pd.to_datetime(df.block_timestamp)
    df=df.sort_values('block_number')
    df=df.set_index('block_number')
    return df


def getpoolstats(poolid):
    #' return token0, token1, decimals0, decimals1, tickspacing, feetier
    #' call bigquery: `bigquery-public-data.crypto_ethereum.tokens` join with `mimetic-design-338620.uniswap.V3Factory_PoolCreated`
    return


def getpriceatblocknumber(address, block_numbers=[]):
    #' get price of a pair specificed by liquidity pool address at specified block_numbers
    #' Use pandas merge_asof to get to the price asof prespecified block_numbers
    #' Utilize getpricefromswap and getpoolstats
    return
