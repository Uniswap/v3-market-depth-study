

This project calculates current and historical market depth from Uniswap V3 liquidity pools and preform comparison against centralized exchange market depths.


Data requirement:
 - Bigquery/Dune Analytics: to obtain all mint and burn events for each pool
 - Subgraph: to obtain block-level price data for pools
 - Coinpaprika API (optional): to get historical price externally
 - Kaiko API (optional): to obtain centralized exchange market depth



Files:
 - depthutil.py  Functions used to construct liquidity distribution retrospectively and generate market depth at each historical date and level
 - depthutil2.py Alternative ways of construction liquidity distribution and calculating market depth (more efficient)
 - example.py Simple example of market depth calculation  
 - MarketDepthStudy.ipynb  Notebook used to construct key results
