import pandas as pd
from coinpaprika import client as Coinpaprika
%pwd
%cd ../../marketdepthstudy


client = Coinpaprika.Client()
# client.coins()

raw = client.historical(
    "eth-ethereum", start="2021-05-01T00:00:00Z", limit=5000, interval='1d')
df = pd.DataFrame(raw)
df2 = df[['timestamp', 'price']]
df2.columns = ['date', 'price']
df2.to_csv('data/ethprice_latest.csv', index=False)
