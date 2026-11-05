# The Ghost Weight: how much Canton Super Validator reward weight is waiting on a promise

*Draft, November 2026. Data, code and every number in this article are reproducible from the public repository linked at the end.*

## Summary

- Total Super Validator (SV) reward weight on Canton MainNet grew from **130 to 404.45** between January 2025 and November 2026.
- **180.22 of that weight (44.6%)** does not belong to an operating SV. It sits on escrow ("ghost") parties for organisations that must first meet milestones, or in a pool not yet assigned to anyone.
- Escrowed weight takes its share of every round's SV rewards like any other weight, but it is not minted. At today's issuance curve that share is about **847 million CC a year** (about $88 million at a CC price of $0.104), which flows to the unminted pool.
- Of about **262 weight** ever promised through 38 milestone-based CIPs, about **65 has been earned**, **19 has been removed** and **177 is still in escrow**.
- **69 escrowed weight across 16 grants** is past every deadline that can be dated from the CIP text, which is the point at which CIP-0111 requires a review. A further **67 weight across 7 grants** has milestones that were not published.
- A unit of SV weight earned about **70 million CC a year in January 2025** and about **4.7 million CC a year today**.

None of this is hidden. The escrow model is written into the CIPs, and every weight change is a public commit. What has been missing is the whole picture over time. This article puts it together and suggests three ways to make it easier to follow.

## 1. What SV weight is

Each round, a fixed share of new Canton Coin goes to Super Validators. The share is set by the issuance curve: today it is 20% of the 10 billion CC a year ceiling, after 5% goes to the Development Fund (CIP-0082). In the Splice source (`Issuance.daml`, `computeIssuingRoundParameters`), this SV tranche is divided by the total SV reward weight:

```
svTranche = amuletToIssuePerYear / roundsPerYear × (1 − developmentFund) × (1 − validator% − app%)
issuancePerSvRewardCoupon = svTranche / totalSvRewardWeight
```

So each unit of weight earns the same amount, and every new unit of weight reduces what the others earn.

