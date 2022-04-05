import requests
import pandas as pd
import time
import numpy as np
import json
import os
# from multiprocessing import Pool
from tqdm.contrib.concurrent import process_map


def subgraph_pull(pool0x="0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8",block_number=12377369):
  try:
    query = '''
    {
      pools(where: {id: "%s"}
                    block: {number:%i}
    ) {
        tick
        token0Price
        token1Price
      }
    }
    ''' % (pool0x,block_number)

    request = requests.post('https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3'
                                '',
                                json={'query': query})

    if request.status_code == 200:
        _dt = request.json()
    else:
        print("Failed with reason ")

    if not _dt['data']['pools']:
        print('exit')
        return

    out=_dt['data']['pools'][0]

    time.sleep(.5)

  except Exception as e:
    print(e)
    return

  return out

def getprice_ts(poolid="0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8",bn=[]):
    tmplist=list()
    from tqdm import tqdm
    for i in tqdm(range(len(bn))):
        # print(i)
        bi=bn[i]
        ctick=subgraph_pull(poolid,bi)
        ctick['bn']=bi
        tmplist.append(ctick)
    df=pd.DataFrame.from_dict(tmplist).iloc[1:]
    df['tick']=df.tick.astype('int')
    df['token0Price']=df.token0Price.astype('float')
    df['token1Price']=df.token1Price.astype('float')
    return df

if __name__ == "__main__":
    import sys
    POOL_ID="0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"
    BLOCKFILE='lookup_dateblockN2.csv'
    if len(sys.argv) > 1:
        POOL_ID = sys.argv[1]
    if len(sys.argv) > 2:
        BLOCKFILE= sys.argv[2]
    bn=pd.read_csv(BLOCKFILE)
    tmplist=list()
    from tqdm import tqdm
    for i in tqdm(range(len(bn))):
        # print(i)
        bi=bn.iloc[i].block_number
        ctick=subgraph_pull(POOL_ID,bi)
        ctick['bn']=bi
        tmplist.append(ctick)
    df=pd.DataFrame.from_dict(tmplist)
    df.iloc[1:].to_csv('tickprice_%s.csv' % POOL_ID)
    # df['token0Price']=list(map(float,df['token0Price'].values))
    # df.plot('bn','token0Price')
