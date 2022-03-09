# %cd ../../marketdepthstudy
# Imports
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import datetime
# %matplotlib inline
from importlib import reload
import depthutil as dpu

reload(dpu)
# filein = "data/mintburn_usdceth3000_220202.csv"
filein = 'data/mintburnall_bigquery.csv'
fileprice = "data/ethprice_latest.csv"

# 0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8	USDC-WETH 3000 60
# 0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640	USDC-WETH 500 10
address = '0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8'
tickspacing = 60
depthpct = 0.02
dfdepth, liqdist, dfrgns=dpu.CalcAll(filein,fileprice,tickspacing,depthpct,address)
dfdepth.to_pickle('data/usdcweth3000_depth.pkl')
liqdist.to_pickle('data/usdcweth3000_liqdist.pkl')
dfrgns.to_pickle('data/usdcweth3000_rgns.pkl')


address = '0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640'
tickspacing = 10
depthpct = 0.02
dfdepth, liqdist, dfrgns=dpu.CalcAll(filein,fileprice,tickspacing,depthpct,address)
dfdepth.to_pickle('data/usdcweth500_depth.pkl')
liqdist.to_pickle('data/usdcweth500_liqdist.pkl')
dfrgns.to_pickle('data/usdcweth500_rgns.pkl')

liqdist.columns

liqdist.loc[liqdist.date=='2022-02-22'].query("price<6000").plot('price','depth')

dfdepth

liqdist.loc[liqdist.date=='2022-02-22'].query("price<6000")


dfdepth.set_index('date').plot()


# load data and format
dfprice = pd.read_csv(fileprice).rename(columns={"price": "P"})
dfprice["date"] = pd.to_datetime(dfprice.date).dt.date
df = pd.read_csv(filein, dtype={'amount': float,
                 'amount0': float, 'amount1': float})
len(df)
df = df.loc[df.address == address]
###
df = df.loc[df.address.isin(['0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8', '0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640'])]

df.loc[df.type==1].groupby('address').amount.describe()
####
df.columns

df.tickLower.describe()

df = df.rename(columns={"lowertick": "tickLower",
               "uppertick": "tickUpper", "block_timestamp": "call_block_time"})
df["date"] = pd.to_datetime(df.call_block_time).dt.date

df["amount"] = df.amount.map(float)


dfs = df.groupby(["date", "tickLower", "tickUpper"]).amount.sum()
dft2 = pd.DataFrame(dfs).reset_index()

rgn = dpu.genLiqRange(dft2, tickspacing=tickspacing)
reload(dpu)
 dfprice.loc[dfprice.date
                       == datetime.date(2022, 1, 31), "P"].values[0]
rgn["P"] = dfprice.loc[dfprice.date
                       == datetime.date(2022, 1, 31), "P"].values[0]

rgn.head()
liq = dpu.genDepth(rgn, tickspacing=tickspacing,alt=0)#.pipe(dpu.calcDepth)
liq2 = dpu.genDepth(rgn, tickspacing=tickspacing, alt=1)#.pipe(dpu.calcDepth)




liq.query("price<6000").plot("price", "liqX")
liq2.query("price<6000").plot("price", "liqX")
pd.merge(liq, liq2, on="price").query("price<10000").set_index("price")[["liqX_x", "liqX_y"]].plot()
liq.query("price<6000").plot("price", "y")
liq.query("price<6000").plot("price", "x")


liq.query("price<1e7").liqX.sum() / 1e6
liq2.query("price<1e7").liqX.sum() / 1e6
liq.liqX.sum() / 1e6
liq2.liqX.sum() / 1e6



liq.query("price<6000").plot('price','liqX')
liq.query("price<6000").plot('price','depth')
liq.query("price<1e7").plot('price','depth')
liq.depth.max()

dfsingle=dpu.fillGranularDistribution(liq.query("price<6000"),returnDepth=0,depthpct=1)#.plot('price','depthattick')
dfsingle.head()
dfsingle.plot('price','depthattick')
