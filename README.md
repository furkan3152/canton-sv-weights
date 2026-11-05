# canton-sv-weights

The history of Super Validator reward weight on Canton MainNet, rebuilt from the
public git history of [canton-foundation/configs](https://github.com/canton-foundation/configs),
and what it means for SV rewards and milestone-based (escrowed) weight.

The write-up is in [article.md](article.md).

## Run

Python 3.10 or later. Only the plots need matplotlib.

```
git clone https://github.com/canton-foundation/configs ../configs
python3 src/extract.py ../configs     # data/snapshots.csv, data/beneficiaries.csv
python3 src/lifecycle.py              # data/grants.csv, data/events.csv
python3 src/deadlines.py              # data/deadlines.csv
pip install matplotlib
python3 src/dilution.py               # data/dilution.csv, figures/dilution.png
python3 src/plot_weight_classes.py    # figures/weight-classes.png
python3 src/plot_escrow_status.py     # figures/escrow-status.png
```

## Data

| File | Contents |
|---|---|
| `data/snapshots.csv` | One row per config commit: total weight and weight by holder class |
| `data/beneficiaries.csv` | One row per commit, node and beneficiary |
| `data/grants.csv` | One row per milestone-based CIP grant |
| `data/events.csv` | Every change of a grant's escrowed or active weight |
| `data/cip_milestones.json` | Milestone deadlines extracted from the CIP texts |
| `data/deadlines.csv` | Escrowed weight compared with those deadlines |
| `data/dilution.csv` | CC per year for one unit of weight, and the escrowed share |
| `data/onchain/` | Live DSO state used to check node totals and read the issuance curve |

See "Method and limits" in the article before relying on any number.
