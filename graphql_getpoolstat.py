import requests
import pandas as pd
import time
import numpy as np
import json
import os
# from multiprocessing import Pool
from tqdm.contrib.concurrent import process_map


def subgraph_getpoolstats(pool0x="0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"):
  try:
    query = '''
    {
      pools(where: {id: "%s"}
    ) {
        token0 {
          decimals
          name
          symbol
          id
        }
        token1 {
          decimals
          name
          symbol
        }
        feeTier
        volumeUSD
        untrackedVolumeUSD
        volumeToken1
        volumeToken0
        feesUSD
        collectedFeesUSD
        collectedFeesToken1
        collectedFeesToken0
      }
    }
    ''' % (pool0x)

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
    # time.sleep(.5)

  except Exception as e:
    print(e)
    return
  return out


if __name__ == "__main__":
    import sys
    POOL_ID="0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"
    if len(sys.argv) > 1:
        POOL_ID = sys.argv[1]
    # print(subgraph_getpoolstats(POOL_ID))
    print(pd.DataFrame(subgraph_getpoolstats(POOL_ID)))
