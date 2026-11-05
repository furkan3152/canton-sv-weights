# canton-sv-weights

The history of Super Validator reward weight on Canton MainNet, rebuilt from the
public git history of [canton-foundation/configs](https://github.com/canton-foundation/configs),
and what it means for SV rewards and milestone-based (escrowed) weight.

The write-up is in [article.md](article.md).

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
