import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import datetime
import os
# %matplotlib inline
from importlib import reload
import depthutil as dpu
import depthutil2 as dpu2
import graphql_getpoolstat
reload(graphql_getpoolstat)
reload(dpu)
reload(dpu2)


# Setup
address='0x11b815efb8f581194ae79006d24e0d814b7697f6'
filein = 'data/mintburnall_bigquery.csv'
poolstats=graphql_getpoolstat.subgraph_getpoolstats(address)
decimals0=int(poolstats['token0']['decimals'])
decimals1=int(poolstats['token1']['decimals'])
symbol0=poolstats['token0']['symbol']
symbol1=poolstats['token1']['symbol']
feeTier=int(poolstats['feeTier'])
ts=dpu2.feetier2tickspacing(feeTier)
print(symbol0,decimals0, symbol1, decimals1,feeTier,ts)


df = pd.read_csv(filein, dtype={'amount': float, 'amount0': float, 'amount1': float})
df = df.loc[df.address == address]
df = df.loc[df.amount!=0]
df["date"] = pd.to_datetime(df.block_timestamp).dt.date
df=df.sort_values('block_number')
fileprice='tickprice_%s.csv' % address
if (not(os.path.exists(fileprice))):
    print('getting prices:')
    bndate=df.loc[df.amount!=0].groupby('date').block_number.last()
    bndate.to_csv('tmp_bndate.csv')
    os.system('python3.9 graphql_getprice.py %s %s' % (address,'tmp_bndate.csv'))
dfprice=pd.read_csv(fileprice)[['bn','token0Price','tick']].rename(columns={'bn':'block_number','token0Price':'price','tick':'currenttick'})
dfl = dpu2.genLiqRange(df,ts=ts)
dfl['block_timestamp']=pd.to_datetime(dfl.block_timestamp)
dfl['date']=dfl.block_timestamp.dt.date
dfm=pd.merge(dfl,dfprice,on='block_number',how='left').dropna()
dfm2=dpu2.genLiqRangeXNumeraire(dfm,tickspacing=ts,decimals0=decimals0,decimals1=decimals1,pricemode=0)

import pytest


# test 1:
# Liquidity for pool '0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8' adds up to 1.600162726770379e+21 at block_number 14260474
dfm2.loc[dfm2.block_number==14260474].amount.sum()==pytest.approx(1.600162726770379e+21)


# test 2
# Liquidity for pool '0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8' at block_number 14260474 lowertick 197460 is 1.1738573703702172e+19
dfm2.loc[(dfm2.block_number==14260474) & (dfm2.tickLower==int(np.floor(197484/60)*60)),'amount'].values[0]==pytest.approx(1.1738573703702172e+19)

# test 3
# Token 0 (USDC) locked in for pool '0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8' at block_number 14260474 lowertick 197460 is 1.087375e+06
# toekn 1 (eth) locked in this tick spacing is 273.281667
dfm2.loc[(dfm2.block_number==14260474) & (dfm2.tickLower==int(np.floor(197484/60)*60)),'x'].values[0]==pytest.approx(1.087375e+06)
dfm2.loc[(dfm2.block_number==14260474) & (dfm2.tickLower==int(np.floor(197484/60)*60)),'y'].values[0]==pytest.approx(273.281667)



# test 4
1.812494e+06/60
# per tick liquidity of the above tickspacing is 30208.233333333334
tmpdf=dfm2.loc[(dfm2.block_number==14260474) & (dfm2.tickLower==int(np.floor(197484/60)*60))]
dpu2.calc_liquidity_at_tick(i=197460,din=tmpdf,p=1.0001**197484)/1e6==pytest.approx(30208.233333333334)
print('not too far off:',dpu2.calc_liquidity_at_tick(i=197460,din=tmpdf,p=1.0001**197484)/1e6)



# test 5
# (1e12/1.0001**197460)/2653.3792-1
# (1e12/1.0001**(197460+59))/2653.3792-1

i00=1e12/1.0001**197484
i00/(1e12/1.0001**197460)-1
i00/(1e12/1.0001**(197460+60))-1

# market depth for price pct range from -0.002397002598245934 to 0.00360630714589405 should be equivalent to token 0 +token 1 converted to token 0 ~ $1.812494e+06
# there should be exactly 60 tics
# should current price be provided by p or 1.0001**currenttick? does it matter empirically?

dfm2.tail(5)
d1,diag1=dpu2.calc_market_depth(df=dfm2.loc[(dfm2.block_number==14260474)],i0=197484,delta=-0.002397002598245934,plusminus=False,logdelta=False,diagnosis=True)
d2,diag2=dpu2.calc_market_depth(df=dfm2.loc[(dfm2.block_number==14260474)],i0=197484,delta=0.00360630714589405,plusminus=False,logdelta=False,diagnosis=True)

d1+d2==pytest.approx(1.812494e+06)
print(d1+d2)

print(len(diag1)+len(diag2))

# note that current tick is included twice
print(diag1)
print(diag2)


2187.5
# mkt depth for 2%
md=dpu2.pipeMarketDepth(address='0x11b815efb8f581194ae79006d24e0d814b7697f6',pctchg=[.02])
md.block_number.unique()
# 6210937
md
md.plot('date','marketdepth')
import sqlite3

con= sqlite3.connect('marketdepth.db')

df2=pd.read_sql_query('select * from market_depth',con)

df2

df2.loc[df2.twoPctInd==1]
1e12/3.823607e+08
df2.loc[(df2.twoPctInd==1) & (df2.priceImpact>1)]
df2['p']=1e12/df2.curPrice
df3=df2.loc[(df2.twoPctInd==1) & (df2.priceImpact<1)].groupby('block').tail(1)
df3['depth']=df3.token0In
# df3['depth']=np.array(map(float,df3.token1Out))
# df3['depth']=df3['depth']
df4=pd.merge(md.loc[md.pct>0],df3[['block','depth']],left_on='block_number',right_on='block')
df4.set_index('date')[['marketdepth','depth']].plot()
df4['ratio']=df4.marketdepth/df4.depth
df4.set_index('date')[['ratio']].plot()



df=pd.read_csv('data/ETHUSDT-trades-2022-03-14.csv',names=['tradeId','price','qty','quoteQty','time','isBuyerMaker','isBestMatch'])
df.describe()
