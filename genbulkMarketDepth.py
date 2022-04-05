import numpy as np
import pandas as pd
import sqlite3
from tqdm import tqdm
import depthutil2 as dpu2

import dbtools as db

pools = pd.read_csv("data/toppoolsbyvolume.csv")

DB_OUT='uniswap.marketdepth_daily'
pcts = [-.06, -.04, -.02, -.01, -.005, -.004, -.003, -.002, -.001, -.00075, -.00050, -.00025,
        .001, .00025, .00050, .00075, .002, .003, .004, .005, .01, .02, .04, .06]

pools=pools.sort_values('usd_amount',ascending=False).iloc[:1000]
# exists=db.bigquery(f'select distinct(address) from uniswap.marketdepth_daily')
# pools=pools.loc[~pools.exchange_contract_address.isin(exists.address)]
for i in tqdm(range(len(pools))):
    address=pools.iloc[i].exchange_contract_address
    # if not(db.bigquery(f'select count(address) as ct from uniswap.marketdepth where address="%s"' % address).ct[0]):
    try:
        md=dpu2.pipeMarketDepth2(filein='data/mintburnall_bigquery.csv',address=address,pctchg=pcts,UseSubgraph=False,CalcAtPriceChg=True)
        md['address']=address
        poolstats=db.getpoolstats(address)
        md['unit_token0']=poolstats['token0symbol']
        pd.io.gbq.to_gbq(md, DB_OUT,project_id='mimetic-design-338620',if_exists='append')
    except:
        print(f'failed database call at %s %s trying subgraph' % (i,address))
        try:
            md=dpu2.pipeMarketDepth(address=address,pctchg=pcts,UseSubgraph=True)
            md['address']=address
            poolstats=db.getpoolstats(address)
            md['unit_token0']=poolstats['token0symbol']
            pd.io.gbq.to_gbq(md, DB_OUT,project_id='mimetic-design-338620',if_exists='append')
        except:
            print(f'failed permanently database call at %s %s' % (i,address))
            pass
