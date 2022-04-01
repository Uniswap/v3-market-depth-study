import numpy as np
import pandas as pd
import math
import graphql_getpoolstat
import os
from tqdm import tqdm

def _genLiqRange(df,ts=60,getblocks=[]):
    #' generate granular liquidity at each tick spacing from mint/burn ranges and save historical states for blocks in getblock
    dft=df.loc[df.amount!=0].copy()
    if(type(getblocks)!=list):
        getblocks=list(getblocks)

    tmin=dft.tickLower.min()
    tmax=dft.tickUpper.max()
    Nt=int((tmax-tmin)/ts)

    blockN=dft.block_number.values

    getblocks.sort()

    tl=list(map(int,(dft.tickLower.values-tmin)/ts))#
    tu=list(map(int,(dft.tickUpper.values-tmin)/ts))
    tamount=dft.amount.values


    ll=np.zeros(Nt)
    # store historical liquidity states at defined block numbers
    if (len(getblocks)==0):
        getblocks=[max(blockN)]
    lm=np.zeros((Nt,len(getblocks)))
    j=0 # counter for blockN
    for i in range(len(tl)-1):
        ll[tl[i]:tu[i]]=ll[tl[i]:tu[i]]+tamount[i]
        # save liquidity state at block getblocks[j]
        ## could be multiple blocks per
        if((blockN[i] in getblocks) and (blockN[i+1]!=blockN[i])):
            lm[:,j]=ll
            j+=1
    #last tx
    i+=1
    ll[tl[i]:tu[i]]=ll[tl[i]:tu[i]]+tamount[i]
    if(blockN[i] in getblocks):
        lm[:,j]=ll.copy()

    if(j!=(len(getblocks)-1)):
        print('error: cannot find all blocks')
        print(j)
    dfout=pd.DataFrame(ll,index=range(tmin,tmax,ts))
    dfhist=pd.DataFrame(lm.transpose(),columns=range(tmin,tmax,ts),index=getblocks)
    # state at every single block
#     lm=np.zeros((Nt,len(tl)))
#     lm[tl[0]:tu[0],0]=tamount[0]
#     for i in range(1,len(tl)-1):
#         lm[tl[i]:tu[i],i]=lm[tl[i]:tu[i],i-1]+tamount[i]
#     dfout=pd.DataFrame(lm.transpose(),columns=range(tmin,tmax,ts),index=dft.block_number)
    return dfout,dfhist

def genLiqRange(df,ts=60):
    # wrapper around _genliqrange2
    df=df.sort_values('block_number')
    _,dfh = _genLiqRange(df,ts=ts,getblocks=df.loc[df.amount!=0].groupby('date').block_number.last().values)
    tmp=pd.merge(dfh.reset_index(),df.loc[:,['block_number','block_timestamp']].drop_duplicates('block_number'),how='left',left_on='index',right_on='block_number')
    dfout=pd.DataFrame(tmp.drop(columns='index').set_index(['block_number','block_timestamp']).stack()).reset_index().rename(columns={'level_2':'tickLower',0:'amount'})
    return dfout

def calc_liquidity_at_tick(i,din, s=60, p=np.nan):
    #' calculate liquidity at tick range i to i+s given a dataframe/dict din that contains columns "tickLower","amount" and current price "p" in raw form
    j=np.floor(i/s)*s
    pa=1.0001**j
    pb=1.0001**(j+s)
    if(type(din)==dict):
        try:
            Ljs=din[j]
        except:
            # import pdb; pdb.set_trace()
            # print(i)
            # print(j)
            # print(din)
            return 0
    else:
        Ljs=din.loc[din.tickLower==j,'amount'].values[0]
    if (math.isnan(p)):
        p=din.loc[din.tickLower==j,'p'].values[0]
    if (p>=pb):
#         print('p>=pb')
        xjs=0
        yjs=Ljs*(np.sqrt(pb)-np.sqrt(pa))
    elif (p<=pa):
#         print('p<=pa')
        xjs=Ljs/np.sqrt(pa)-Ljs/np.sqrt(pb)
        yjs=0
    elif (pa<=p<pb):
        xjs=Ljs/np.sqrt(p)-Ljs/np.sqrt(pb)
        yjs=Ljs*(np.sqrt(p)-np.sqrt(pa))
    lambjs=xjs+1/p*yjs
    li=lambjs/s
    return li

