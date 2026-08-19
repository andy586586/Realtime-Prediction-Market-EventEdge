-- Latest quote per market.
SELECT ts, venue, market, bid, ask, bid_size, ask_size
FROM quotes
LATEST ON ts PARTITION BY market;

-- Latest fair value available at each quote, with the same edge definition as q.
SELECT
    q.ts,
    q.venue,
    q.market,
    q.bid,
    q.ask,
    (q.bid + q.ask) / 2 AS mid,
    q.ask - q.bid AS spread,
    f.fair,
    f.confidence,
    f.news_score,
    f.imbalance,
    f.fair - ((q.bid + q.ask) / 2) AS edge
FROM quotes q
ASOF JOIN fair_values f ON q.market = f.market;

-- Candidate events. Change the constants to tune the screen.
SELECT *
FROM (
    SELECT
        q.ts,
        q.venue,
        q.market,
        q.bid,
        q.ask,
        (q.bid + q.ask) / 2 AS mid,
        q.ask - q.bid AS spread,
        f.fair,
        f.confidence,
        f.fair - ((q.bid + q.ask) / 2) AS edge
    FROM quotes q
    ASOF JOIN fair_values f ON q.market = f.market
)
WHERE abs(edge) > 0.025 AND spread < 0.06;

-- One-minute probability bars.
SELECT
    market,
    first((bid + ask) / 2) AS open,
    max((bid + ask) / 2) AS high,
    min((bid + ask) / 2) AS low,
    last((bid + ask) / 2) AS close,
    avg(ask - bid) AS avg_spread
FROM quotes
SAMPLE BY 1m ALIGN TO CALENDAR;
