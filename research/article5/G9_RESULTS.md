# ABS-05 Gate G9 Result

**Computational status: PASS**

**Numerical benchmark condition: PASS**

**Scientific status: NOT DEMONSTRATED — NONDEPLOYABLE UPPER BENCHMARK**

**Playbook status: PROHIBITED**

G9 completed the preregistered effect-size comparison. The exact-sequence
dynamic benchmark cleared the numerical threshold, but the result does not
demonstrate a practical decision policy. The benchmark knows the complete
remaining empirical opportunity sequence, G6 did not identify player
confidence, G8 rejected the win-probability model, and the shuffled-label
falsification retained a positive advantage.

## Primary numerical result

The primary analysis used the G5 constrained correction value, fixed `p=0.60`,
two starting challenge units, the documented extra-inning restoration rule,
and all 4,390 team-games in 2,195 game clusters.

The exact-sequence dynamic benchmark averaged 1.477066 expected runs per
team-game. The best simple non-oracle comparator was `p * V >= 0.05`, averaging
0.567449. The difference was **0.909617 expected runs per team-game**, with a
game-clustered 95% bootstrap interval of **0.894625 to 0.924834**. This exceeds
the preregistered 0.01-run minimum and its interval excludes zero.

For one starting unit, the corresponding difference was 0.593946 expected runs
per team-game (95% interval 0.584444 to 0.604031).

These are upper-benchmark values under independent Bernoulli success draws and
the observed future opportunity sequence. They are not estimates of value an
MLB team could obtain at decision time.

## Sensitivity results

All reported differences compare the exact-sequence benchmark with the best
simple comparator selected within each bootstrap replicate.

| Probability scenario | Starting units | Best simple policy | Difference | 95% interval |
| --- | ---: | --- | ---: | ---: |
| Fixed 0.50 | 1 | `p * V >= 0.05` | 0.439982 | 0.432579–0.447448 |
| Fixed 0.50 | 2 | `p * V >= 0.05` | 0.679016 | 0.667490–0.690786 |
| Fixed 0.60 | 1 | `p * V >= 0.05` | 0.593946 | 0.584444–0.604031 |
| Fixed 0.60 | 2 | `p * V >= 0.05` | 0.909617 | 0.894625–0.924834 |
| Fixed 0.70 | 1 | `p * V >= 0.05` | 0.774218 | 0.761841–0.786814 |
| Fixed 0.70 | 2 | `p * V >= 0.05` | 1.161801 | 1.142620–1.181042 |
| Public-tracking benchmark | 1 | `p * V >= 0.05` | 0.055774 | 0.053325–0.058321 |
| Public-tracking benchmark | 2 | `p * V >= 0.05` | 0.058332 | 0.056141–0.060592 |
| Challenger-selected transport | 1 | confidence 0.60 | 0.604161 | 0.594832–0.613851 |
| Challenger-selected transport | 2 | confidence 0.60 | 0.928561 | 0.913354–0.943603 |

The observed league realized 0.224861 corrected-call runs per team-game. The
hindsight oracle averaged 0.742353. These quantities are descriptive only and
were excluded from the comparator set: observed actions use selected private
information and realized outcomes, while the oracle knows correctness and
never loses inventory.

## Mandatory falsification

The public correctness labels were shuffled with seed `20260925`, the frozen
G6 formula was refit, and the resulting in-sample AUC against shuffled labels
was 0.505590, inside the required 0.48–0.52 range.

Despite the absence of useful label information, the two-unit exact-sequence
benchmark still exceeded its best simple comparator by 0.035166 expected runs
per team-game (95% interval 0.034343 to 0.035992). The one-unit difference was
0.018918 (0.018304 to 0.019555).

This falsification shows that a positive benchmark advantage can arise from
exact knowledge of the future opportunity/value sequence even when the
probability model contains no validated label signal. It is therefore not
evidence that a decision-time dynamic policy improves on simple rules.

## Consequence

The numerical benchmark condition passes, but the scientific G9 claim does
not. C05 may describe the computational upper-bound result only. It may not be
translated into a deployable threshold, team recommendation, judgment of
observed decisions, or practical playbook.

The G8 stop remains controlling. The Article 5 work may continue only as a
model-free or explicitly assumption-labeled framework unless the unresolved
decision-time information, counterfactual game-path, objective-scale, and
strategic-response problems are solved in a newly authorized research plan.

## Determinism and artifact hashes

Two clean builds in separate output directories were byte-identical.

| Artifact | SHA-256 |
| --- | --- |
| `VALIDATION.md` | `0da934b688bdcf77514cf9965b186dd32a054ea66d5e99a347adef9df765eab4` |
| `descriptive_benchmarks.csv` | `70c4290bb635763007c316b978e9b086d0afa94c3e5aab08883a8f3ee3250e63` |
| `effect_size.csv` | `42fe8d9dc7af5b3205a45c5550bc749c376c98eaf39bc9f4d33376ef949b4ed0` |
| `manifest.json` | `c78dad815364a6ea5346cdd1017f5d39f0f6a3247766bc27fec3e59285160332` |
| `policy_summary.csv` | `a94ade8d4d845b7662aba7c21804bad40ad9070a04336f8f017e0e4ca282d153` |
| `shuffle_diagnostic.json` | `130aa28338026962506daadc414d6913173ac292704b384c6f6352d1072c2064` |
| `team_game_values.csv` | `1a9754bba3505b98c7929acd9077cfd4512371ca4c0813879e4cf8b436d710e0` |
| `validation.json` | `708ae8d75aed9bc8d1ed88e6671e31485f4dd07f837b9e25c5bbaa753aa1daf9` |

## Verification and resources

The G9 build used 10,000 deterministic game-cluster bootstrap replicates and
only the locked local snapshot. It consumed no live data, paid source, GitHub
Actions, Vercel, Supabase, Odds API, or additional Claude exchange. The
rejected G8 win-probability comparison was deliberately not reused, as frozen
in the G9 specification. Observed and oracle results were retained only as
incompatible-estimand descriptive benchmarks.

All 37 Article 5 unit tests passed. The broader 132-test repository run exposed
one legacy fixture issue: the Sprint 3 determinism test regenerates an ignored
manifest with the current Git commit, which cannot match the frozen historical
manifest hash and temporarily causes two Sprint 4 dependency failures. The
accepted manifest was restored from the checksum-verified Google Drive backup;
both affected Sprint 4 tests then passed. No G9 code or result depends on that
legacy manifest.