def calc_market_depth(df,i0=198120,delta=0.02,ts=60,plusminus=True,logdelta=False,diagnosis=False,decimals0=6):
    # ' returns market depth given a dataframe with columns 'tickLower', 'amount' and current tick i0,
    # df has a mapping between tick and liqudity in raw form and current price p
    if logdelta:
        d=int((delta+np.log(1.0001**i0))/np.log(1.0001)-i0)
    else:
        d=int(np.log((delta+1)*1.0001**i0)/(np.log(1.0001))-i0)

    if (plusminus):
        r=np.arange(i0-d,i0+d)
    else:
        r=np.arange(i0,i0+d,np.sign(d))

    # dataframe to dict and price to scalar for faster processing
    din=dict(df.set_index('tickLower').amount)
    p=1.0001**i0
    if(diagnosis):
        # returns liquidity at each tick spacing
        lis=list()
        print('d',d)
        print('min',min(r))
        print('max',max(r))
        for i in r:
            lis.append(calc_liquidity_at_tick(i,din=din,s=ts,p=p)/(10**decimals0))
        m=sum(lis)
        print(d*2)
        print(len(lis))
        dd=pd.DataFrame({'tickLower':r,'depthattick':lis})
        return m,dd
    else:
        m=0
        for i in r:
            m+=calc_liquidity_at_tick(i,din=din,s=ts,p=p)
        return m/(10**(decimals0))

def genMarketDepth(dfm,delta=0.02,ts=60,plusminus=True,logdelta=True,decimals0=6):
    # generate time series of market depth for specific delta
    # dfm contains columns "block_number", 'tickLower', 'amount', 'currenttick' (for tick associated with current price)
    blockN=dfm.block_number.unique()
    if(abs(delta)<1e-10):
        md=0
    else:
        md=[calc_market_depth(dfm.loc[dfm.block_number==bn],
                            i0=int(dfm.loc[dfm.block_number==bn,'currenttick'].values[0]),delta=delta,ts=ts,plusminus=plusminus,logdelta=logdelta,decimals0=decimals0) for bn in blockN]
    dfout=pd.DataFrame(md,blockN,columns=['marketdepth'])
    return dfout



def LimitTickRange(df,dfprice,nstd=10):
    #' limit tick range to nstd of min and max price
    minticklimit=int(dfprice.currenttick.min()-nstd*dfprice.currenttick.std())
    maxticklimit=int(dfprice.currenttick.max()+nstd*dfprice.currenttick.std())
    # print(dfprice.currenttick.std())
    df=df.loc[(df.tickLower>=minticklimit) & (df.tickLower<=maxticklimit)]
    return df


def feetier2tickspacing(feetier):
    return {
        100: 1,
        500: 10,
        3000: 60,
        10000: 200
    }.get(feetier)



