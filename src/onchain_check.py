"""Check the config file's node totals against on-chain weight votes.

Every change of an SV node's total reward weight is an on-chain
SRARC_UpdateSvRewardWeight vote. This script takes each executed vote, as
indexed by Lighthouse, and finds the config commit whose node total equals the
new weight and is closest in time to the vote's effective time.

Votes whose effective time is 2025-07-06 08:16 are excluded: they are the batch
of earlier changes that Lighthouse recorded when it started indexing, not
changes made on that day.

Writes data/weight_votes.csv.
"""

import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_START = "2025-07-06T08:16"


def when(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def main():
    votes = json.load(open(ROOT / "data" / "lighthouse" / "governance.json"))["vote_requests"]
    votes = sorted(
        (v for v in votes if v["action_kind"] == "SRARC_UpdateSvRewardWeight"
         and v["status"] == "executed" and not v["target_effective_at"].startswith(INDEX_START)),
        key=lambda v: v["target_effective_at"],
    )

    totals = defaultdict(lambda: defaultdict(float))
    dates = {}
    for r in csv.DictReader(open(ROOT / "data" / "beneficiaries.csv")):
        totals[r["commit"]][r["node"]] += float(r["weight"])
        dates[r["commit"]] = when(r["date"])

    out = []
    for v in votes:
        node = v["action_target"].split("::")[0]
        weight = int(v["action_details"][0].split(":")[1].replace(",", "")) / 10_000
        effective = when(v["target_effective_at"])
        matches = [c for c in dates if abs(totals[c].get(node, -1.0) - weight) < 1e-6]
        best = min(matches, key=lambda c: abs(dates[c] - effective), default=None)
        out.append({
            "effective": v["target_effective_at"], "node": node, "new_weight": weight,
            "config_commit": best or "",
            "config_date": dates[best].isoformat() if best else "",
            "lag_days": round((dates[best] - effective).total_seconds() / 86400, 2) if best else "",
            "reason": (v["reason_body"] or "").replace("\n", " ")[:200],
        })

    with open(ROOT / "data" / "weight_votes.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    return out


def cip0111_votes():
    """Every vote whose stated reason cites CIP-0111."""
    votes = json.load(open(ROOT / "data" / "lighthouse" / "governance.json"))["vote_requests"]
    return [(v["created_at"][:10], v["status"], v["action_kind"], (v.get("reason_body") or "")[:120])
            for v in votes if "CIP-0111" in (v.get("reason_body") or "")]


if __name__ == "__main__":
    for v in cip0111_votes():
        print("cites CIP-0111:", *v)
    out = main()
    lags = sorted(r["lag_days"] for r in out if r["lag_days"] != "")
    print(f"{len(out)} executed weight votes; {len(lags)} matched a config commit, "
          f"median lag {lags[len(lags) // 2]} days, range {lags[0]} to {lags[-1]}")
    for r in out:
        if r["lag_days"] == "":
            print("  no config commit with", r["node"], r["new_weight"], "effective", r["effective"][:10])
