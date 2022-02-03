### import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from importlib import reload
import depthutil as dpu
import datetime as dt

reload(dpu)

with open("kaikoapikey.txt") as f:
    apikey = f.readlines()[0].replace("\n", "")


# today --------------------------------------
today = dt.datetime.utcnow()
end = today-dt.timedelta(days=1)
# from datetime to string
end = end.strftime("%Y-%m-%d %H")

# 30 days ago --------------------------------------
N = 30
d = dt.timedelta(days=N)
start = today - d
# from datetime to string
start = start.strftime("%Y-%m-%d %H")


reloadkaiko = 1
if reloadkaiko:
    import kaiko

    kc = kaiko.KaikoClient(api_key=apikey)
    pairs = ["eth-usd", "eth-usdt", "eth-usdc", "eth-dai"]
    exchanges = [
        "cbse",
        "bnce",
        "bnus",
        "krkn",
        "gmni",
        "huob",
        "usp2",
        "usp3",
        "ftxu",
        "ftxx",
    ]
    # exchanges=['cbse']
    oball = dict()
    for exchange in exchanges:
        ob = dict()
        for pair in pairs:
            tmp = kaiko.OrderBookAggregations(
                exchange,
                instrument=pair,
                interval="1d",
                start_time=start,
                end_time=end,
                client=kc,
            )
            ob[pair] = tmp.df
        dfob = pd.concat(ob)
        dfob["exchange"] = exchange
        oball[exchange] = dfob
    df = pd.concat(oball)
    df.to_pickle("data/kaiko_exchanges_eth_220202.pkl")
else:
    df = pd.read_pickle("data/kaiko_exchanges_eth_220202.pkl")


df.head(1)


# ------------
# today --------------------------------------
today = dt.datetime.utcnow()
end = today
# from datetime to string
end = end.strftime("%Y-%m-%d %H")

# 30 days ago --------------------------------------
N = 30
d = dt.timedelta(days=N)
start = today - d
# from datetime to string
start = start.strftime("%Y-%m-%d %H")
pairs = [
    "eth-usd",
    "eth-usdt",
    "eth-usdc",
    "eth-dai",
    "usdc-usdt",
    "dai-usdc",
    "link-eth",
    "wbtc-eth",
    "ftm-eth",
    "matic-eth",
    "comp-eth",
    "mkr-eth",
]
exchanges = ["cbse", "bnce", "krkn", "gmni", "ftxx"]
# exchanges=['cbse']

oball = dict()
for exchange in exchanges:
    ob = dict()
    for pair in pairs:
        try:
            print("Fetching: %s: %s" % (pair, exchange))
            tmp = kaiko.OrderBookAggregations(
                exchange,
                instrument=pair,
                interval="1d",
                start_time=start,
                end_time=end,
                client=kc,
            )
            ob[pair] = tmp.df
        except:
            print("no price: %s: %s" % (pair, exchange))
    dfob = pd.concat(ob)
    dfob["exchange"] = exchange
    oball[exchange] = dfob
df = pd.concat(oball)
df.reset_index().groupby(["level_0", "level_1"]
                         ).bid_volume2.median().to_clipboard()

df.to_pickle("data/kaiko_exchanges_longdatareq_20220202.pkl")

fields = [
    "mid_price",
    "spread",
    "bid_volume0_1",
    "bid_voume0_3",
    "bid_volume0_5",
    "bid_volume0_6",
    "bid_volume1",
    "bid_volume2",
    "bid_volume4",
    "bid_volume6",
    "bid_volume8",
    "bid_volume10",
    "ask_volume0_1",
    "ask_voume0_3",
    "ask_volume0_5",
    "ask_volume0_6",
    "ask_volume1",
    "ask_volume2",
    "ask_volume4",
    "ask_volume6",
    "ask_volume8",
    "ask_volume10",
]

idx = pd.IndexSlice
df.loc[idx[:, "eth-usdt", :],
       "bid_volume2"].droplevel(1).swaplevel().unstack().corr()

df.loc[idx[:, "link-eth", :],
       "bid_volume2"].droplevel(1).swaplevel().unstack().corr()

df.loc[idx[:, "link-eth", :],
       "bid_volume2"].droplevel(1).swaplevel().unstack().plot()
df.head(1)


len(exchanges)

#%%
