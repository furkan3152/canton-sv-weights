#!/bin/sh
# Refresh the Lighthouse snapshots used by mints.py and the tests.
# Lighthouse (lighthouse.cantonloop.com) indexes on-chain Canton MainNet state.
set -e
cd "$(dirname "$0")/../data/lighthouse"
B=https://lighthouse.cantonloop.com/api/web
for e in governance svs rounds dev-fund; do
  curl -sSf -m 120 "$B/$e" -o "$e.json"
done
date -u +%Y-%m-%dT%H:%MZ > fetched-at.txt
