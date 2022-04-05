This project calculates current and historical market depth from Uniswap V3 liquidity pools and preform comparison against centralized exchange market depths.


Data requirement:
 - Bigquery/Dune Analytics: to obtain all mint and burn events for each pool
   - Run bigquery_mintburn.sql on GCP
 - Subgraph: to obtain block-level price data for pools (alternatively use Bigquery)
 - Coinpaprika API (optional): to get historical price externally
 - Kaiko API (optional): to obtain centralized exchange market depth



Files:
 - depthutil.py  Functions used to construct liquidity distribution retrospectively and generate market depth at each historical date and level
 - depthutil2.py V2 version (more efficient) of constructing liquidity distribution and calculating market depth 
 - example.py Simple example of market depth calculation
 - genbulkMarketDepth.py for bulk calculation and upload to GCP