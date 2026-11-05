"""Figure 4: approved milestone mints against the model's escrowed rewards.

Reads data/mints.csv (written by mints.py) and writes figures/mints.png.
"""

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
NAMES = {"CIP-0060": "Zero Hash", "CIP-0061": "Chainlink",
         "CIP-0063": "Kaiko", "CIP-0065": "Chainlink, LayerZero, Wormhole",
         "CIP-0074": "BitGo", "CIP-0091": "Zenith",
         "CIP-0094": "Blockdaemon", "CIP-0106": "QCP", "CIP-0118": "Franklin Templeton"}


def main():
    rows = [r for r in csv.DictReader(open(ROOT / "data" / "mints.csv")) if r["comparable"] == "True"]
    x = [float(r["modeled_escrow_cc"]) / 1e6 for r in rows]
    y = [float(r["approved_mint_cc"]) / 1e6 for r in rows]
    m, p = sum(y), sum(x)

    fig, ax = plt.subplots(figsize=(7, 6), dpi=150)
    lim = (0.8, 130)
    ax.plot(lim, lim, color="#999", linewidth=1, linestyle="--")
    ax.text(70, 85, "approved = model", fontsize=8, color="#666", rotation=45,
            ha="center", va="center")
    ax.scatter(x, y, s=42, color="#4C6A92", edgecolor="white", linewidth=1.5, zorder=3)
    for r, xi, yi in zip(rows, x, y):
        if r["cip"] in NAMES:
            ax.annotate(f"{NAMES[r['cip']]} ({r['ratio']})", (xi, yi), xytext=(6, -3),
                        textcoords="offset points", fontsize=7, color="#333")
    ax.set_xscale("log")
    ax.set_yscale("log")
    from matplotlib.ticker import FuncFormatter
    fmt = FuncFormatter(lambda v, _: f"{v:g}")
    for axis in (ax.xaxis, ax.yaxis):
        axis.set_major_formatter(fmt)
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("Model: CC the earned weight accrued in escrow (million)")
    ax.set_ylabel("Approved by on-chain mint votes (million CC)")
    ax.set_title(f"Milestone mints of {len(rows)} grants against the model", loc="left")
    ax.grid(alpha=0.3, which="major")
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.01, f"Total approved {m:,.0f}M CC, model {p:,.0f}M CC (ratio {m / p:.2f}). "
             "Votes indexed by Lighthouse; repeated votes counted once.", fontsize=7, color="#666")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(ROOT / "figures" / "mints.png")


if __name__ == "__main__":
    main()
