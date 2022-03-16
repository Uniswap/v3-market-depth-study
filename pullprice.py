from google.oauth2 import service_account
import pandas as pd
from graphql_getprice import subgraph_pull

def gethistprice(poolid='0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8'):
    from google.cloud import bigquery
    credentials = service_account.Credentials.from_service_account_file('/home/gordon/bigquerykey.json')
    project_id='mimetic-design-338620'
    client = bigquery.Client(project=project_id)
    query='''
      SELECT
        distinct(block_number)
      FROM
        `mimetic-design-338620.uniswap.MintBurn`
      WHERE
        address='%s'
    ''' % poolid
    bn = pd.io.gbq.read_gbq(query, project_id=project_id, dialect='standard',credentials=credentials)

    tmplist=list()
    from tqdm import tqdm
    for i in tqdm(range(len(bn))):
        bi=bn.iloc[i].block_number
        ctick=subgraph_pull(poolid,bi)
        ctick['bn']=bi
        tmplist.append(ctick)
    df=pd.DataFrame.from_dict(tmplist)
    # df.iloc[1:].to_csv('tickprice_%s.csv' % poolid)
    df['address']=poolid
    pd.io.gbq.to_gbq(df,'uniswap.px',project_id,if_exists='append',credentials=credentials)


addresses=["0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640","0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8","0x7bea39867e4169dbe237d55c8242a8f2fcdcc387","0x11b815efb8f581194ae79006d24e0d814b7697f6","0x4e68ccd3e89f51c3074ca5072bbac773960dfa36","0xc5af84701f98fa483ece78af83f11b6c38aca71d","0x60594a405d53811d3bc4766596efd80fd545a270","0xc2e9f25be6257c210d7adf0d4cd6e3e881ba25f8"]

for ad in addresses:
    print(ad)
    gethistprice(ad)
