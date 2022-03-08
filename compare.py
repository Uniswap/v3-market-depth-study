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
reload(dpu)
reload(dpu2)

df1=pd.read_pickle('data/usdcweth3000_depth.pkl')

# new way
filein = 'data/mintburnall_bigquery.csv'
fileprice = "data/ethprice_latest.csv"
depthpct=0.02
address='0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8'
address='0x5777d92f208679db4b9778590fa3cab3ac9e2168'
# dfprice = pd.read_csv(fileprice).rename(columns={"price": "P"})
# dfprice["date"] = pd.to_datetime(dfprice.date).dt.date
# dfprice['currenttick']=list(map(int,np.log(1e12/dfprice.P.values)/np.log(1.0001)))
import graphql_getpoolstat
poolstats=graphql_getpoolstat.subgraph_getpoolstats(address)

decimals0=int(poolstats['token0']['decimals'])
decimals1=int(poolstats['token1']['decimals'])
symbol0=poolstats['token0']['symbol']
symbol1=poolstats['token1']['symbol']
feeTier=int(poolstats['feeTier'])
ts=dpu2.feetier2tickspacing(feeTier)


df = pd.read_csv(filein, dtype={'amount': float, 'amount0': float, 'amount1': float})
df = df.loc[df.address == address]
df["date"] = pd.to_datetime(df.block_timestamp).dt.date
df=df.sort_values('block_number')

getprice=0
if (getprice):
    # get price
    bndate=df.groupby('date').block_number.last()
    bndate.to_csv('tmp_bndate.csv')
    os.system('python3.9 graphql_getprice.py %s %s' % (address,'tmp_bndate.csv'))


fileprice='tickprice_%s.csv' % address
dfprice=pd.read_csv(fileprice)[['bn','token0Price','tick']].rename(columns={'bn':'block_number','token0Price':'price','tick':'currenttick'})



df=dpu2.LimitTickRange(df,dfprice,nstd=5)

####
dfl = dpu2.genLiqRange(df,ts=1)

dfl['block_timestamp']=pd.to_datetime(dfl.block_timestamp)
dfl['date']=dfl.block_timestamp.dt.date

# dfm=pd.merge(dfl,dfprice,on='date',how='left').dropna()
dfm=pd.merge(dfl,dfprice,on='block_number',how='left').dropna()
dfm.loc[dfm.block_number==14260478].plot('tickLower','amount')





######
reload(dpu2)


bbp=dpu2.genMarketDepth(dfm,delta=.02,ds=1, plusminus=False,decimals0=1e18)
bbm=dpu2.genMarketDepth(dfm,delta=-.02,ds=1,plusminus=False,decimals0=1e18)
mktdepth2pct=pd.merge(bbp,bbm,left_index=True,right_index=True,suffixes=('bid','ask'))#.plot()

mktdepth2pct['diff']=mktdepth2pct.marketdepthbid-mktdepth2pct.marketdepthask
mktdepth2pct.plot()
dpu2.genMarketDepth(dfm,delta=.02,ds=1, plusminus=True,decimals0=1e18)

bbp.plot()



### compare with other file

lookup_dateblockN=dfl[['date','block_number']].drop_duplicates().set_index('block_number')
df1['date']=pd.to_datetime(df1['date'])
lookup_dateblockN['date']=pd.to_datetime(lookup_dateblockN['date'])

df2=pd.merge(mktdepth2pct,lookup_dateblockN,left_index=True,right_index=True)

dd=pd.merge(df1,df2,on='date').set_index('date')



#
# lookup_dateblockN.reset_index()
#
# reload(sg)
#
# tmplist=list()
# import subgraph as sg
# dfbn=lookup_dateblockN.reset_index()
# for i in range(len(dfbn)):
#     blockN=dfbn.iloc[i]['block_number']
#     print(blockN)
#     out,_,_=sg.getdata(pool0x= "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8",blockN=blockN)
#     tmplist.append(out)
#
#
# blockN
# out,_,_=sg.g   v
#
# sg.getdata(blockN=dfbn.iloc[i]['block_number'])
#
# dfbn.iloc[i]['block_number']
#
#
# dfbn.to_csv('lookup_dateblockN.csv')
#
#
#
# df.head()
# df2.plot('date','diff')
# df['amt0']=df.amount0*df.type/1e6
# df['amt1']=df.amount1*df.type/1e18
#
# df.iloc[:2].sum()
# df.loc[df.block_number<=13000379,['amt0','amt1']].sum()/1e6
#
#
# len(lookup_dateblockN)

dd[['depthask','marketdepthask']].plot()

dd[['depthbid','marketdepthbid']].plot()

dd.assign(diff=lambda x: np.abs(x.depthbid-x.marketdepthbid)).describe()
dd.assign(diff=lambda x: np.abs(x.depthask-x.marketdepthask)).describe()

# dfm.head()
#
# dfm.loc[dfm.block_number==12370671].amount.sum()
#
# dtin=dfm.loc[dfm.block_number==12370671]
# tt=dfm.loc[dfm.block_number==12370671]
# tt['diff']=tt.amount.diff()
# tt.query("diff!=0")
#
# tt.query("diff!=0").amount.sum()
# tt.amount.sum()
#
# dtin['P']=3306.010642872511#1e12/1.0001**196412
# dtin.sum()
#
# dd2=dpu.genLiqRangeXNumeraire(dtin)
# dd2.sum()
#
# df.loc[df.block_number==12370671]#.transaction_hash.values
#
# L=4.303370e+15
# x=5.000000e+10
# y=9.205484e+18
# sa=1.0001**(192660//2)
# sb=1.0001**(199800//2)
# sa
# sz=y/L+sa
# 1e12/sz**2
#
#
# print('a')
