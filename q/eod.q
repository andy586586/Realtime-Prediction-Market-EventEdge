/ Persist RDB tables into a date-partitioned historical store.
.eod.flush:{[root;day]
  dayPath:hsym `$string[root],"/",string day;
  {[dayPath;table]
      data:value table;
      if[count data; .Q.dpft[dayPath;();`market;table;data]]
    }[dayPath] each `quote`fairValue;
  :`quote`fairValue
 };
