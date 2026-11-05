# canton-sv-weights

An open, reproducible account of Super Validator reward weight on Canton
MainNet, with a focus on milestone-based (escrowed) weight: how much there is,
what it has accrued, what has been paid out, and what is due for review.

The write-up is [article.md](article.md). In short:

- 180.22 of 404.45 SV reward weight (44.6%) is escrowed or unassigned
  (config commit of 1 November 2026).
- It has accrued about 1.74 billion CC since June 2025, summed round by round.
- The method reproduces the milestone payouts approved on-chain: 521 million
  CC approved against 540 million computed, over 19 grants.

Every figure is rebuilt from public sources by the scripts below. The tests
check the results against on-chain state: node weights in `DsoRules`, the
issuance paid per SV coupon at 241 sampled rounds, and the payout votes.

## Run

Python 3.10 or later. Only the plots need matplotlib.

```
git clone https://github.com/canton-foundation/configs ../configs
pip install matplotlib
./run.sh ../configs
```

`run.sh` rebuilds every table and figure and then runs the consistency tests
in `tests/`. `src/fetch_lighthouse.sh` refreshes the on-chain snapshots in
`data/lighthouse/`, including the round samples (`src/fetch_rounds.py`).

| Step | Script | Output |
|---|---|---|
| Weight history | `src/extract.py` | `data/snapshots.csv`, `data/beneficiaries.csv` |
| Grant life cycle | `src/lifecycle.py` | `data/grants.csv`, `data/events.csv` |
| Deadlines | `src/deadlines.py` | `data/deadlines.csv` |
| Rewards | `src/dilution.py` | `data/dilution.csv`, `figures/dilution.png` |
| Milestone mints | `src/mints.py` | `data/mint_votes.csv`, `data/mints.csv` |
| Config against chain | `src/onchain_check.py` | `data/weight_votes.csv` |
| Figures | `src/plot_*.py` | `figures/*.png` |

## Data

| File | Contents |
|---|---|
| `data/snapshots.csv` | One row per config commit: total weight and weight by holder class |
| `data/beneficiaries.csv` | One row per commit, node and beneficiary |
| `data/grants.csv` | One row per milestone-based CIP grant |
| `data/events.csv` | Every change of a grant's escrowed or active weight |
| `data/cip_milestones.json` | Milestone deadlines extracted from the CIP texts |
| `data/milestone_weights.json` | Maximum weight of each dated milestone, read by hand from the CIP texts |
| `data/deadlines.csv` | Escrowed weight compared with those deadlines |
| `data/dilution.csv` | CC per year for one unit of weight, and the escrowed share |
| `data/mint_votes.csv` | Every on-chain vote to mint from the unclaimed pool |
| `data/mints.csv` | Approved milestone mints per grant, against the model |
| `data/weight_votes.csv` | Every executed weight vote, matched with the config commit |
| `data/onchain/` | Live DSO state used to check node totals and read the issuance curve |
| `data/lighthouse/` | Vote requests and rounds as indexed by Lighthouse, with the fetch time; `round_samples.csv` holds every 500th round's opening time and paid SV issuance |

See "Method and limits" in the article before relying on any number.

## Sources

| Source | Used for | Terms |
|---|---|---|
| [canton-foundation/configs](https://github.com/canton-foundation/configs) | SV weights and beneficiaries, every commit | No licence file; the repository is public |
| [canton-foundation/cips](https://github.com/canton-foundation/cips) | Milestones, deadlines and quotes | CC0-1.0 (per CIP) |
| [canton-network/splice](https://github.com/canton-network/splice) | Reward formulas and contract behaviour (quoted, not copied) | Apache-2.0 |
| SV app public API (`/dso`) | Live `DsoRules` and `AmuletRules` in `data/onchain/` | Public endpoint |
| [Lighthouse](https://lighthouse.cantonloop.com) | Vote requests and round data in `data/lighthouse/` | Third-party indexer; snapshots kept for reproducibility |

## Licence

The code is released under the MIT licence (`LICENSE`). The article and the
figures are released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Data taken from the sources above remains subject to their terms.
