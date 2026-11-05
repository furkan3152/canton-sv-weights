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
    ("Every dated deadline has passed (due for CIP-0111 review)", "#C0504D"),
    ("Some dated deadlines have passed", "#E8A06A"),
    ("Milestones not published", "#9E9E9E"),
    ("Deadlines still ahead", "#7FA6C9"),
]


SHORT = {"London Stock Exchange Group": "LSEG", "a16z crypto": "a16z",
         "Societe Generale": "SocGen", "Further Asset Management": "Further",
         "Bosphorus SV": "BSV", "YZi Labs": "YZi Labs", "Zodia Custody": "Zodia",
         "Tharimmune": "Tharimmune"}


def group(r):
    if r["all_dated_deadlines_passed"] == "True":
        return GROUPS[0][0]
    if r["review_due"] == "True":
        return GROUPS[1][0]
    if r["timeline_confidential"] == "True":
        return GROUPS[2][0]
    return GROUPS[3][0]


def main():
    rows = [r for r in csv.DictReader(open(ROOT / "data" / "deadlines.csv"))
            if float(r["escrow_now"]) > 0]
    by = {name: [] for name, _ in GROUPS}
    for r in rows:
        by[group(r)].append(r)

    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=150)
    for i, (name, color) in enumerate(GROUPS):
        left = 0.0
        for r in sorted(by[name], key=lambda r: -float(r["escrow_now"])):
            w = float(r["escrow_now"])
            ax.barh(i, w, left=left, color=color, edgecolor="white", linewidth=1)
            if w >= 6:
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
    fig.text(0.01, 0.01, "YZi Labs' programme term has passed and its initiatives are "
             "optional and unpublished; it is shown once, in the first row. Deadlines "
             "from the CIP texts at canton-foundation/cips 92df641.",
             fontsize=6.5, color="#666")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    out = ROOT / "figures" / "escrow-status.png"
    fig.savefig(out)
    print(out, {k: round(sum(float(r["escrow_now"]) for r in v), 3) for k, v in by.items()})


if __name__ == "__main__":
    main()
