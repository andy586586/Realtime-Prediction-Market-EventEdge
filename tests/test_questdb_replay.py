import unittest

from python.eventedge.questdb_replay import fair_value_line, quote_line, timestamp_ns


class QuestDbReplayTest(unittest.TestCase):
    def test_timestamp_is_utc_nanoseconds(self) -> None:
        self.assertEqual(timestamp_ns("1970-01-01T00:00:01Z"), 1_000_000_000)
        self.assertEqual(timestamp_ns("1970-01-01T01:00:01+01:00"), 1_000_000_000)

    def test_quote_line_escapes_tags(self) -> None:
        line = quote_line({
            "ts": "1970-01-01T00:00:01Z",
            "venue": "demo venue",
            "market": "A=B,C",
            "bid": "0.4",
            "ask": "0.42",
            "bid_size": "10",
            "ask_size": "12",
        })
        self.assertEqual(
            line,
            "quotes,venue=demo\\ venue,market=A\\=B\\,C "
            "bid=0.4,ask=0.42,bid_size=10.0,ask_size=12.0 1000000000",
        )

    def test_fair_value_line(self) -> None:
        line = fair_value_line({
            "ts": "1970-01-01T00:00:01+00:00",
            "market": "MKT",
            "fair": "0.5",
            "confidence": "0.8",
            "news_score": "1.2",
            "imbalance": "-0.1",
        })
        self.assertIn("fair_values,market=MKT", line)
        self.assertTrue(line.endswith("1000000000"))


if __name__ == "__main__":
    unittest.main()
