"""Sample closed mining rounds from Lighthouse.

For every STEP-th round, record when it opened and the CC it paid per SV
reward coupon weight unit (issuancePerSvRewardCoupon). Between samples the
script interpolates linearly, so the sample spacing only needs to be small
against the intervals between weight changes.

Writes data/lighthouse/round_samples.csv. Run it only to refresh the data.
"""

import csv
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://lighthouse.cantonloop.com/api/web/rounds/"
STEP = 500


def get(n, tries=5):
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(BASE + str(n), timeout=60) as r:
                return json.load(r)
        except OSError:
            if attempt == tries - 1:
                raise
            time.sleep(2 ** attempt)


def main(last):
    out = []
    for n in list(range(STEP, last, STEP)) + [last]:
        r = get(n)
        out.append({"round": r["round"], "open_at": r["open_at"],
                    "issuance_per_sv_reward_coupon": r["issuance_per_sv_reward_coupon"]})
        time.sleep(0.5)
    with open(ROOT / "data" / "lighthouse" / "round_samples.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(len(out), "samples", out[0], out[-1])


def latest_closed_round():
    rounds = json.load(open(ROOT / "data" / "lighthouse" / "rounds.json"))["rounds"]
    return max(r["round"] for r in rounds if r["status"] == "closed")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else latest_closed_round())
