import numpy as np
import pandas as pd
import sqlite3
from tqdm import tqdm
import depthutil2 as dpu2

# df=pd.read_csv('data/toppools.csv')
# df2=pd.DataFrame(df.groupby('exchange_contract_address').usd_amount.sum()).reset_index().sort_values('usd_amount',ascending=False).replace('\\\\x','0x',regex=True)
# df2.to_csv('data/toppoolsbyvolume.csv')

import dbtools as db

pools = pd.read_csv("data/toppoolsbyvolume.csv")

DB_OUT='uniswap.marketdepth'
pcts = [-.06, -.04, -.02, -.01, -.005, -.004, -.003, -.002, -.001, -.00075, -.00050, -.00025,
        .001, .00025, .00050, .00075, .002, .003, .004, .005, .01, .02, .04, .06]

for i in tqdm(range(len(pools))):
    if not(db.bigquery(f'select count(address) as ct from uniswap.marketdepth where address="%s"' % address).ct[0]):
        try:
            address=pools.iloc[i].exchange_contract_address
            md=dpu2.pipeMarketDepth(address=address,pctchg=pcts,UseSubgraph=False)
            md['address']=address
            poolstats=db.getpoolstats(address)
            md['unit_token0']=poolstats['token0symbol']
            pd.io.gbq.to_gbq(md, DB_OUT,project_id='mimetic-design-338620',if_exists='append')
        except:
            print(f'failed at %s %s' % (i,address))
            pass
