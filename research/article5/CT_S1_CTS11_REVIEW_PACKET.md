# CT-S1 CTS11 Bounded Adversarial Review Packet

## Reviewer task

Review only the proposed CTS11 public-claim boundary below. Look for unsupported
wording, denominator errors, hindsight or player-belief leakage, confusion
between sampling uncertainty and model spread, and any sentence that becomes a
playbook, optimal-policy claim, or grade of a player decision.

Return one bounded response with:

1. **Blocking defects** that must prevent numerical drafting;
2. **Nonblocking wording corrections**;
3. **Decision:** `PASS`, `PASS WITH CORRECTIONS`, or `FAIL`;
4. a one-sentence explanation of the strongest counterargument to publication.

Do not propose a new model, request new analysis, rewrite the article, or infer
facts outside this packet.

## Interpretation contract

Challenge Threshold tells you how sure you need to be under a named value
model. It does not tell you how sure you are.

The CT-S1 reference is `C / (V + C)` under a fixed-path expected-runs model.
`V` is immediate correction value and `C` is modeled future inventory value.
The reference convention uses `p=0.60` and future use when
`p × correction value >= 0.05` runs. `deltaW` is zero by construction. This is
a standardization choice, not player belief and not an optimal policy.

## Proposed publishable boundary

- Confirmation support: 22,584 of 24,880 state/inventory candidates, or
  90.7717%, using development March 25-September 9 and untouched confirmation
  September 11-27. September 10 is in neither period.
- Frozen-reference temporal stability across 22,584 matched rows: median
  absolute drift 0.007628, 90th-percentile drift 0.026143, and Spearman
  correlation 0.995354.
- Convention sensitivity: 21,942 of 22,428 complete supported development rows
  and 21,929 of 22,428 confirmation rows had model-spread width above 0.10,
  about 98% in each period. The spread must travel with affected point values
  and cannot be called a confidence interval.
- One of three development-selected ordinary representative contrasts survived
  the frozen test. It was an offensive challenge of an original called strike,
  bottom fifth, home team trailing by at least two, bases empty, no outs, two
  units. The named reference was 0.668030 at 1-1 and 0.595135 at 1-2 in
  development, and 0.672804 versus 0.600331 in confirmation. Under the named
  model, the terminal-count state required about 7.3 percentage points less
  confidence. All eight alternatives preserved direction, but levels differed.
  The failed early/late and inventory representatives were retained.
- For that contrast, confirmation 95% game-clustered sampling intervals were
  0.648558-0.696556 at 1-1 and 0.574113-0.626422 at 1-2. Separate model-spread
  ranges were 0.587087-0.756986 and 0.509469-0.694697. The intervals use 2,000
  replicates and hold the named implementation fixed.
- Two complete isolated builds reproduced 25 files byte-for-byte with no
  differences or exclusions, left 447 protected inputs unchanged, and passed
  99 focused tests. This is computational reproducibility, not proof of unique
  scientific correctness.

## Proposed decision

Authorize numerical drafting of a versioned **Challenge Threshold Standard 1
(CT-S1)** reference-evaluator article and companion methodology, limited to the
claims above. Require model spread next to affected point values and require
the fixed-path, required-confidence, and player-belief caveats.

Do not authorize a Pascal ABS Challenge Playbook, challenge/preserve action
bands, claims of optimal strategy, grades of observed decisions, universal
count rules, or the failed predecessor name `CT-2026`.
