import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def genLiqRange(dft,tickwindow=60):
    #' Generate Liquidity Distribution (liquidity amount) based on default tick size
    if not(all(dft.tickLower % tickwindow==0) & all(dft.tickUpper % tickwindow==0)):
        print('fail tick window')
    rgn=np.arange(dft.tickLower.min(),dft.tickUpper.max()+1,tickwindow)
    dfrgn=pd.DataFrame({'tickLower':rgn,'amount':0}).set_index('tickLower')
    for i,row in dft.iterrows():
        dfrgn.loc[np.arange(row.tickLower, row.tickUpper,tickwindow),'amount']=dfrgn.loc[np.arange(row.tickLower, row.tickUpper,tickwindow),'amount']+row['amount']#/(row['tickUpper']-row['tickLower'])
    dfrgn=dfrgn.reset_index()
    dfrgn['price']=1e12/(1.0001**dfrgn.tickLower)
    return dfrgn

def genLiqRangeOverTime(df,savefile='',tickwindow=60):
    #' Generate multiple dates of liquidity range
    dfs=df.groupby(['date','tickLower','tickUpper']).amount.sum()
    dft2=pd.DataFrame(dfs).reset_index()
    rgns=dict()
    for dt in dft2["date"].unique():
        rgns[dt]=genLiqRange(dft2.loc[dft2.date<=dt],tickwindow=tickwindow)
    dfrgns=pd.concat(rgns).droplevel(1).rename_axis('date')
    if (savefile!=''):
        dfrgns.to_pickle('dfrgns.pkl')
    return dfrgns



def calcdollarliq(dfrgn,tickwindow=60,alt=0):
    # convert liquidity amount to dollar liquidity amount
    dfrgn=dfrgn.assign(pa=lambda x: 1.0001**x.tickLower)
    dfrgn=dfrgn.assign(pb=lambda x: 1.0001**(x.tickLower+tickwindow))
    # dfrgn=dfrgn.assign(x=lambda x: x.amount*(x.pb**0.5-x.pa**0.5)/((x.pa*x.pb)**0.5))
    dfrgn['p']=1/dfrgn.P*1e12

    dfrgn.loc[dfrgn.p <= dfrgn.pa,'x']=dfrgn.amount*(dfrgn.pb**0.5-dfrgn.pa**0.5)/((dfrgn.pa*dfrgn.pb)**0.5)/1e6
    dfrgn.loc[(dfrgn.pa<dfrgn.p) & (dfrgn.p<dfrgn.pb),'x']=dfrgn.amount*(dfrgn.pb**0.5-dfrgn.p**0.5)/((dfrgn.p*dfrgn.pb)**0.5)/1e6
    dfrgn.loc[dfrgn.p>=dfrgn.pb,'x']=0

    dfrgn.loc[dfrgn.p <= dfrgn.pa,'y']=0
    dfrgn.loc[(dfrgn.pa<dfrgn.p) & (dfrgn.p<dfrgn.pb),'y']=dfrgn.amount*(dfrgn.p**0.5-dfrgn.pa**0.5)/1e18
    dfrgn.loc[dfrgn.p>=dfrgn.pb,'y']=dfrgn.amount*(dfrgn.pb**0.5-dfrgn.pa**0.5)/1e18

    # convert liquidity using price at lower tick 
    dfrgn['liqusd']=1*dfrgn.x+dfrgn.price*dfrgn.y
    if alt:
        # note that here P is the current price rather than the price at each tick
        dfrgn['liqusd']=1*dfrgn.x+dfrgn.P*dfrgn.y
    return dfrgn


def calcDepth(dfrgn):
    # Generate depth of any liquidity range/distribution by intergrating across the range
    df1=dfrgn.loc[dfrgn.price>dfrgn.P].sort_values('price')
    df2=dfrgn.loc[dfrgn.price<=dfrgn.P].sort_values('price')
    df2['depth']=df2.loc[::-1,'liqusd'].cumsum()[::-1]
    df1=df1.assign(depth=lambda x: x.liqusd.cumsum())
    dfm=pd.concat([df2,df1])
    return dfm

def calc_usdliq_depth(dfrgn,tickwindow=60):
    #' Calculate dollar liquidity distribution and depth chart
    dfrgn=calcdollarliq(dfrgn,tickwindow=tickwindow)
    dfm=calcDepth(dfrgn)
    # depth=dfm.loc[(dfm.price>=dfm.P*0.97) & (dfm.price<=dfm.P*1.03)].liqusd.sum()
    return dfm[['date','tickLower','price','P','liqusd','depth']]