The weight of each SV node, and how a node passes part of its weight to other parties ("beneficiaries"), is approved by SV operators and published in [`canton-foundation/configs`](https://github.com/canton-foundation/configs), file `configs/MainNet/approved-sv-id-values.yaml`. That file has 121 commits since 22 January 2025. Each commit is a snapshot of the weight table, and most commit messages cite the CIP behind the change.

## 2. The ghost weight

Since mid-2025, many CIPs have given organisations SV weight that they earn by meeting milestones: an integration, a product launch, a volume target. Until a milestone is met, the weight is held in escrow by another node. CIP-0066 describes the flow: "The GSF node hosts an SV weight on behalf of an SV in an escrow agreement", "The GSF specifically disables the final minting action for all escrowed SV parties", and "All the coin earned by escrowed parties goes into the unminted pool".

In the config file, each escrow party is named `<Organisation>-ghost-1` (or `-Escrow-1`) and is hosted on one of three ghost validators: the Global Synchronizer Foundation's `GhostSV-validator-1`, MPC Holding's `MPCH-GHOSTvalidator-1` and Five North's `5nghost-mainnet-1`.

![Figure 1](figures/weight-classes.png)

*Figure 1. SV reward weight by holder, from every commit of the config file.*

On 1 November 2026:

| Holder | Weight | Share |
|---|---|---|
| Kept by the 13 SV node operators | 83.63 | 20.7% |
| Passed to active beneficiaries | 140.61 | 34.8% |
| **Escrowed on 33 ghost parties** | **177.13** | **43.8%** |
| **Not yet assigned (GhostSV pool)** | **3.10** | **0.8%** |
| Total | 404.45 | |

The node totals in the file match the live on-chain `DsoRules` exactly (all 13 nodes, round 120,388, fetched 5 November 2026).

Escrowed weight was zero until June 2025. It passed a third of all weight in November 2025 and has stayed between 31% and 46% since. Most of the growth in total weight since mid-2025 is escrowed weight.

## 3. What a unit of weight earns

![Figure 2](figures/dilution.png)

*Figure 2. CC per year earned by one unit of SV weight. The sharp fall on 20 January 2026 is the scheduled curve step from 20B to 10B CC a year, when the SV share also fell from 48% to 20%.*

A unit of weight earned about 70 million CC a year in January 2025 and earns about 4.7 million CC a year today. The scheduled issuance curve explains most of that fall: if total weight had stayed at 130, a unit would still earn about 14.6 million CC a year. Weight growth explains the rest, from 14.6 million to 4.7 million.

The escrowed share follows from the same formula. At the current curve, the SV tranche is 1.9 billion CC a year, and 44.6% of it, about **847 million CC a year**, is assigned to escrow and unassigned weight. Since June 2025 the total is between **1.76 and 1.86 billion CC** (the range comes from the Development Fund's activation date, which is not published).

These coins are not lost. Under CIP-0066, when a milestone is met, governance can vote to mint the corresponding amount from the unminted pool to the organisation. When weight is removed under CIP-0111, the escrowed rewards "should be burned". Until either happens, the amount waits in a pool controlled by SV governance.

## 4. Promises and outcomes

Grouping every beneficiary row by the CIP in its comment gives the history of 38 milestone grants. Each change is classified as a new grant, a milestone (escrow moves to an active party), a reduction or an increase. Every event links to the commit that made it.

| | Weight |
|---|---|
| Promised (peak of each grant) | 262.45 |
| Earned through milestones | 65.28 |
| Removed | 19.45 |
| Still escrowed | 177.13 |

- 6 grants are fully earned, 15 are partly earned, 15 have earned nothing yet, and 2 were removed.
- For grants that met a milestone, the first one came after a median of **92 days**.
- The first removals under CIP-0111 were Monstera FZE (5) and Woodside AI (10), on 17 May 2026, about nine months after their weight was added.
- CIP-0105 lock enforcement has cut and restored active weight several times (Taurus, Ledger, Quantstamp, Elliptic, DFNS).

### Deadlines

The CIP texts set deadlines for most milestones, often "+180 days from CIP approval". Comparing those deadlines with the escrow on 1 November 2026:

![Figure 3](figures/escrow-status.png)

*Figure 3. Escrowed weight by deadline status.*

| Status | Grants | Escrowed weight |
|---|---|---|
| Every dated deadline has passed | 16 | 69.0 |
| Some dated deadlines have passed | 2 | 12.0 |
| Milestones not published | 7 | 67.0 |
| Deadlines still ahead | 5 | 29.1 |

A passed deadline does not mean the weight is forfeit. CIP-0111 says: "At a minimum, the TWG must review SVs for potential weight reduction whenever the deadline for a milestone associated with a milestone-based SV CIP passes." Removal then needs a recommendation, an off-chain SV vote and an on-chain vote. Some deadlines may also have been extended, and some milestones run from another event rather than a date. What the public record shows is narrower: for 16 grants holding 69 weight, every dated deadline has passed, and the outcome of the required review is not in any public source I could find.

Seven grants, holding 67 weight, did not publish their milestones (for example, CIP-0110 says Apollo's "specific commitments, timelines, and commercial details will remain confidential"). For these, the community cannot tell how close the organisation is to earning its weight.

## 5. Two smaller findings

**A configuration that listed more weight than the node had.** On four occasions in January, February and May 2026, the file gave the GSF node's beneficiaries more weight than the node itself (by 0.45, and once by 2.9). The SV app handles this safely: `weightDistributionForSv` in `SvUtil.scala` walks the list in order and caps the last beneficiaries at the remaining weight, so no extra CC was minted. The beneficiaries that were capped were the last in the list, the DTCC escrow party (9.55 instead of 10 for about 23 days) and the Société Générale escrow party (5.1 instead of 8 for about one day). Both are escrow parties, so no active participant was paid less.

**A documentation mismatch.** The [tokenomics reference](https://docs.canton.network/overview/reference/tokenomics-of-gs) says "Unclaimed rewards beyond all tranches go to SV rewards". In the code, the SV tranche is a fixed share, and unclaimed validator, app and SV rewards are recorded together in an `UnclaimedReward` contract (`AmuletRules.daml`, around line 600). The page would be clearer if it said that.

## 6. Suggestions

1. **Publish an escrow view.** One page, generated from the config repository, listing each grant: CIP, escrowed weight, active weight, milestones and their deadlines. The code in this repository already produces it.
2. **Record the CIP-0111 reviews publicly.** When the TWG reviews a grant after a deadline, a one-line public outcome (met, extended to a date, or reduced) would show that the process is working.
3. **Publish at least the milestone dates for confidential grants.** The commercial details can stay private. The deadline and the weight attached to it are enough for the community to follow progress.

## Method and limits

- **Weights** come from every commit of `configs/MainNet/approved-sv-id-values.yaml`. A party is classed as escrow if its name contains "ghost" or "escrow", or it is hosted on one of the three ghost validators. "Unassigned" is `GhostSV-validator-1`.
- **Node totals** are verified against the live on-chain `DsoRules`. Beneficiary splits are SV app configuration and are not on-chain, so they cannot be checked the same way. One commit (#358) says it aligned "public extraBeneficiaries with the actual SV configuration", so the public file can drift from the running configuration.
- **Rewards** use the formula in `Issuance.daml` and the live issuance curve. They assume every coupon is created. The escrowed share is what that weight would earn, based on CIP-0066's description that escrowed parties are not minted. Scan endpoints were not reachable without an allowlisted IP, so the actual unminted pool was not measured.
- **Deadlines** were extracted from the CIP texts (canton-foundation/cips at 92df641). Undated milestones (for example "180 days after go-live") are not counted as passed.
- Before January 2025 the file did not list beneficiaries, so all early weight shows as kept by the node.

## Reproduce it

```
git clone https://github.com/canton-foundation/configs
git clone https://github.com/<you>/canton-sv-weights && cd canton-sv-weights
python3 src/extract.py ../configs
python3 src/lifecycle.py
python3 src/dilution.py
python3 src/deadlines.py
```

*Disclosure: I hold no CC and have no commercial relationship with any organisation named here.*
