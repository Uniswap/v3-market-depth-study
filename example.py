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

# fileprice = "data/ethprice_latest.csv"
# depthpct=0.02
address='0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8'
# address='0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640'
# address='0x5777d92f208679db4b9778590fa3cab3ac9e2168' # usdc dai
# address='0xcbcdf9626bc03e24f779434178a73a0b4bad62ed' #btc-eth
# address='0x99ac8ca7087fa4a2a1fb6357269965a2014abc35' #btc-eth

reload(dpu2)
# pipeline for entire process
md=dpu2.pipeMarketDepth(address='0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8',pctchg=[-.02,.02])


md.groupby('date').sum().marketdepth.plot()






# 2% +- depth
# CEX ETH USDX
# V3 ETH USDX


# debug
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

dfprice.plot('block_number','price')


# reduce size of range if 1tick spacing
if(ts==1):
    df=dpu2.LimitTickRange(df,dfprice,nstd=5).copy()

dfl = dpu2.genLiqRange(df,ts=ts)
# dfl=dpu2.LimitTickRange(dfl,dfprice,nstd=5).copy()

# dfl.groupby('block_number').amount.sum()

dfl['block_timestamp']=pd.to_datetime(dfl.block_timestamp)
dfl['date']=dfl.block_timestamp.dt.date

# aa=dfl.groupby('block_number').amount.sum();aa.loc[aa<1e23].plot()

# dfm=pd.merge(dfl,dfprice,on='date',how='left').dropna()
dfm=pd.merge(dfl,dfprice,on='block_number',how='left').dropna()
# dfm.loc[dfm.block_number==dfm.block_number.max()].plot('tickLower','amount')
 # dfm.groupby('block_number').amount.sum().plot()


reload(dpu2)

dfm2=dpu2.genLiqRangeXNumeraire(dfm,tickspacing=ts,decimals0=decimals0,decimals1=decimals1,pricemode=0)

liqsumbydate=dfm2.groupby(['date','block_number']).agg({'x':sum,'y':sum,'liqX':sum,'amount':sum})

bn=liqsumbydate.reset_index().block_number.max(); bn
liqsumbydate.tail(5)
import subgraph
reload(subgraph)

sg,_,_=subgraph.getdata(pool0x=address,blockN=bn); sg


#
tvlusd=pd.read_csv('tvl_usdceth.csv')
tvlusd['date']=pd.to_datetime(tvlusd.dt).dt.date
tvlm=pd.merge(tvlusd,liqsumbydate,on='date')


fig,ax=plt.subplots(figsize=(8,6))
tvlm['date']=pd.to_datetime(tvlm.date).dt.date
tvlm['usdmm']=tvlm.tvlusd/1e6
tvlm['liqxmm']=tvlm.liqX/1e6
ax=tvlm.set_index('date')[['usdmm','liqxmm']].plot(ax=ax,title='TVL comparison for usdc-eth 30bps pool',ylabel='TVL in $mm')
ax.legend(['TVL_subgraph','TVL_liquidity_sum'])
fig.savefig('TVL_compare.pdf')



tvl=pd.read_csv('tvlbypair.csv')
tvl['date']=pd.to_datetime(tvl.week).dt.date
address1='\\' + address[1:]
tvlpool=tvl.loc[tvl.pool==address1]
# tvlpool.plot('date','pool_bal')
tvlm=pd.merge(tvlpool[['date','pool_bal']],liqsumbydate,on='date')
tvlm.set_index('date')[['pool_bal','liqX']].plot()


######
reload(dpu2)

bbp=dpu2.genMarketDepth(dfm,delta=.02,ts=ts, plusminus=False,decimals0=decimals0)
bbm=dpu2.genMarketDepth(dfm,delta=-.02,ts=ts,plusminus=False,decimals0=decimals0)


mktdepth2pct=pd.merge(bbp,bbm,left_index=True,right_index=True,suffixes=('bid','ask'))#.plot()

mktdepth2pct.tail()

mktdepth2pct['diff']=mktdepth2pct.marketdepthbid-mktdepth2pct.marketdepthask
