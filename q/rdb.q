/ Real-time subscriber. Start after tick.q with: q q/rdb.q -p 5011
tpPort:5010;
if[0<count .z.x; tpPort:"J"$.z.x 0];
tp:hopen `::localhost:tpPort;
upd:{[table;rows] set[table;value[table],rows];};
snapshot:tp(`.u.sub;`quote`fairValue);
{set[x;snapshot x]} each key snapshot;
latestQuotes:{[] select last ts,last bid,last ask,last bidSize,last askSize by market from quote};
latestEdges:{[]
  q:update mid:(bid+ask)%2,spread:ask-bid from latestQuotes[];
  f:select last ts,last fair,last confidence,last newsScore,last imbalance by market from fairValue;
  update edge:fair-mid from q lj `market xkey f
 };
candidateTrades:{[minEdge;maxSpread]
  select from latestEdges[] where abs edge>minEdge,spread<maxSpread
 };
show "EventEdge RDB subscribed";
