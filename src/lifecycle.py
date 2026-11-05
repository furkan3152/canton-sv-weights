"""Stage 1: the life cycle of every milestone-based SV weight grant.

A milestone grant is a CIP that gives an organisation SV weight in escrow. The
escrowed part sits on a ghost party; when a milestone is met, governance moves
weight to an active party of that organisation; when a milestone is missed,
the weight is reduced (CIP-0105, CIP-0111).

This script groups beneficiary rows by CIP and follows each grant through the
snapshots in data/beneficiaries.csv. It writes:

  data/grants.csv   one row per CIP that ever had escrowed weight
  data/events.csv   one row per change of a grant's escrowed or active weight

A beneficiary row whose comment cites several CIPs is counted under the first
one that has escrowed weight, so that the weight is not counted twice.
"""

import csv
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EPS = 1e-9


FLOWS = ("escrow_granted", "earned_from_escrow", "earned_direct",
         "released_unearned", "removed", "enforced", "restored")
ENFORCEMENT = re.compile(r"CIP-?0105", re.I)
ALIGNMENT = re.compile(r"align public extraBeneficiaries", re.I)


def classify(de, da, before, subject):
    """Name one change of a grant's escrowed (de) and active (da) weight."""
    if ALIGNMENT.search(subject):
        return "alignment"
    if ENFORCEMENT.search(subject) and abs(de) < EPS:
        return "enforcement"  # CIP-0105 lock enforcement or its reversal
    if de < -EPS and da > EPS:
        return "milestone"  # escrow released to an active party
    if de < -EPS:
        return "removal"
    if de > EPS:
        return "grant" if before < EPS else "increase"
    if da > EPS:
        return "earned-direct"  # earned weight added without an escrow release
    return "active-reduction"


def load():
    rows = list(csv.DictReader(open(ROOT / "data" / "beneficiaries.csv")))
    snaps = list(csv.DictReader(open(ROOT / "data" / "snapshots.csv")))
    return rows, snaps


def main():
    rows, snaps = load()
    order = [s["commit"] for s in snaps]
    info = {s["commit"]: s for s in snaps}

    escrow_cips = {
        r["cips"].split(";")[0]
        for r in rows
        if r["class"] == "escrow" and r["cips"]
    }

    # weight[cip][commit] = {"escrow": x, "active": y}
    weight = defaultdict(lambda: defaultdict(lambda: {"escrow": 0.0, "active": 0.0}))
    names = defaultdict(set)
    for r in rows:
        if not r["cips"] or r["class"] not in ("escrow", "active"):
            continue
        cips = r["cips"].split(";")
        cip = next((c for c in cips if c in escrow_cips), None)
        if cip is None:
            continue
        weight[cip][r["commit"]][r["class"]] += float(r["weight"])
        names[cip].add(r["comment"].split(" CIP")[0].split(" #")[0].strip())

    grants, events = [], []
    for cip in sorted(weight):
        series = [(c, weight[cip][c]["escrow"], weight[cip][c]["active"]) for c in order]
        present = [(c, e, a) for c, e, a in series if e + a > EPS]
        if not present:
            continue
        first, last = present[0][0], order[-1]
        peak_total = max(e + a for _, e, a in series)
        peak_escrow = max(e for _, e, _ in series)
        _, e_now, a_now = series[-1]

        flows = dict.fromkeys(FLOWS, 0.0)
        prev_e = prev_a = 0.0
        for c, e, a in series:
            de, da = e - prev_e, a - prev_a
            if abs(de) > EPS or abs(da) > EPS:
                kind = classify(de, da, prev_e + prev_a, info[c]["subject"])
                if kind == "grant" or kind == "increase":
                    flows["escrow_granted"] += max(de, 0.0)
                    flows["earned_direct"] += max(da, 0.0)
                elif kind == "milestone":
                    flows["earned_from_escrow"] += min(-de, da)
                    flows["released_unearned"] += max(-de - da, 0.0)
                    flows["earned_direct"] += max(da + de, 0.0)
                elif kind == "removal":
                    flows["removed"] += -de
                    flows["enforced"] += max(-da, 0.0)
                elif kind == "earned-direct":
                    flows["earned_direct"] += da
                elif kind in ("enforcement", "alignment"):
                    flows["enforced"] += max(-da, 0.0)
                    flows["restored"] += max(da, 0.0)
                    flows["escrow_granted"] += max(de, 0.0)
                    flows["removed"] += max(-de, 0.0)
                events.append({
                    "cip": f"CIP-{cip}", "date": info[c]["date"][:10], "commit": c,
                    "kind": kind, "escrow_before": round(prev_e, 4),
                    "escrow_after": round(e, 4), "active_before": round(prev_a, 4),
                    "active_after": round(a, 4), "subject": info[c]["subject"],
                })
            prev_e, prev_a = e, a

        # Every unit of escrow either is still escrowed, was earned, was
        # released without being earned, or was removed.
        balance = flows["escrow_granted"] - e_now - flows["earned_from_escrow"] \
            - flows["released_unearned"] - flows["removed"]
        assert abs(balance) < 1e-6, (cip, flows, e_now)
        active = flows["earned_from_escrow"] + flows["earned_direct"] \
            - flows["enforced"] + flows["restored"]
        assert abs(active - a_now) < 1e-6, (cip, flows, a_now)

        grants.append({
            "cip": f"CIP-{cip}",
            "organisation": "; ".join(sorted(n for n in names[cip] if n)),
            "first_seen": info[first]["date"][:10],
            "peak_total": round(peak_total, 4),
            "peak_escrow": round(peak_escrow, 4),
            "escrow_now": round(e_now, 4),
            "active_now": round(a_now, 4),
            **{k: round(v, 4) for k, v in flows.items()},
            "status": (
                "fully escrowed" if a_now < EPS and e_now > EPS
                else "partly earned" if a_now > EPS and e_now > EPS
                else "fully earned" if a_now > EPS
                else "removed"
            ),
        })

    for name, data in (("grants", grants), ("events", events)):
        with open(ROOT / "data" / f"{name}.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0]))
            w.writeheader()
            w.writerows(data)
    print(f"{len(grants)} grants, {len(events)} events")


if __name__ == "__main__":
    main()
