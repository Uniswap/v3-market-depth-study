import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


def genLiqRange(dft, tickspacing=60):
    #' Generate Liquidity Distribution (liquidity amount) based on default tick size
    #' returns dataframe with columns 'tickLower', 'amount', 'price'
    if not (
        all(dft.tickLower % tickspacing == 0) & all(dft.tickUpper % tickspacing == 0)
    ):
        print("fail tick window")
    rgn = np.arange(dft.tickLower.min(), dft.tickUpper.max() + 1, tickspacing)
    dfrgn = pd.DataFrame({"tickLower": rgn, "amount": 0}).set_index("tickLower")
    for i, row in dft.iterrows():
        dfrgn.loc[np.arange(row.tickLower, row.tickUpper, tickspacing), "amount"] = (
            dfrgn.loc[np.arange(row.tickLower, row.tickUpper, tickspacing), "amount"]
            + row["amount"]
        )  # /(row['tickUpper']-row['tickLower'])
    dfrgn = dfrgn.reset_index()
    dfrgn["price"] = 1e12 / (1.0001 ** dfrgn.tickLower)
    return dfrgn


def genLiqRangeOverTime(df, savefile="", tickspacing=60):
    #' Generate multiple dates of liquidity range
    dfs = df.groupby(["date", "tickLower", "tickUpper"]).amount.sum()
    dft2 = pd.DataFrame(dfs).reset_index()
    rgns = dict()
    for dt in dft2["date"].unique():
        rgns[dt] = genLiqRange(dft2.loc[dft2.date <= dt], tickspacing=tickspacing)
    dfrgns = pd.concat(rgns).droplevel(1).rename_axis("date")
    if savefile != "":
        dfrgns.to_pickle("dfrgns.pkl")
    return dfrgns


def genLiqRangeXNumeraire(dfrgn, tickspacing=60, alt=1):
    #' convert liquidity amount to dollar liquidity amount
    #' input dfrgn is a dataframe of liquidity distribution with columns 'tickLower', 'amount', 'P' as current price,  ['price' associated with tick]
    #' returns dataframe with columns: 'tickLower', 'amount', 'price', 'P', 'pa', 'pb', 'p', 'x', 'y',
    #' 'liqX', 'depth'
    dfrgn = dfrgn.assign(pa=lambda x: 1.0001 ** x.tickLower)
    dfrgn = dfrgn.assign(pb=lambda x: 1.0001 ** (x.tickLower + tickspacing))
    # dfrgn=dfrgn.assign(x=lambda x: x.amount*(x.pb**0.5-x.pa**0.5)/((x.pa*x.pb)**0.5))
    dfrgn["p"] = 1 / dfrgn.P * 1e12

    dfrgn.loc[dfrgn.p <= dfrgn.pa, "x"] = ( dfrgn.amount * (dfrgn.pb ** 0.5 - dfrgn.pa ** 0.5) / ((dfrgn.pa * dfrgn.pb) ** 0.5) / 1e6 )
    dfrgn.loc[(dfrgn.pa < dfrgn.p) & (dfrgn.p < dfrgn.pb), "x"] = ( dfrgn.amount * (dfrgn.pb ** 0.5 - dfrgn.p ** 0.5) / ((dfrgn.p * dfrgn.pb) ** 0.5) / 1e6 )
    dfrgn.loc[dfrgn.p >= dfrgn.pb, "x"] = 0

    dfrgn.loc[dfrgn.p <= dfrgn.pa, "y"] = 0
    dfrgn.loc[(dfrgn.pa < dfrgn.p) & (dfrgn.p < dfrgn.pb), "y"] = ( dfrgn.amount * (dfrgn.p ** 0.5 - dfrgn.pa ** 0.5) / 1e18 )
    dfrgn.loc[dfrgn.p >= dfrgn.pb, "y"] = ( dfrgn.amount * (dfrgn.pb ** 0.5 - dfrgn.pa ** 0.5) / 1e18 )

    if alt:
        # note that here P is the current price rather than the price at each tick
        dfrgn["liqX"] = 1 * dfrgn.x + dfrgn.P * dfrgn.y
    else:
        # convert liquidity using price at lower tick
        dfrgn["liqX"] = 1 * dfrgn.x + dfrgn.price * dfrgn.y
    return dfrgn


def genDepth(dfrgn, tickspacing=60,alt=1):
    #' Calculate dollar liquidity amount distribution and depth chart
    dfrgnD = genLiqRangeXNumeraire(dfrgn, tickspacing=tickspacing,alt=alt)
    #' Generate depth of any liquidity range/distribution by integrating across the range
    df1 = dfrgnD.loc[dfrgnD.price > dfrgnD.P].sort_values("price")
    df2 = dfrgnD.loc[dfrgnD.price <= dfrgnD.P].sort_values("price")
    df2["depth"] = df2.loc[::-1, "liqX"].cumsum()[::-1]
    df1 = df1.assign(depth=lambda x: x.liqX.cumsum())
    dfm = pd.concat([df2, df1])

    # depth=dfm.loc[(dfm.price>=dfm.P*0.97) & (dfm.price<=dfm.P*1.03)].liqX.sum()
    return dfm#[["date", "tickLower", "price", "P", "liqX", "depth"]]


