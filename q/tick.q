/ Minimal EventEdge tickerplant. Start with: q q/tick.q -p 5010
tables:`quote`fairValue;
quote:([] ts:`timestamp$(); venue:`symbol$(); market:`symbol$(); bid:`float$(); ask:`float$(); bidSize:`float$(); askSize:`float$());
fairValue:([] ts:`timestamp$(); market:`symbol$(); fair:`float$(); confidence:`float$(); newsScore:`float$(); imbalance:`float$());
.u.subscribers:();
.u.seq:0j;
.u.sub:{[requested]
  if[not all requested in tables;'"unknown table"];
  .u.subscribers,:enlist (.z.w;requested);
  :tables!value each tables
 };
.u.pub:{[table;rows]
  if[not table in tables;'"unknown table"];
  .u.seq+:1;
  set[table;value[table],rows];
  {[table;rows;subscriber]
      if[table in last subscriber; first[subscriber] (`upd;table;rows)]
    }[table;rows] each .u.subscribers;
  :.u.seq
 };
.z.pc:{[handle] .u.subscribers:.[.u.subscribers;where handle<>first each .u.subscribers;]};
show "EventEdge tickerplant listening";
