# Challenge Threshold 2026 Reference Specification

## Freeze status

This specification is frozen before the CT-2026 publication table is built.
It defines a reference evaluator, not a player-confidence model, action
recommendation, or empirical playbook.

CT-2026 is authorized by the ABS-05 preregistration, which makes the threshold
primary and model-free while treating the mapping from evidence to belief as a
separate layer. The G8 failure remains controlling for prescriptive translation.

## Public definition

**Challenge Threshold is the minimum confidence that an ABS call is wrong
required for challenging to break even under a declared value model.**

The preferred public interpretation is:

> Challenge Threshold tells you how sure you need to be. It does not tell you
> how sure you are.

A lower value means less confidence is required to justify risking a challenge
unit. A higher value means stronger evidence is required. CT evaluates the
situation; the player, catcher, coach, or team supplies the belief.

## Version name and scope

- Public name: **Challenge Threshold**
- Short name: **CT**
- Reference version: **CT-2026**
- Analytical label: **CT-2026 run-value reference**
- Data window: 2026-03-25 through 2026-09-09
- Objective: expected runs for the team entitled to challenge
- Supported sides: offense after a called strike and defense after a called ball
- Supported inventory: one or two challenge units before the pitch
- Challenge mechanics: success retains the unit; failure consumes one; a team
  with zero receives one at the start of an extra inning; positive inventory is
  not incremented

CT-2026 is a versioned seasonal reference. It is not an unchanging baseball
constant and must not be silently recomputed after publication.

## Mathematical definition

Let:

- `V` be the immediate expected-run value of correcting the call if it is wrong;
- `C` be the marginal future expected-run value of the challenge unit at risk;
- `deltaW` be the change in subsequent game value caused by correcting the call;
  and
- `p` be the decision maker's confidence that the challenge will succeed.

The general break-even threshold is:

```text
CT = C / (V + deltaW + C)
```

The current empirical-sequence engine holds the observed subsequent game path
fixed. CT-2026 therefore uses:

```text
CT-2026 = C_reference / (V_reference + C_reference)
deltaW  = 0 by construction
```

Every publication table, figure, feed, or interface must carry the fixed-path
restriction. CT-2026 must not be described as the final win-probability form of
the metric.

### Boundary cases

- If `V > 0` and `C = 0`, CT is 0%.
- If `V = 0` and `C > 0`, CT is 100%.
- If `V = 0` and `C = 0`, CT is undefined and the row is not published.
- Inputs and outputs must be finite; CT must lie in `[0, 1]` before formatting.
- Ties at `p = CT` are break-even. CT itself does not prescribe whether a team
  with non-run preferences should challenge on a tie.

## Reference correction value

`V_reference` is the G5 constrained, partially pooled count-aware run-expectancy
value of flipping the on-field call. It is oriented to the team entitled to
challenge and uses only the pre-pitch count, outs, bases, and call as made.

The correction-value lookup must:

- preserve the G5 monotonicity constraints;
- distinguish offense and defense through the call transition;
- exclude position-player pitching and legally unavailable states;
- exclude ambiguous runner-placement cases from the reference point estimate;
- retain the approved ambiguous lower and upper values as a separate diagnostic;
  and
- never use realized runs after the pitch.

CT-2026 may display Article 4 values for historical comparison only when the
different estimator is named. Article 4's pooled value must not be silently
substituted for `V_reference`.

## Reference inventory cost

### Reference convention

`C_reference` uses a non-clairvoyant fixed future-use policy with the G7
inventory mechanics and preregistered conventions:

- fixed future success input of 0.60 at every future opportunity;
- the G5 constrained correction-value estimator;
- the documented extra-inning grant;
- challenge a future opportunity when `0.60 * V >= 0.05` expected runs;
- one and two units solved separately; and
- `deltaW=0` because the future game path is held fixed.

The fixed 0.60 input is a **standardization convention for pricing future
inventory**. It is not an estimate of any player's confidence, a league-wide
probability that every call is wrong, or a claim that 60% is optimal. It was
frozen as the neutral G8 reference before the stability results were observed.
The 0.05 expected-run use policy was named in the original charter,
preregistration, G7 comparisons, and Article 4. Ties challenge. Neither value
was selected after inspecting CT-2026 thresholds.