def genLiqRangeXNumeraire(dfrgn, tickspacing=60,decimals0=6,decimals1=18,pricemode=0):
    #' convert liquidity amount to dollar liquidity amount
    #' input dfrgn is a dataframe of liquidity distribution with columns 'tickLower', 'amount', 'price' as current price,  ['price' associated with tick]
    #' returns dataframe with columns: 'tickLower', 'amount', 'price',  'pa', 'pb', 'p', 'x', 'y',
    #' 'liqX', 'depth'
    dfrgn = dfrgn.assign(pa=lambda x: 1.0001 ** x.tickLower)
    dfrgn = dfrgn.assign(tickUpper=lambda x: (x.tickLower + tickspacing))
    dfrgn = dfrgn.assign(pb=lambda x: 1.0001 ** (x.tickLower + tickspacing))

    if (pricemode):
        dfrgn["p"] = 1 / dfrgn.price * (10**(decimals1-decimals0))
        dfrgn.loc[dfrgn.p <= dfrgn.pa, "x"] = ( dfrgn.amount * (dfrgn.pb ** 0.5 - dfrgn.pa ** 0.5) / ((dfrgn.pa * dfrgn.pb) ** 0.5) / 10**decimals0 )
        dfrgn.loc[(dfrgn.pa < dfrgn.p) & (dfrgn.p < dfrgn.pb), "x"] = ( dfrgn.amount * (dfrgn.pb ** 0.5 - dfrgn.p ** 0.5) / ((dfrgn.p * dfrgn.pb) ** 0.5) / 10**decimals0 )
        dfrgn.loc[dfrgn.p >= dfrgn.pb, "x"] = 0

        dfrgn.loc[dfrgn.p <= dfrgn.pa, "y"] = 0
        dfrgn.loc[(dfrgn.pa < dfrgn.p) & (dfrgn.p < dfrgn.pb), "y"] = ( dfrgn.amount * (dfrgn.p ** 0.5 - dfrgn.pa ** 0.5) / 10**decimals1 )
        dfrgn.loc[dfrgn.p >= dfrgn.pb, "y"] = ( dfrgn.amount * (dfrgn.pb ** 0.5 - dfrgn.pa ** 0.5) / 10**decimals1 )
    else:
        dfrgn = dfrgn.assign(p=lambda x: 1.0001 ** x.currenttick)
        dfrgn.loc[np.floor(dfrgn.currenttick/tickspacing)*tickspacing < (dfrgn.tickLower), "x"] = ( dfrgn.amount * (dfrgn.pb ** 0.5 - dfrgn.pa ** 0.5) / ((dfrgn.pa * dfrgn.pb) ** 0.5) / 10**decimals0 )
        dfrgn.loc[np.floor(dfrgn.currenttick/tickspacing)*tickspacing==dfrgn.tickLower, "x"] = ( dfrgn.amount * (dfrgn.pb ** 0.5 - dfrgn.p ** 0.5) / ((dfrgn.p * dfrgn.pb) ** 0.5) / 10**decimals0 )
        dfrgn.loc[np.floor(dfrgn.currenttick/tickspacing)*tickspacing>=(dfrgn.tickLower+tickspacing), "x"] = 0

        dfrgn.loc[np.floor(dfrgn.currenttick/tickspacing)*tickspacing < (dfrgn.tickLower), "y"] = 0
        dfrgn.loc[np.floor(dfrgn.currenttick/tickspacing)*tickspacing==dfrgn.tickLower, "y"] = ( dfrgn.amount * (dfrgn.p ** 0.5 - dfrgn.pa ** 0.5) / 10**decimals1 )
        dfrgn.loc[np.floor(dfrgn.currenttick/tickspacing)*tickspacing>=(dfrgn.tickLower+tickspacing), "y"] = ( dfrgn.amount * (dfrgn.pb ** 0.5 - dfrgn.pa ** 0.5) / 10**decimals1 )

        dfrgn['side']=np.nan
        dfrgn.loc[np.floor(dfrgn.currenttick/tickspacing)*tickspacing < (dfrgn.tickLower), "side"] = -1
        dfrgn.loc[np.floor(dfrgn.currenttick/tickspacing)*tickspacing==dfrgn.tickLower, "side"] = 0
        dfrgn.loc[np.floor(dfrgn.currenttick/tickspacing)*tickspacing>=(dfrgn.tickLower+tickspacing), "side"] = 1

    dfrgn["liqX"] = 1 * dfrgn.x + dfrgn.price * dfrgn.y
    return dfrgn

