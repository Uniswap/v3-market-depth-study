import pandas as pd
from depthutil2 import *
import sys

if __name__ == "__main__":
    address='0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8'
    # address='0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640'
    # address='0x4e68ccd3e89f51c3074ca5072bbac773960dfa36'
    # address='0x5777d92f208679db4b9778590fa3cab3ac9e2168' # usdc dai
    # address='0xcbcdf9626bc03e24f779434178a73a0b4bad62ed' #btc-eth
    # address='0x99ac8ca7087fa4a2a1fb6357269965a2014abc35' #btc-eth
    EXAMPLEONLY=0
    LOADMINTBURN=0

    if len(sys.argv) > 1:
        address = sys.argv[1]
    if len(sys.argv) > 2:
        EXAMPLEONLY= sys.argv[2]
    if len(sys.argv) > 3:
        LOADMINTBURN= sys.argv[3]


    if LOADMINTBURN:
        #' Load mint burn history from GCP server by running bigquery_mintburn.sql or run dune mintburn_dune.sql and download data
        from dbtools import *
        df=bigquery("select * from uniswap.MintBurn where amount!=0")
        df.to_csv('data/mintburnall_bigquery.csv')

    # Generate Market Depth at +- 2%
    # For example, use pre-saved price file; otherwise download from subgraph or GCP

    if EXAMPLEONLY:
        print('Calculating historical market depth example on WETH/USDC 30 bps pool only using pre-saved price file')
        md=pipeMarketDepth(filein = 'data/mintburnall_bigquery.csv', address='0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8',pctchg=[-.02,.02],UseSubgraph=True,UsePriceFile='data/tickprice_0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8.csv')
    else:
        print('download price from subgraph...')
        md=pipeMarketDepth(filein = 'data/mintburnall_bigquery.csv', address=address,pctchg=[-.02,.02],UseSubgraph=True,UsePriceFile='')

    print('Market depth description:')
    print(md.describe())
    md.to_csv('output/example_%s.csv' % address)
    print('Plots saved in output folder')
    # +2% market depth
    fig=md.loc[md.pct==.02].plot('date','marketdepth').get_figure()
    fig.savefig('output/marketdepthhistorical_example.png')

    # +/-2% market depth
    fig=md.groupby('date').sum().marketdepth.plot().get_figure()
    fig.savefig('output/marketdepthhistorical_example2.png')
