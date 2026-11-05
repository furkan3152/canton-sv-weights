"""Stage 3: compare milestone mints with the escrowed rewards the model predicts.

When a milestone is met, SV governance votes to let the organisation mint the
CC its weight earned while it was escrowed (CIP-0066 flow): a
DsoRules_CreateUnallocatedUnclaimedActivityRecord vote with a beneficiary and
an amount, paid from the UnclaimedReward pool.

Inputs:
  data/lighthouse/governance.json  every on-chain VoteRequest, as indexed by
                                   Lighthouse (lighthouse.cantonloop.com)
  data/events.csv                  milestone events from lifecycle.py
  data/dilution.csv                CC per year for one unit of weight

For each grant, the model value is the weight earned at each milestone times
the CC one unit of weight earned between the grant's first escrow and that
milestone. It assumes the SV node collected every round.

Writes data/mint_votes.csv (every such vote) and data/mints.csv (per grant).
"""

import csv
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Grants whose mints do not follow the escrow-release pattern, so the model
# does not apply: CIP-0102/CIP-0114 weight is earned under the CIP-0114
# programme, and the CIP-0115 mints were made without releasing escrow.
NOT_COMPARABLE = {"CIP-0102", "CIP-0114", "CIP-0115"}
YEAR_SECONDS = 365 * 24 * 3600
CIP_RE = re.compile(r"CIPs?[- ]?0*(\d{2,3})", re.I)


def when(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def per_unit_series():
    rows = list(csv.DictReader(open(ROOT / "data" / "dilution.csv")))
    return [(when(r["date"]), float(r["cc_per_weight_unit_per_year"])) for r in rows]


def cc_per_unit_between(series, start, stop):
    total = 0.0
    for i, (t, rate) in enumerate(series):
        t_next = series[i + 1][0] if i + 1 < len(series) else stop
        lo, hi = max(t, start), min(t_next, stop)
        if hi > lo:
            total += rate * (hi - lo).total_seconds() / YEAR_SECONDS
    return total


def votes():
    data = json.load(open(ROOT / "data" / "lighthouse" / "governance.json"))
    out = []
    for v in data["vote_requests"]:
        if v["action_kind"] != "SRARC_CreateUnallocatedUnclaimedActivityRecord":
            continue
        details = " | ".join(v["action_details"] or [])
        amount = float(re.search(r"Amount:\s*([\d,.]+)", details).group(1).replace(",", ""))
        reason = (v["reason_body"] or "").replace("\n", " ")
        cips = CIP_RE.findall(reason)
        lowered = reason.lower()
        if amount <= 10:
            kind = "test mint"
        elif "external party id" in lowered or "wrong partyid" in lowered:
            kind = "party correction"
        elif cips and cips[0] == "67":
            kind = "one-time allocation (CIP-0067)"
        else:
            kind = "milestone"
        out.append({
            "created": v["created_at"][:10], "status": v["status"],
            "beneficiary": v["action_target"].split("::")[0], "amount_cc": amount,
            "cip": f"CIP-{int(cips[0]):04d}" if cips else "", "kind": kind,
            "reason_url": v["reason_url"] or "", "vote_id": v["id"],
        })
    out.sort(key=lambda r: r["created"])

    # A vote that repeats an executed vote's exact amount is a resubmission
    # (for example after the first record expired); count it once. Some
    # resubmissions cite no CIP, so match on the amount alone.
    seen = set()
    for r in out:
        key = round(r["amount_cc"], 2)
        r["repeat"] = r["status"] == "executed" and key in seen
        if r["status"] == "executed":
            seen.add(key)
    return out


def main():
    rows = votes()
    with open(ROOT / "data" / "mint_votes.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    minted = defaultdict(float)
    for r in rows:
        if r["status"] == "executed" and r["kind"] == "milestone" and not r["repeat"]:
            minted[r["cip"]] += r["amount_cc"]

    series = per_unit_series()
    events = list(csv.DictReader(open(ROOT / "data" / "events.csv")))
    start = {}
    modeled = defaultdict(float)
    earned = defaultdict(float)
    for e in events:
        t = when(e["date"] + "T00:00:00+00:00")
        if e["kind"] == "grant":
            start[e["cip"]] = t
        if e["kind"] != "milestone":
            continue
        de = float(e["escrow_before"]) - float(e["escrow_after"])
        da = float(e["active_after"]) - float(e["active_before"])
        w = min(de, da)
        earned[e["cip"]] += w
        modeled[e["cip"]] += w * cc_per_unit_between(series, start[e["cip"]], t)

    out = []
    for cip in sorted(set(minted) | set(modeled)):
        m, p = minted.get(cip, 0.0), modeled.get(cip, 0.0)
        out.append({
            "cip": cip, "earned_weight": round(earned.get(cip, 0.0), 4),
            "approved_mint_cc": round(m), "modeled_escrow_cc": round(p),
            "ratio": round(m / p, 3) if p and cip not in NOT_COMPARABLE else "",
            "comparable": cip not in NOT_COMPARABLE and bool(m) and bool(p),
        })
    with open(ROOT / "data" / "mints.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    return rows, out


if __name__ == "__main__":
    rows, out = main()
    for r in out:
        print(f"{r['cip']} earned={r['earned_weight']:>7} mint={r['approved_mint_cc']:>14,} "
              f"model={r['modeled_escrow_cc']:>14,} ratio={r['ratio']}")
    both = [r for r in out if r["comparable"]]
    m = sum(r["approved_mint_cc"] for r in both)
    p = sum(r["modeled_escrow_cc"] for r in both)
    print(f"grants with both: {len(both)}, mint {m:,.0f}, model {p:,.0f}, ratio {m / p:.3f}")
