/ Replay CSV data into the tickerplant while preserving source row order.
tp:hopen `::localhost:5010;
quotes:("PSSSFFFF";enlist csv) 0:`data/orderbooks.csv;
fairs:("PSFFFFF";enlist csv) 0:`data/fair_values.csv;
publishQuote:{[row]
  tp(`.u.pub;`quote;enlist `ts`venue`market`bid`ask`bidSize`askSize!
    (row`ts;`$row`venue;`$row`market;row`bid;row`ask;row`bid_size;row`ask_size))
 };
publishFair:{[row]
  tp(`.u.pub;`fairValue;enlist `ts`market`fair`confidence`newsScore`imbalance!
    (row`ts;`$row`market;row`fair;row`confidence;row`news_score;row`imbalance))
 };
publishQuote each quotes;
publishFair each fairs;
show "replay complete";
exit 0;
