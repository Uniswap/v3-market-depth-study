import matplotlib.pyplot as plt
import pandas as pd
import datetime
from importlib import reload
from depthutil2 import *
import graphql_getpoolstat

address='0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8'
# address='0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640'
# address='0x4e68ccd3e89f51c3074ca5072bbac773960dfa36'
# address='0x5777d92f208679db4b9778590fa3cab3ac9e2168' # usdc dai
# address='0xcbcdf9626bc03e24f779434178a73a0b4bad62ed' #btc-eth
# address='0x99ac8ca7087fa4a2a1fb6357269965a2014abc35' #btc-eth

loadmintburns=0
if loadmintburns:
    #' Load mint burn history from GCP server by running bigquery_mintburn.sql or run dune mintburn_dune.sql and download data
    from dbtools import *
    df=bigquery("select * from uniswap.MintBurn where amount!=0")
    df.to_csv('data/mintburnall_bigquery.csv')

# Generate Market Depth at +- 2%
md=pipeMarketDepth(filein = 'data/mintburnall_bigquery.csv', address=address,pctchg=[-.02,.02],UseSubgraph=True)

# +2% market depth
md.loc[md.pct==.02].plot('date','marketdepth')

# -2% market depth
md.groupby('date').sum().marketdepth.plot()

#%%