def genFullLiqDistribution(dfrgns,tickwindow=60):
    #' Calls calc_usdliq_depth to getnerate full range of liquidity distribution, dollar liquidity and depth
    liqdist=list()
    for dt in dfrgns["date"].unique():
        liqdist.append(calc_usdliq_depth(dfrgns.loc[dfrgns.date==dt],tickwindow=tickwindow))
#     pd.concat(liqdist).to_pickle('data/liqdist_eth.pkl')
    dfliqdist=pd.concat(liqdist)
    return dfliqdist

def expandliqdistrib(df,depthpct=0.02,returnDepth=1,tickwindow=60):
    # expand liquidity distribution granularity to 1 tick for a single date
    dft=df.copy()
    P=dft.P.values[0]
    if (depthpct==1):
        P_u=0
        P_l=1e9
        tick_u=dft.tickLower.max()
        tick_l=dft.tickLower.min()
    else:
        P_u=dft.P.values[0]*(1-depthpct)
        P_l=dft.P.values[0]*(1+depthpct)
        tick_u=(int(np.log((1/P_u*1e12))/np.log(1.0001)/tickwindow)+1)*tickwindow
        tick_l=(int(np.log((1/P_l*1e12))/np.log(1.0001)/tickwindow)-1)*tickwindow

    dft['liqusdpertick']=dft['liqusd']/tickwindow
    dft['tick_u']=tick_u
    dft['tick_l']=tick_l

    rgn=np.arange(tick_l,tick_u+1,1)
    dfrgn=pd.DataFrame({'tickLower':rgn,'depthattick':0})
    dfrgn['price']=1e12/(1.0001**dfrgn.tickLower)
    for i,row in dft[((dft.tickLower>=dft.tick_l-tickwindow) & (dft.tickLower<=dft.tick_u+tickwindow))].iterrows():
        dfrgn.loc[(dfrgn.tickLower>=row.tickLower) & (dfrgn.tickLower<=row.tickLower+tickwindow),'depthattick']=row['liqusdpertick']
    depth=dfrgn[(dfrgn.price>=P_u) & (dfrgn.price<=P_l)].depthattick.sum()
    depthbid=dfrgn[(dfrgn.price>=P_u) & (dfrgn.price<=P)].depthattick.sum()
    depthask=dfrgn[(dfrgn.price>=P) & (dfrgn.price<=P_l)].depthattick.sum()
    if returnDepth:
        return depth,depthbid,depthask
    else:
        return dfrgn[(dfrgn.price>=P_u) & (dfrgn.price<=P_l)]

def genDepthTS(liqdist,depthpct=0.02,tickwindow=60):
    # Generate depth time series by calling expandliqdistrib for all dates
    depths=list()
    for dt in liqdist.date.unique():
        depths.append(expandliqdistrib(liqdist.loc[liqdist.date==dt],depthpct=depthpct,returnDepth=1,tickwindow=tickwindow))
    dfdepth=pd.DataFrame(depths,index=pd.to_datetime(liqdist.date.unique())).rename(columns={0:'depth'})
    dfdepth=dfdepth.reset_index().rename(columns={'index':'date',1:'depthbid',2:'depthask'})
    dfdepth['date']=pd.to_datetime(dfdepth.date)
    return dfdepth


def CalcAll(filein='../data/mintburn_usdceth3000_simple.csv', fileprice='../data/ethprice.csv',tickwindow=60,depthpct=0.02):
    dfprice=pd.read_csv(fileprice).rename(columns={'price':'P'})
    dfprice['date']=pd.to_datetime(dfprice.date).dt.date

    df=pd.read_csv(filein)
    df['amount']=df.amount.map(float)
    df=df.rename(columns={'lowertick':'tickLower','uppertick':'tickUpper'})
    df['date']=pd.to_datetime(df.call_block_time).dt.date

    # default liq distribution
    dfrgns=genLiqRangeOverTime(df,savefile='',tickwindow=tickwindow)
    # merge in price and adhoc filter
    dfrgns=dfrgns.reset_index()
    dfrgns['date']=pd.to_datetime(dfrgns.date)
    dfprice['date']=pd.to_datetime(dfprice.date)

    dfrgns=pd.merge(dfrgns,dfprice,on='date')
    # dfrgns=dfrgns.loc[dfrgns.price<6000]
    # Calc usd liquidity
    liqdist=pd.DataFrame(genFullLiqDistribution(dfrgns,tickwindow=tickwindow))
    # generate 1-tick distribution and depth
    dfdepth=genDepthTS(liqdist,depthpct=depthpct,tickwindow=tickwindow)
    return dfdepth,liqdist,dfrgns