def pipeMarketDepth(filein = 'data/mintburnall_bigquery.csv',address='0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8',pctchg=[-.05, -.02, .02, .05], UseSubgraph=True):
    #' create market depth from mintburn file (from either dune or gcpbigquery) given address, pctchg
    #' queries either subgraph or gcpbigquery for historical pricees
    if UseSubgraph:
        poolstats=graphql_getpoolstat.subgraph_getpoolstats(address)
        decimals0=int(poolstats['token0']['decimals'])
        decimals1=int(poolstats['token1']['decimals'])
        symbol0=poolstats['token0']['symbol']
        symbol1=poolstats['token1']['symbol']
        feeTier=int(poolstats['feeTier'])
        ts=feetier2tickspacing(feeTier)
    else:
        # use internal server (non-public)
        import dbtools
        poolstats=dbtools.getpoolstats(address)
        decimals0=int(poolstats['decimals0'])
        decimals1=int(poolstats['decimals1'])
        symbol0=poolstats['token0symbol']
        symbol1=poolstats['token1symbol']
        feeTier=int(poolstats['fee'])
        ts=int(poolstats['tickSpacing'])
    print(symbol0,decimals0, symbol1, decimals1,feeTier,ts)

    df = pd.read_csv(filein, dtype={'amount': float, 'amount0': float, 'amount1': float})
    df = df.loc[df.address == address]
    df = df.loc[df.amount!=0]
    df["date"] = pd.to_datetime(df.block_timestamp).dt.date
    df=df.sort_values('block_number')

    bndate=df.loc[df.amount!=0].groupby('date').block_number.last()

    if UseSubgraph:
        fileprice='tickprice_%s.csv' % address
        if (not(os.path.exists(fileprice))):
            print('getting prices:')
            bndate.to_csv('tmp_bndate.csv')
            os.system('python3.9 graphql_getprice.py %s %s' % (address,'tmp_bndate.csv'))
        dfprice=pd.read_csv(fileprice)[['bn','token0Price','tick']].rename(columns={'bn':'block_number','token0Price':'price','tick':'currenttick'})
    else:
        # use internal server (non-public)
        dfprice=dbtools.getpriceatblocknumber(address=address,block_numbers=bndate.values).rename(columns={'tick':'currenttick'})[['block_number','price','currenttick']]


    # reduce size of range if 1tick spacing
    if(ts==1):
        df=LimitTickRange(df,dfprice,nstd=5).copy()

    dfl = genLiqRange(df,ts=ts)
    # reduce bounds again to simplify market depth calculations
    dfl=LimitTickRange(dfl,dfprice,nstd=5).copy()

    dfl['block_timestamp']=pd.to_datetime(dfl.block_timestamp)
    dfl['date']=dfl.block_timestamp.dt.date

    dfm=pd.merge(dfl,dfprice,on='block_number',how='left').dropna()

    tmplist=list()
    for pc in tqdm(pctchg):
        tmp=genMarketDepth(dfm,delta=pc,ts=ts, plusminus=False,decimals0=decimals0,logdelta=False)
        tmp['pct']=pc
        tmplist.append(tmp)

    dfmktdepth=pd.concat(tmplist)

    blockdate=dfm.loc[:,['date','block_number']].drop_duplicates()
    blockdate['date']=pd.to_datetime(blockdate.date)
    dfmktdepth=pd.merge(dfmktdepth.reset_index(),blockdate,left_on='index',right_on='block_number').drop('index',axis=1)
    return dfmktdepth


def genMarketDepthCrossSection(df,decimals0=6,ts=60,pctchg=np.round(np.arange(-.1,.11,.01)/.01)*.01):
#     generate cross-section of market depth for pct chg
    tmplist=list()
    for pc in pctchg:
        tmp=genMarketDepth(df,delta=pc,ts=ts, plusminus=False,decimals0=decimals0,logdelta=False)
        tmp['pct']=pc
        tmplist.append(tmp)
    dfmktdepth=pd.concat(tmplist)
    return dfmktdepth

def calcV2DepthfromTDL(total_deposit_locked,p,delta=np.round(np.arange(-.1,.11,.01)/.01)*.01):
    # calculate v2 depth from TDL and price (y/x)
    x=total_deposit_locked/2
    L=x*np.sqrt(p)
    return calcV2Depth(L,p0=p,delta=delta)

def calcV2Depth(L,p0,delta=np.round(np.arange(-.1,.11,.01)/.01)*.01):
    a=np.abs(L/np.sqrt((1+delta)*p0)-L/np.sqrt(p0))
    dfa=pd.DataFrame({'pct':delta,'v2depth':a})
    return dfa

def calcV2DepthfromV3XYP(x,y,price,delta=np.arange(-.02,.04,.02)):
    #' calc v2 depth given v3 total X Y and current price in x/y (e.g. usd/eth=2600)'
    tdl=x+y*price
    xadj=tdl/2
    yadj=tdl/2
    x2=xadj
    y2=yadj/price
    L=np.sqrt(x2*y2)
    p0=y2/x2
    a=np.abs(L/np.sqrt((1+delta)*p0)-x2)
    dfa=pd.DataFrame({'pct':delta,'v2depth':a})
    return dfa

def getV2EquivalentDepthfromV3(dfm,ts,decimals0,decimals1,delta=np.array([-.02,.02])):
    #' Generate V2 equivalent market depth from v3 liquidity distribution
    if (type(delta)==list):
        delta=np.array(delta)
    dfm2=genLiqRangeXNumeraire(dfm,tickspacing=ts,decimals0=decimals0,decimals1=decimals1,pricemode=0)
    liqsumbydate=dfm2.groupby(['date','block_number']).agg({'x':sum,'y':sum,'liqX':sum,'amount':sum,'currenttick':'mean','price':'mean','p':'mean'})
    tmp=list()
    for i,ll in liqsumbydate.iterrows():
        tmpdf=calcV2DepthfromV3XYP(x=ll.x, y=ll.y, price=ll.price,delta=delta)
        tmpdf['date']=i[0]
        tmpdf['block_number']=i[1]
        tmp.append(tmpdf)
    v2d=pd.concat(tmp)
    return v2d
