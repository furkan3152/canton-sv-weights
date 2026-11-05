"""Stage 1b: compare escrowed weight with the milestone deadlines in the CIPs.

Inputs:
  data/grants.csv          from lifecycle.py (escrowed and active weight now)
  data/cip_milestones.json milestone deadlines extracted from the CIP texts

For every grant that still has escrowed weight at the last config snapshot,
count the milestones whose absolute due date has passed. A passed deadline
does not mean the weight is forfeit: CIP-0111 requires a TWG review and an SV
vote before any reduction. It only marks grants that are due for that review.

Writes data/deadlines.csv.
"""

import csv
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main(as_of=date(2026, 11, 1)):
    grants = {g["cip"]: g for g in csv.DictReader(open(ROOT / "data" / "grants.csv"))}
    cips = {c["cip"]: c for c in json.load(open(ROOT / "data" / "cip_milestones.json"))["cips"]}

    out = []
    for cip, g in grants.items():
        c = cips.get(cip)
        if c is None:
            continue
        dated = [m for m in c["milestones"] if m.get("absolute_due_date")]
        passed = [m for m in dated if date.fromisoformat(m["absolute_due_date"]) < as_of]
        out.append({
            "cip": cip,
            "organisation": c["organisation"],
            "approved": c["approved"],
            "escrow_now": float(g["escrow_now"]),
            "active_now": float(g["active_now"]),
            "status": g["status"],
            "milestones": len(c["milestones"]),
            "dated_milestones": len(dated),
            "passed_deadlines": len(passed),
            "last_due_date": max((m["absolute_due_date"] for m in dated), default=""),
            "timeline_confidential": bool(c.get("milestones_confidential")),
            "review_due": bool(passed) and float(g["escrow_now"]) > 0,
            "all_dated_deadlines_passed": bool(dated) and len(passed) == len(dated)
                and float(g["escrow_now"]) > 0,
        })

    out.sort(key=lambda r: (not r["review_due"], r["last_due_date"]))
    with open(ROOT / "data" / "deadlines.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    return out


if __name__ == "__main__":
    rows = main()
    due = [r for r in rows if r["review_due"]]
    print(f"{len(due)} grants with escrow past at least one dated deadline, "
          f"{sum(r['escrow_now'] for r in due):.3f} weight")
    for r in rows:
        print(f"{r['cip']} {r['organisation'][:22]:22} esc={r['escrow_now']:>6} "
              f"passed={r['passed_deadlines']}/{r['dated_milestones']} of {r['milestones']} "
              f"last_due={r['last_due_date'] or '-':10} conf={r['timeline_confidential']} "
              f"{'ALL-PASSED' if r['all_dated_deadlines_passed'] else ''}")
