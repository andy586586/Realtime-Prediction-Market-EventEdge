#!/usr/bin/env bash
set -euo pipefail

docker compose up -d questdb

for attempt in $(seq 1 30); do
  if curl --silent --fail "http://localhost:9000/exec?query=select%201" >/dev/null; then
    break
  fi
  if [[ "$attempt" == "30" ]]; then
    echo "QuestDB did not become ready on http://localhost:9000" >&2
    exit 1
  fi
  sleep 1
done

python3 -m python.eventedge.questdb_replay --reset

curl --silent --get "http://localhost:9000/exec" \
  --data-urlencode "query=select ts,venue,market,bid,ask from quotes latest on ts partition by market" \
  | python3 -m json.tool

echo "QuestDB console: http://localhost:9000"
