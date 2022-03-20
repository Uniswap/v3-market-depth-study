import pandas as pd
from dbhelper import *


df=gbqquery("select * from uniswap.MintBurn where amount!=0")

df.to_csv('data/mintburn.csv')





aa
