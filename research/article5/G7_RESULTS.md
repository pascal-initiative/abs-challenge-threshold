# ABS-05 Gate G7 Result

**Build status: PASS**
**Scientific status: RESTRICTED — `deltaW` zero by construction**

G7 validates the dynamic program and inventory accounting. It does not validate
an optimal MLB player policy, a player-confidence model, or an article playbook.

## What validated

The exact backward recursion processed 334,948 eligible future-stream
opportunities across 4,390 team-games. This includes all 312,228 observed legal
decisions plus 22,720 calls observed after inventory exhaustion. Keeping those
later calls prevents the observed policy from censoring the opportunity stream
for a counterfactual policy that might still have inventory.

The computational checks passed:

- success retains a challenge unit and failure consumes one;
- an extra-inning grant restores zero inventory to one but does not increment
  positive inventory;
- game end truncates future value;
- tiny sequences match brute-force enumeration;
- the dynamic policy weakly dominates every fixed comparator for every
  team-game and probability scenario;
- all canonical values and thresholds are finite, nonnegative where required,
  and thresholds lie in `[0, 1]`; and
- a 50,000-repetition Monte Carlo check was within four standard errors of the
  recursion (1.503951 simulated versus 1.506901 exact; difference 0.002949,
  standard error 0.004722).

Two clean builds were byte-identical.

## What the values mean

G7 evaluates five explicitly labeled probability scenarios: fixed confidence
of 0.50, 0.60, and 0.70; the G6 public-tracking full-fit benchmark; and the G6
challenger-selected transport assumption. The fitted scenarios are sensitivity
inputs, not estimates of what a player knew.

For the dynamic policy, mean marginal option values varied substantially by
scenario:

| Probability scenario | Mean `C(1)` | Mean `C(2)` |
| --- | ---: | ---: |
| Public-tracking benchmark | 0.1849 | 0.1060 |
| Fixed 0.50 | 0.5974 | 0.4425 |
| Challenger-selected transport assumption | 0.9159 | 0.6885 |

This spread is the result: the option values are highly assumption-sensitive.
They must not be presented as player-policy estimates or compared directly with
Article 4's league-behavior value without explaining the different policy and
information assumptions.

Marginal inventory value was concave in 99.9909% of evaluated team-game and
scenario combinations. Two exceptions occurred in the same extra-inning
team-game under two probability scenarios, where the zero-to-one extra-inning
grant interacts with inventory held before extras. Concavity is therefore not a
universal rule and remains a tested output rather than an engine assumption.

## Scientific restriction

The engine holds the observed subsequent pitch and game-state sequence fixed
after a hypothetical correction. As a result, `deltaW=0` by construction;
opponent response, changed plate-appearance outcomes, and rewritten game paths
are not modeled. The reported `C/(V+C)` values are restricted
empirical-sequence thresholds, not the final full-form Challenge Threshold.

G7 permits continued model-free and assumption-labeled threshold research. It
does not permit empirical evidence-to-action guidance, declarations that
players challenged incorrectly, or a Pascal ABS Challenge Playbook.

## Determinism and artifact hashes

| Artifact | SHA-256 |
| --- | --- |
| `VALIDATION.md` | `b8d29d8a672780d10da0acff0824ce30839b2dde65ef4ddd0cc72f73cd8ef392` |
| `game_summary.csv` | `1e5bab4ff308bd97f0cc0dc1cdfe20e464350994e46b26753ccc19ef8094459c` |
| `game_values.csv` | `641c34086561f3ad55caee173089d0fb22b569818feede5274fa8d81f8c15be5` |
| `manifest.json` | `c13230d85fb19d8dfe666e0d746a7a778d980d3d77d3aea68c95f3dce45de1c6` |
| `threshold_rows.csv` | `a3eabd0e9579679a58d57cb8dddcc98bec98d9ff0429d13c06f478f932483c48` |
| `threshold_summary.csv` | `027e1388bf7c0e62adf588bcaef5b3599e26dae62d924c3f8a8aa19bba215fa2` |
| `validation.json` | `bf399b400e2b30a56a55349ca328a1a7ed3683fbbc38f8af79ed5136d6b65ee2` |

## Resource use

The build used only the locked local snapshot and local computation. It
consumed no live data, paid API, GitHub Actions, Vercel, Supabase, or Odds API
resources. No additional Claude review was used; the Article 5
specialist/correction budget remains exhausted after G5.
