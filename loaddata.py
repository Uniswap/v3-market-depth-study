import pandas as pd
from dbtools import *


df=bigquery("select * from uniswap.MintBurn where amount!=0")

df.to_csv('data/mintburn.csv')
