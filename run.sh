#!/bin/bash

mkdir data
mkdir output
curl https://storage.googleapis.com/uniswap-data/mintburnall_bigquery.csv.gz --output data/mintburnall_bigquery.csv.gz
gzip -d data/mintburnall_bigquery.csv.gz

curl https://storage.googleapis.com/uniswap-data/tickprice_0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8.csv.gz  --output data/tickprice_0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8.csv.gz
gzip -d data/tickprice_0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8.csv.gz


python3 example.py 0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8 1

open output/marketdepthhistorical_example.png

open output/marketdepthhistorical_example2.png

open output/example_0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8.csv