### Non-clairvoyant fixed-policy evaluation

G7 chooses actions with the complete remaining observed opportunity sequence.
G9 demonstrated that exact-sequence allocation can retain value even after the
modeled correctness signal is removed. Averaging G7's row-level marginal costs
would therefore carry a privileged-future component into CT-2026 and is
prohibited.

CT-2026 treats the observed team-game sequences as draws from the distribution
of possible futures. At each observed future opportunity, the reference policy
uses only fixed `p=0.60` and the opportunity's current correction value. It does
not use the identity or contents of the remaining sequence, its row-level
marginal inventory cost, or a fitted player-probability model.

Use deterministic fixed-policy evaluation:

1. Set the future action to CHALLENGE when `0.60 * V_reference >= 0.05` and
   inventory is positive; otherwise HOLD.
2. Evaluate those frozen actions over every complete historical team-game
   sequence using G7's success-retention, failure-consumption, extra-inning
   grant, and game-truncation mechanics.
3. For each state and inventory, set the schedule to the arithmetic mean of the
   evaluated marginal continuation values across matching historical rows,
   using the mechanical support hierarchy below.

There is no fitted action loop and no convergence parameter. The failed
state-policy iteration and rejected relaxation checks remain documented in
`CT2026_CT2_RESULTS.md`; their values are not CT-2026 inputs.

For a supported state `s` and inventory `k`, the reference schedule is:

```text
C_reference(s, k) = expected marginal continuation value under the fixed
                     CT-2026 future-use convention
```

Compute CT from `C_reference` and `V_reference`. Do not average historical
row-level thresholds; combine the expected-value inputs before applying the
nonlinear threshold transformation.

G7 exact-sequence values remain a mechanics check and a privileged-information
upper diagnostic. They are never CT-2026 reference inputs or publication values.

### Inventory-cost state

The primary schedule uses:

- regulation inning `1` through `9`, with `10+` for extras;
- top or bottom half;
- outs `0`, `1`, or `2` before the pitch;
- entitled-team role `HOME` or `AWAY`;
- entitled-team score bucket: trailing by two or more, trailing by one, tied,
  leading by one, or leading by two or more;
- inventory `1` or `2`; and
- extra-inning grant eligibility implied by inning and inventory.

Count, bases, and call side determine `V_reference`; they do not enter the
primary inventory-cost schedule. A later version may add them only through a
new frozen specification and demonstrated out-of-sample improvement.

### Mechanical support hierarchy

Use the most specific state with at least 200 historical decisions from at
least 100 distinct games. If support is insufficient, apply this exact backoff:

1. drop score bucket;
2. then drop entitled-team role;
3. then replace exact inning with `1-3`, `4-6`, `7-9`, or `10+`;
4. then drop half-inning; and
5. stop without publishing if the resulting state still fails support.

Outs and inventory may never be dropped. Record the selected support level,
row count, and distinct-game count on every output row. No analyst-selected
backoff is permitted.

## Publication table

The evaluator population is every supported, legal called-pitch state, whether
the historical call was later shown to be correct or incorrect. The table is a
state grid, not an incorrect-calls leaderboard.

Each row must contain:

- `ct_version`;
- call side and call as made;
- balls, strikes, outs, and base state;
- inning, half, score bucket, team role, and inventory;
- `correction_value_runs_reference`;
- `inventory_cost_runs_reference`;
- `challenge_threshold_reference`;
- `challenge_threshold_core_low` and `challenge_threshold_core_high`;
- support/backoff level, historical rows, and distinct games;
- fixed-path and information labels;
- publication eligibility and any exclusion reason; and
- source artifact hashes.

The machine-readable table stores decimal values at full deterministic
precision. Reader-facing products show CT as a whole percentage; methodology
tables may show one decimal place. Values must be rounded, never truncated.

## Sensitivity range

The reference estimate remains the single CT-2026 comparison number. It must be
accompanied by a visible range when the range is material.

The **core range** varies only prespecified supported conventions:

- fixed future success inputs 0.50, 0.60, and 0.70;
- fixed expected-value use cutoffs 0.00, 0.05, and 0.10 runs;
- G5 constrained, Article 4 pooled-count, and Article 4 raw RE288 correction
  values where valid;
- extra-inning restoration on and off for states whose future horizon can reach
  extra innings; and
- ambiguous runner-placement lower and upper bounds only for the affected
  diagnostic rows.

The public-tracking and challenger-selected probability scenarios are reported
as **diagnostic alternatives**, not included as equal-weight endpoints of the
core range. The selected transport model failed transport identification, and
the public model does not represent player-observed evidence.

Article 4's league-typical option values and G7's exact-sequence values are also
reported as incompatible-estimand diagnostics. The former describes observed
league use; the latter has privileged future allocation. Neither replaces or
sets an endpoint of the CT-2026 core range.

For each table state, report the minimum and maximum CT across the applicable
core variants. A range width greater than 10 percentage points receives a
`MATERIAL_MODEL_SENSITIVITY` flag. The 10-point display flag is an editorial
disclosure threshold, not a new scientific pass/fail rule and not a replacement
for the G8 action-flip result.

## Uncertainty

Estimate sampling uncertainty for `C_reference` with a deterministic
game-clustered bootstrap. Freeze the seed, replicate count, and interval method
in the build implementation before inspecting intervals. Games, not pitches,
are the resampling unit.

Sampling intervals and model-sensitivity ranges answer different questions and
must be displayed separately:

- sampling interval: variation from the historical game sample;
- model range: variation from approved analytical choices.

Do not merge them into one interval.

## Representative article states

Select examples mechanically after the full table validates:

1. one ordinary supported state nearest the median reference CT;
2. one supported state in the lowest reference-CT decile;
3. one supported state in the highest reference-CT decile;
4. one matched early/late pair with identical count, outs, bases, call side,
   score bucket, team role, and inventory where support permits; and
5. one matched one-unit/two-unit pair.

Ties are resolved by descending support and then lexical state key. Examples
may be rejected for clarity or redundancy only with a written reason; they may
not be replaced by a more dramatic hand-selected value.

Labels such as “easy challenge,” “preserve,” “good,” “bad,” or traffic-light
colors are prohibited in CT-2026. Use neutral descriptions such as lower,
middle, and higher required confidence.

## Permitted uses

- compare the price of challenging across supported game states;
- state how much confidence the reference model requires;
- explain why count, runners, outs, inning, and inventory move the threshold;
- give broadcasters and readers a common reference number;
- compare CT versions after documenting model and rules changes; and
- let a decision maker compare their own belief with CT without Pascal
  estimating that belief.

## Prohibited uses

- infer a player's subjective confidence from CT;
- declare an observed challenge, pass, success, or failure correct or incorrect;
- treat an unused challenge as wasted;
- call CT an empirical success probability;
- publish a dynamic-policy action as CT;
- claim the fixed 0.60 convention describes every player or pitch;
- claim CT-2026 optimizes wins or includes strategic opponent response;
- use the exact remaining realized sequence in a public event-level value;
- rank players or teams by “decision quality” without a separately validated
  evidence model; or
- publish a Pascal ABS Challenge Playbook.

## Versioning and recalculation

Freeze and archive every public version with its table, specification, code,
manifest, and source hashes. A new major seasonal version is required when any
of the following changes materially:

- ABS zone or challenge rules;
- starting inventory or extra-inning restoration;
- run environment;
- tracking or data definitions;
- reference correction-value estimator;
- future-inventory convention or policy; or
- supported-state design.

Within-season corrections receive a dated patch version and changelog. Never
overwrite a previously published table without retaining the prior artifact.

The locked September 9 snapshot may be published as `CT-2026.0-snapshot`. A
full-season rebuild, if performed, becomes a separately validated version rather
than silently replacing the snapshot.

## Resource ceiling

Resource class is R0. Reuse the locked local snapshot and local computation.
No live acquisition, paid source, GitHub Actions, Vercel, Supabase, Odds API,
hosted database, production system, or additional Claude exchange is authorized
for the specification and reference-table build.
