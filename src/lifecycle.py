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
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EPS = 1e-9


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

        earned = reduced = 0.0
        prev_e = prev_a = 0.0
        for c, e, a in series:
            de, da = e - prev_e, a - prev_a
            if abs(de) > EPS or abs(da) > EPS:
                kind = "grant"
                if de < -EPS and da > EPS:
                    kind = "milestone"  # escrow released to an active party
                    earned += min(-de, da)
                elif de < -EPS and (e + a) < (prev_e + prev_a) - EPS:
                    kind = "reduction"
                    reduced += (prev_e + prev_a) - (e + a)
                elif de > EPS or da > EPS:
                    kind = "grant" if prev_e + prev_a < EPS else "increase"
                elif da < -EPS:
                    kind = "active-reduction"
                    reduced += -da
                events.append({
                    "cip": f"CIP-{cip}", "date": info[c]["date"][:10], "commit": c,
                    "kind": kind, "escrow_before": round(prev_e, 4),
                    "escrow_after": round(e, 4), "active_before": round(prev_a, 4),
                    "active_after": round(a, 4), "subject": info[c]["subject"],
                })
            prev_e, prev_a = e, a

        grants.append({
            "cip": f"CIP-{cip}",
            "organisation": "; ".join(sorted(n for n in names[cip] if n)),
            "first_seen": info[first]["date"][:10],
            "peak_total": round(peak_total, 4),
            "peak_escrow": round(peak_escrow, 4),
            "escrow_now": round(e_now, 4),
            "active_now": round(a_now, 4),
            "earned_by_milestones": round(earned, 4),
            "reduced": round(reduced, 4),
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
