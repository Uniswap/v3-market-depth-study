import pandas as pd
from google.cloud import bigquery

def getpricefromswap(address='0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8',decimals0=6,decimals1=18):
    project_id='mimetic-design-338620'
    q=f'''with px as (SELECT block_timestamp,block_number,address, tick, sqrtPriceX96, row_number() over
    (partition by block_number, address order by log_index desc) as rn  FROM `mimetic-design-338620.uniswap.swap`
    where address="{address}"
    )
    select block_timestamp,block_number,tick, sqrtPriceX96 from px where rn=1;'''
    df = pd.io.gbq.read_gbq(q, project_id=project_id, dialect='standard')
    df['price']=list(map(lambda x: 10**(decimals1-decimals0)/(float(x)**2/(2**192)),df.sqrtPriceX96))
    df['tick']=list(map(int,df.tick))
    df['date']=pd.to_datetime(df.block_timestamp)
    df=df.sort_values('block_number')
    df=df.set_index('block_number')
    return df


def getpricefromdb(address='0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8'):
    # gets price from db based on swap data
    project_id='mimetic-design-338620'
    poolstats=getpoolstats(address=address)
    q=f'''select *  FROM `mimetic-design-338620.uniswap.price`
     where address="{address}"
    '''
    df = pd.io.gbq.read_gbq(q, project_id=project_id, dialect='standard')
    df['price']=list(map(lambda x: 10**(poolstats['decimals1']-poolstats['decimals0'])/(float(x)**2/(2**192)),df.sqrtPriceX96))
    df['tick']=list(map(int,df.tick))
    df['date']=pd.to_datetime(df.block_timestamp)
    df=df.sort_values('block_number')
    df=df.set_index('block_number')
    return df


def getpoolstats(address='0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8'):
    #' return token0, token1, decimals0, decimals1, tickspacing, feetier
    #' call bigquery: `bigquery-public-data.crypto_ethereum.tokens` join with `mimetic-design-338620.uniswap.V3Factory_PoolCreated`
    #' select pools.*, tk0.symbol as token0symbol, tk0.decimals as decimals0, tk1.symbol as token1symbol, tk1.decimals as decimals1 from `mimetic-design-338620.uniswap.V3Factory_PoolCreated` pools
    # left join `bigquery-public-data.crypto_ethereum.amended_tokens` tk0 on pools.token0=tk0.address
    # left join `bigquery-public-data.crypto_ethereum.amended_tokens` tk1 on pools.token1=tk1.address
    project_id='mimetic-design-338620'
    q=f'''select token0, token1,fee,tickSpacing,pool,token0symbol,token1symbol,decimals0,decimals1 FROM `mimetic-design-338620.uniswap.pools_tokens_decimals`
     where pool="{address}"
    '''
    df = pd.io.gbq.read_gbq(q, project_id=project_id, dialect='standard')
    return dict(df.iloc[0])


def getpriceatblocknumber(address='0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8', block_numbers=[12602988, 12839866, 12902514]):
    #' get price of a pair specificed by liquidity pool address at specified block_numbers
    #' Use pandas merge_asof to get to the price asof prespecified block_numbers
    #' Utilize getpricefromswap and getpoolstats
    poolstats=getpoolstats(address=address)
    dfbn=pd.DataFrame(block_numbers,columns={'block_number'})
    df=getpricefromdb(address)
    df=df.reset_index()
    df['block_number']=list(map(int,df.block_number))
    dfout=pd.merge_asof(dfbn,df,on='block_number')
    return dfout
