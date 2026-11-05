"""Figure 3: escrowed SV weight at the last snapshot, by deadline status.

Reads data/deadlines.csv (written by deadlines.py) and writes
figures/escrow-status.png.
"""

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent

GROUPS = [
    ("Tied to passed, dated milestones not yet earned\n(due for CIP-0111 review)", "#C0504D"),
    ("Other escrow of those grants: undated or\nlater milestones, or earned below the maximum", "#E8A06A"),
    ("Milestones not published", "#9E9E9E"),
    ("No dated deadline has passed yet", "#7FA6C9"),
]


SHORT = {"London Stock Exchange Group": "LSEG", "a16z crypto": "a16z",
         "Societe Generale": "SocGen", "Further Asset Management": "Further",
         "Bosphorus SV": "BSV", "YZi Labs": "YZi Labs", "Zodia Custody": "Zodia",
         "Tharimmune": "Tharimmune", "USDT0 issuer": "USDT0"}


def pieces(r):
    """Split a grant's escrow into the groups of the figure."""
    escrow = float(r["escrow_now"])
    if r["review_due"] == "True":
        low = float(r["unmet_passed_low"])
        return [(0, low), (1, escrow - low)]
    if r["timeline_confidential"] == "True":
        return [(2, escrow)]
    return [(3, escrow)]


def main():
    rows = [r for r in csv.DictReader(open(ROOT / "data" / "deadlines.csv"))
            if float(r["escrow_now"]) > 0]
    by = [[] for _ in GROUPS]
    for r in rows:
        for i, w in pieces(r):
            if w > 1e-9:
                by[i].append((r, w))
    by = {GROUPS[i][0]: v for i, v in enumerate(by)}

    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=150)
    for i, (name, color) in enumerate(GROUPS):
        left = 0.0
        for r, w in sorted(by[name], key=lambda p: -p[1]):
            ax.barh(i, w, left=left, color=color, edgecolor="white", linewidth=1)
            if w >= 5.9:
                label = r["organisation"].split(" (")[0].split(",")[0].split(" issuer")[0]
                label = SHORT.get(label, label.split()[0])
                ax.text(left + w / 2, i, label, ha="center", va="center",
                        fontsize=7, color="white")
            left += w
        ax.text(left + 1, i, f"{left:.1f} weight, {len(by[name])} grants",
                va="center", fontsize=8)
    ax.set_yticks(range(len(GROUPS)), [name for name, _ in GROUPS], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Escrowed SV reward weight on 2026-11-01")
    ax.set_title("Where the escrowed Super Validator weight stands", loc="left")
    ax.set_xlim(0, 100)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.01, "First row: the low bound, assuming weight earned so far came from the "
             "dated milestones first. Deadlines and milestone weights from the CIP texts at "
             "canton-foundation/cips 92df641.",
             fontsize=6.5, color="#666")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    out = ROOT / "figures" / "escrow-status.png"
    fig.savefig(out)
    print(out, {k.split(chr(10))[0]: round(sum(w for _, w in v), 3) for k, v in by.items()})


if __name__ == "__main__":
    main()
