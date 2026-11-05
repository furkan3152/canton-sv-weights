#!/bin/sh
# Refresh the Lighthouse snapshots used by mints.py, dilution.py and the tests.
# Lighthouse (lighthouse.cantonloop.com) indexes on-chain Canton MainNet state.
set -e
SRC=$(cd "$(dirname "$0")" && pwd)
cd "$SRC/../data/lighthouse"
B=https://lighthouse.cantonloop.com/api/web
for e in governance rounds; do
  curl -sSf -m 120 "$B/$e" -o "$e.json"
done
date -u +%Y-%m-%dT%H:%MZ > fetched-at.txt
python3 "$SRC/fetch_rounds.py"
