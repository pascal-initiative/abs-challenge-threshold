# ABS-05 Gate G8 Result

**Computational status: PASS**
**Gate status: FAIL — stability limit exceeded; win-probability sensitivity rejected**
**Playbook status: PROHIBITED**

G8 is a substantive scientific stop. The audit ran as specified and reproduced
deterministically, but the assumption-conditional actions were not stable
enough to support situational recommendations.

## Fixed audit population

The reference used the constrained G5 correction value, fixed 0.60 success
probability, G7 dynamic policy, documented extra-inning restoration, and one or
two units evaluated separately. Fixed 0.60 is an audit anchor, not estimated
player confidence.

The empirical 90th-percentile correction-value cutoff was 0.290737 runs. Ties
produced 31,443 decisions, or 10.071% of the 312,228 legal-decision population.
Every sensitivity used these same pitch keys.

## Primary flip result

Five of 18 available sensitivity/inventory comparisons exceeded the
preregistered 10% ceiling.

| Sensitivity | Inventory 1 | Inventory 2 | Result |
| --- | ---: | ---: | --- |
| Unconstrained partially pooled RE288 | 0.65% | 0.66% | Pass |
| Pooled-count RE | 9.32% | 11.31% | **Fail for two units** |
| Raw RE288 | 3.98% | 3.71% | Pass |
| Leave-one-month-out RE288 | 3.68% | 3.48% | Pass |
| Fixed probability 0.50 | 6.37% | 6.08% | Pass |
| Fixed probability 0.70 | 8.47% | 7.96% | Pass |
| Public-tracking benchmark | 45.96% | 61.27% | **Fail** |
| Challenger-selected transport assumption | 23.25% | 22.45% | **Fail** |
| No extra-inning restoration | 1.33% | 1.05% | Pass |

The fixed-probability range was comparatively stable, but the two fitted G6
benchmarks were not. This is consistent with G6's conclusion: the public model
and selected-challenger model represent different information and selection
processes, and neither identifies subjective player confidence. Their large
disagreement cannot be converted into player advice.

The correction-value sensitivities also reinforce the G5 constraint. Across the
complete future stream, the unconstrained smoothed, raw, and
leave-one-month-out variants generated 1,365, 1,423, and 1,957 negative flip
values, respectively; the constrained and pooled-count variants generated
none. These negatives were preserved in the audit rather than clipped.

## Scenario and distribution audits

Thirteen of the prespecified scenario/inventory/sensitivity comparisons crossed
the neutral validation bands at 0.50 and 0.70 required confidence. All crossings
are recorded in `scenario_stability.csv`. They are concentrated in probability
sensitivities, including full counts, late/close states, two-out
runner-in-scoring-position states, and the public-tracking benchmark broadly.

The reference early/late distribution was comparatively similar. For one unit,
the reference action rate was 11.78% in the early date half and 11.90% in the
late half; for two units it was 20.32% and 20.49%. Median constrained correction
value moved from 0.121092 to 0.113186 runs. This is descriptive distribution
evidence, not proof of temporal policy stability.

The 38 bounded ambiguous runner-action rows were also unstable. Lower-bound
replacement changed 34.21% of one-unit actions and 21.05% of two-unit actions;
upper-bound replacement changed 18.42% and 7.89%. These rows remain outside the
primary flip denominator and cannot support scenario advice.

## Objective-scale follow-up

After this result was accepted, Amendment 002 authorized a bounded attempt to
close the win-probability and opponent-policy gaps without changing the failed
gate.

The rolling-origin home win model was descriptively strong: overall Brier score
was 0.159645 versus 0.249914 for the expanding baseline, AUC was 0.8450, and
10-bin ECE was 0.0175. Late/close ECE was 0.0434. It nevertheless failed the
predeclared counterfactual checks. It assigned the wrong sign to 5,310 of
334,948 future-stream corrections (1.585%), including 591 rows in the fixed
top-value population. Every wrong-sign value crossed a half-inning phase; none
occurred within a phase. The phase model therefore describes observed win
frequency but cannot value call corrections coherently across inning-ending
transitions.

Run-scale versus invalid win-scale actions differed on 24.72% of top-value rows
with one unit and 22.32% with two. These are diagnostic failure results, not an
accepted objective sensitivity.

Opponent value cancels exactly from CHALLENGE minus HOLD under G7's independent
fixed-path additive construction, for both league-typical and optimized policy
values. That closes accounting only inside the restricted model; opponent
response, strategic interaction, and rewritten game paths remain unmodeled.

G7's `deltaW=0` construction and G6's unidentified player-confidence mapping
also remain unresolved. See `G8_OBJECTIVE_RESULTS.md` for the follow-up record.

## Consequence

The Article 5 work may continue only as a model-free or explicitly
assumption-labeled decision framework. It may not provide situational challenge
recommendations, claim an optimal MLB policy, judge observed player decisions,
or produce the Pascal ABS Challenge Playbook. A downstream result cannot
override this failed gate.

## Determinism and artifact hashes

Two clean builds in separate output directories were byte-identical.

| Artifact | SHA-256 |
| --- | --- |
| `VALIDATION.md` | `02a8be78e59dcdde2a543972ed99ca8b720e240c54c0b2345d89ce3a0a61d791` |
| `ambiguous_bounds.csv` | `f363b2de4e6dd0505cb67451e2de35c92d2118043d20cb550cafee528ed318b1` |
| `distribution_shift.csv` | `7f34497fd445716845fa1e2e0c695dfc3f8ae96a44b5cfcf249400f3ac674f80` |
| `flip_summary.csv` | `930a848c2a4e99993d250d3823b09d2ee40c294031211d54d88c01d41393ec0a` |
| `manifest.json` | `535e19abd5c64078b41770cf23829fa38b09ce720410a31db8866207aba317ea` |
| `scenario_stability.csv` | `4b253f471e1385035ac153871fd639619244b751fc628ba17e5669f8299e315c` |
| `top_value_actions.csv` | `e6453b62379f1f668efab8d1b3402f58e253b55539feb951834831eb76467804` |
| `validation.json` | `d617acc1f6b6515af74d3e538c550b157e7cab26ae4d9d3656e44e80a03f4f2b` |

## Verification and resources

The build used only the locked local snapshot and local computation. It
consumed no live data, paid API, GitHub Actions, Vercel, Supabase, Odds API, or
additional Claude review. No planned available comparison was skipped; the
three unavailable mandatory variants are recorded as gate limitations rather
than silently omitted.
