/ analytics.q
/ q/kdb+ analytics layer for EventEdge.

DATA:"data/";

/ Option B schemas:
/ orderbooks.csv:
/ ts,venue,market,token_id,bid,ask,bid_size,ask_size
/
/ fair_values.csv:
/ ts,market,fair,confidence,prior,news_score,likelihood_ratio
/
/ settlements.csv:
/ market,payout

loadOrderbooks:{[path]
  t:("PSSSFFFF"; enlist csv) 0: `$path;
  t:update
      mid:(bid+ask)%2,
      spread:ask-bid,
      imbalance:$[0f=bid_size+ask_size;0f;(bid_size-ask_size)%(bid_size+ask_size)]
    from t;
  t
 };

loadFairValues:{[path]
  ("PSFFFFFF"; enlist csv) 0: `$path
 };

loadSettlements:{[path]
  ("SF"; enlist csv) 0: `$path
 };

orderbooks:loadOrderbooks DATA,"orderbooks.csv";
fairValues:loadFairValues DATA,"fair_values.csv";
settlements:loadSettlements DATA,"settlements.csv";

/ Latest quote per market
latestQuotes:{[] select by market from orderbooks};

/ Time bars over market-implied probability
bars:{[bucket]
  select
      open:first mid,
      high:max mid,
      low:min mid,
      close:last mid,
      avgSpread:avg spread,
      avgImbalance:avg imbalance
    by market, bucket:bucket xbar ts
    from orderbooks
 };

/ Join latest quote with latest fair value and compute trade edge
latestMispricing:{[]
  q:select by market from orderbooks;
  f:select by market from fairValues;
  r:q lj `market xkey f;
  update edge:fair-mid from r
 };

/ Candidate trades from q analytics
candidateTrades:{[minEdge;maxSpread]
  select
      ts,
      venue,
      market,
      bid,
      ask,
      mid,
      fair,
      edge,
      spread,
      confidence
    from latestMispricing[]
    where abs edge > minEdge, spread < maxSpread
 };

/ Settlement-aware realized value of a YES inventory table:
/ expected pos schema: ([] market:`A`B; qty:10 20)
settlePositions:{[pos]
  p:pos lj `market xkey settlements;
  update settlementValue:qty*payout from p
 };