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
filein = "data/mintburn_usdceth3000_220202.csv"
filein = 'data/mintburn_bigquery.csv'
fileprice = "data/ethprice_latest.csv"
tickwindow = 60
depthpct = 0.02

# load data and format
dfprice = pd.read_csv(fileprice).rename(columns={"price": "P"})
dfprice["date"] = pd.to_datetime(dfprice.date).dt.date
df = pd.read_csv(filein)
###
df = df.rename(columns={"lowertick": "tickLower",
               "uppertick": "tickUpper", "block_timestamp": "call_block_time"})
df["date"] = pd.to_datetime(df.call_block_time).dt.date
df["amount"] = df.amount.map(float)*df.type

dfs = df.groupby(["date", "tickLower", "tickUpper"]).amount.sum()
dft2 = pd.DataFrame(dfs).reset_index()

rgn = dpu.genLiqRange(dft2, tickwindow=tickwindow)
reload(dpu)

rgn["P"] = dfprice.loc[dfprice.date
                       == datetime.date(2022, 1, 31), "P"].values[0]
liq = dpu.calcdollarliq(rgn, tickwindow=tickwindow, alt=0).pipe(dpu.calcDepth)
liq2 = dpu.calcdollarliq(rgn, tickwindow=tickwindow, alt=1).pipe(dpu.calcDepth)

liq.query("price<6000").plot("price", "liqusd")
liq2.query("price<6000").plot("price", "liqusd")
pd.merge(liq, liq2, on="price").query("price<10000").set_index(
    "price")[["liqusd_x", "liqusd_y"]].plot()
liq.query("price<6000").plot("price", "y")
liq.query("price<1e7").liqusd.sum() / 1e6
liq2.query("price<1e7").liqusd.sum() / 1e6
liq.liqusd.sum() / 1e6
liq2.liqusd.sum() / 1e6
dpu.expandliqdistrib(liq)
dpu.expandliqdistrib(liq2)
