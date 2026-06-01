/ load_csv.q
/ q q/load_csv.q
/ Loads EventEdge CSV files into q tables.

\l q/analytics.q

show "loaded EventEdge q analytics";
show count orderbooks;
show count fairValues;
show count settlements;
show latestMispricing[];