def genDepthOverTime(dfrgns, tickspacing=60):
    #' Calls genDepth to getnerate full range of liquidity distribution, dollar liquidity and depth
    liqdist = list()
    for dt in dfrgns["date"].unique():
        liqdist.append(
            genDepth(dfrgns.loc[dfrgns.date == dt], tickspacing=tickspacing)
        )
    #     pd.concat(liqdist).to_pickle('data/liqdist_eth.pkl')
    dfliqdist = pd.concat(liqdist)
    return dfliqdist


def fillGranularDistribution(df, depthpct=0.02, returnDepth=1, tickspacing=60):
    # expand liquidity distribution granularity to 1 tick, effectively resampling tickspacing to 1 tick
    dft = df.copy()
    P = dft.P.values[0]
    if depthpct == 1:
        P_u = 0
        P_l = 1e9
        tick_u = dft.tickLower.max()
        tick_l = dft.tickLower.min()
    else:
        P_u = dft.P.values[0] * (1 - depthpct)
        P_l = dft.P.values[0] * (1 + depthpct)
        tick_u = (
            int(np.log((1 / P_u * 1e12)) / np.log(1.0001) / tickspacing) + 1
        ) * tickspacing
        tick_l = (
            int(np.log((1 / P_l * 1e12)) / np.log(1.0001) / tickspacing) - 1
        ) * tickspacing

    dft["liqXpertick"] = dft["liqX"] / tickspacing
    dft["tick_u"] = tick_u
    dft["tick_l"] = tick_l

    rgn = np.arange(tick_l, tick_u + 1, 1)
    dfrgn = pd.DataFrame({"tickLower": rgn, "depthattick": 0})
    dfrgn["price"] = 1e12 / (1.0001 ** dfrgn.tickLower)
    for i, row in dft[ ( (dft.tickLower >= dft.tick_l - tickspacing) & (dft.tickLower <= dft.tick_u + tickspacing) ) ].iterrows():
        dfrgn.loc[ (dfrgn.tickLower >= row.tickLower) & (dfrgn.tickLower <= row.tickLower + tickspacing), "depthattick", ] = row["liqXpertick"]
    depth = dfrgn[(dfrgn.price >= P_u) & (dfrgn.price <= P_l)].depthattick.sum()
    depthbid = dfrgn[(dfrgn.price >= P_u) & (dfrgn.price <= P)].depthattick.sum()
    depthask = dfrgn[(dfrgn.price >= P) & (dfrgn.price <= P_l)].depthattick.sum()
    if returnDepth:
        return depth, depthbid, depthask
    else:
        return dfrgn[(dfrgn.price >= P_u) & (dfrgn.price <= P_l)]


def fillGranularDistributionOverTime(liqdist, depthpct=0.02, tickspacing=60):
    # Generate depth time series by calling fillGranularDistribution for all dates
    depths = list()
    for dt in liqdist.date.unique():
        depths.append(
            fillGranularDistribution(
                liqdist.loc[liqdist.date == dt],
                depthpct=depthpct,
                returnDepth=1,
                tickspacing=tickspacing,
            )
        )
    dfdepth = pd.DataFrame(depths, index=pd.to_datetime(liqdist.date.unique())).rename(
        columns={0: "depth"}
    )
    dfdepth = dfdepth.reset_index().rename(
        columns={"index": "date", 1: "depthbid", 2: "depthask"}
    )
    dfdepth["date"] = pd.to_datetime(dfdepth.date)
    return dfdepth


def CalcAll(
    filein="../data/mintburn_usdceth3000_simple.csv",
    fileprice="../data/ethprice.csv",
    tickspacing=60,
    depthpct=0.02,
    address='0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8',
    bigquery=1
):
    dfprice = pd.read_csv(fileprice).rename(columns={"price": "P"})
    dfprice["date"] = pd.to_datetime(dfprice.date).dt.date

    if(bigquery):
        # read data from bigquery, a slightly different format than dune
        df = pd.read_csv(filein, dtype={'amount': float,
                         'amount0': float, 'amount1': float})
        df = df.loc[df.address == address]
        df = df.rename(columns={"lowertick": "tickLower",
                       "uppertick": "tickUpper", "block_timestamp": "call_block_time"})
    else:#dune
        df = pd.read_csv(filein)

    # conversions
    df["amount"] = df.amount.map(float)
    df = df.rename(columns={"lowertick": "tickLower", "uppertick": "tickUpper"})
    df["date"] = pd.to_datetime(df.call_block_time).dt.date

    # default liq distribution
    dfrgns = genLiqRangeOverTime(df, savefile="", tickspacing=tickspacing)
    # merge in price
    dfrgns = dfrgns.reset_index()
    dfrgns["date"] = pd.to_datetime(dfrgns.date)
    dfprice["date"] = pd.to_datetime(dfprice.date)
    dfrgns = pd.merge(dfrgns, dfprice, on="date")

    # calc depth distribution based on default tick spacing
    liqdist = pd.DataFrame(genDepthOverTime(dfrgns, tickspacing=tickspacing))

    # expand into granular distribution and depth
    dfdepth = fillGranularDistributionOverTime(liqdist, depthpct=depthpct, tickspacing=tickspacing)
    return dfdepth, liqdist, dfrgns
