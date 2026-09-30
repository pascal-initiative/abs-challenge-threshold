# ABS-05 Findings Outline

> **Historical predecessor outline:** This file records the G5--G10 evidence
> before the failed `CT-2026` build and the CT-S1 holdout validation. It is not
> the numerical drafting outline authorized by CTS11. Use
> `CT_S1_PUBLIC_CLAIMS.json` and `CT_S1_DRAFTING_DECISION.md` for the successor
> outline; preserve this file as the earlier failure record.

## Editorial status

This is an evidence-grounded outline, not finished article prose and not the
Pascal ABS Challenge Playbook. It is authorized by G10 only within the
restrictions in the claim ledger.

The article may explain the decision framework, report measured and modeled
results, and make the failed validation gates part of the story. It may not
tell players when to challenge, publish situational recommendations, judge
observed decisions, or describe the exact-sequence benchmark as deployable.

## Recommended editorial direction

### Working title

**How Sure Is Sure Enough to Challenge an ABS Call?**

This title is locked by the editorial review. Article 2 already uses “The
Challenge Threshold” for a behavioral study. Article 5 should connect that work
to a distinct value-based definition: the break-even confidence required by
the situation.

### One-sentence thesis

Challenge Threshold places an ABS opportunity on a common scale by estimating
how confident a player needs to be for a challenge to break even; it evaluates
the situation without claiming to know the player's confidence.

### Reader promise

The reader should finish understanding:

1. why the value of correcting a call is only one part of the decision;
2. how correction value, failure cost, and pass cost produce a required
   confidence percentage;
3. how to interpret and compare Challenge Threshold values;
4. why the metric does not estimate an individual player's belief; and
5. why reference values need declared assumptions, ranges, and annual versions.

### What this article must not promise

- an assumption-free or timeless threshold value;
- proof that MLB players or teams challenge badly;
- proof that unused inventory was wasted;
- an estimate of a particular player's subjective confidence;
- a deployable optimal policy; or
- win-probability advice from the rejected phase model.

## The central finding

The cleanest story is:

> Challenge Threshold tells you how sure you need to be. It does not tell you
> how sure you are.

The immediate consequence of a corrected call can be estimated. Inventory can
be represented in a dynamic program. A break-even confidence threshold can be
defined and published under named assumptions. The player, catcher, coach, or
team supplies the confidence judgment that determines whether their evidence
clears that threshold.

The failed gates constrain the interpretation rather than erase the metric.
They prohibit an empirical playbook, judgment of observed choices, or universal
optimal policy. They require the reference threshold to carry its model version
and material sensitivity range.

## Evidence hierarchy

### Measured

- The locked 2026 snapshot contains 2,195 games, 312,228 legal called-pitch
  decisions, and 9,485 official challenges.
- Publicly reconstructed ABS labels agreed with the official challenge result
  on 9,482 of 9,485 challenged pitches, or 99.968%.
- Among 9,199 out-of-time challenged pitches in the G6 evaluation, observed
  success was 53.74%. The public-tracking benchmark assigned those same pitches
  a mean incorrect-call probability of 24.92%. This is evidence of selection on
  omitted or private information, not a causal estimate of player skill.
- Article 4 found that 74.9% of team-games ended with at least one challenge
  remaining and 51.2% of challenge units expired unused. Neither fact proves a
  passed opportunity was a mistake.

### Modeled

- Under the G5 constrained run-expectancy surface, 20,124 non-ambiguous
  incorrect calls had a median correction value of 0.101169 runs, a mean of
  0.149446, and a maximum of 1.917099.
- Article 4's earlier pooled-count estimator gave a median of 0.111 runs; its
  top 10% of opportunities contained 29.8% of correctable value, and full
  counts were 3.0% of opportunities but 11.4% of value. The Article 4 and G5
  values use different accepted estimators and should be labeled rather than
  silently combined.
- In G7, mean marginal option value varied dramatically with the probability
  scenario. For one unit it ranged from 0.1849 runs under the public-tracking
  benchmark to 0.9159 under the challenger-selected transport assumption; for
  a second unit, from 0.1060 to 0.6885.
- In the high-correction-value audit population, five of 18 primary
  sensitivity/inventory comparisons exceeded the preregistered 10% action-flip
  ceiling. Public-tracking probabilities changed 45.96% of one-unit actions and
  61.27% of two-unit actions; challenger-selected transport changed 23.25% and
  22.45%.
- The exact-future-sequence benchmark exceeded the best simple comparator by
  0.909617 expected runs per team-game at fixed `p=0.60` with two units (95%
  game-clustered interval 0.894625 to 0.924834). This is a computational upper
  benchmark, not an achievable team estimate.
- After correctness labels were shuffled, the refitted model had AUC 0.505590,
  yet the exact-sequence benchmark still retained a 0.035166-run advantage
  (95% interval 0.034343 to 0.035992). The benchmark can gain from privileged
  future-sequence allocation even without useful label information.

### Assumed or restricted

- Fixed confidence values of 0.50, 0.60, and 0.70 are sensitivities, not
  estimates of player belief.
- G7 holds the subsequent observed opportunity sequence fixed, making
  `deltaW=0` by construction.
- The challenger-selected model is a transport assumption outside the selected
  challenged population.
- Opponent value cancels only inside the separable fixed-path construction;
  strategic response is not modeled.
- The attempted win-probability model was rejected after assigning the wrong
  sign to 5,310 of 334,948 counterfactual corrections, including 591 in the
  top-value audit population.

## Proposed article structure

### 1. Open on the decision, not the model

**Purpose:** Establish the tension in a few sentences.

A player has seconds to decide. If the call is wrong, correcting it can change
the count, end or revive a plate appearance, force in a run, or erase a
strikeout. If the player is wrong, the team loses future optionality. Passing
keeps the challenge but may surrender immediate value.

**Suggested turn:** “The question sounds like a rule-of-thumb problem. It is
actually a pricing problem under uncertainty.”

Do not open with a specific historical pass and imply it was wrong. A generic
decision moment is safer and cleaner.

### 2. Introduce the three prices

**Purpose:** Give readers the conceptual tool that organizes the article.

- **Correction value (`V`)**: the expected-run change if a wrong call is fixed.
- **Failure cost (`C`)**: the future option value lost if the challenge fails.
- **Pass cost**: the value forgone if the call was wrong and no challenge was
  made.

Use the full decision equation:

```text
Delta EV = p * (V + deltaW) - (1 - p) * C
p*       = C / (V + deltaW + C)
```

Explain `p*` as the minimum confidence required to break even. Present
`C/(V+C)` only as the restricted G7 version where `deltaW=0` by construction.
Do not present it as a universally validated formula.

### 3. The consequence of a call is measurable—and uneven

**Purpose:** Ground the framework in the strongest validated value result.

Lead with the G5 distribution: median 0.101 runs, mean 0.149, maximum 1.917
among 20,124 determinable incorrect calls. Then use the Article 4 concentration
result to make the distribution intuitive: the top 10% contained about 30% of
value, and 3-2 calls were only 3% of opportunities but 11.4% of value.

**Interpretation allowed:** Count and base-out state change the consequence of
a correction.

**Interpretation prohibited:** Therefore a player should challenge a named
count or game state.

Briefly explain why the G5 estimator imposed baseball-consistent monotonicity.
The first attempt produced negative values because ball four can cross base
states; the corrected global constraint removed that contradiction. This is a
useful transparency example, not implementation trivia.

### 4. A challenge in hand has value, but there is no single price

**Purpose:** Explain why “save it for later” is reasonable but incomplete.

Connect Article 4's league-behavior option value—about 0.080 runs at the start
of the first inning and 0.008 by the ninth—to G7's deeper result: option value
depends heavily on the assumed success information and future policy. G7's
scenario spread is too wide to collapse into one authoritative number.

Mention that the second challenge usually had lower marginal value, but two
extra-inning exceptions showed why concavity was tested rather than assumed.

Use the unused-inventory statistics only to describe behavior. Explicitly say
that successful challenges retain the unit and that unused inventory is not
evidence of an error.

### 5. The threshold and the player's belief are different quantities

**Purpose:** Separate the evaluator from the person using it.

The public-tracking model was highly discriminating and well calibrated on its
own information set (AUC 0.9261; Brier 0.0457). But exact unsigned tracking
distance is not what a hitter or catcher directly observes. The
challenger-selected benchmark was much weaker out of time (AUC 0.5869; Brier
0.2426), and it describes people who already chose to challenge.

The 53.74% observed success versus 24.92% public-model mean on challenged
pitches is the clearest illustration: challenged pitches were selected using
information or processes the public model omits. That gap prevents the model
from claiming to know the player's `p`; it does not invalidate a model-free
break-even threshold.

This section should distinguish three questions:

1. Was the pitch actually wrong?
2. What evidence was available to the player?
3. How strongly should that evidence change the player's belief?

The data address the first much better than the second or third. Challenge
Threshold answers a fourth question: how high would the player's belief need
to be under the declared value assumptions?

### 6. The model failed the test that matters for advice

**Purpose:** Treat the G8 stop as a primary finding.

Explain the preregistered rule: among the top correction-value decile, plausible
sensitivities could not flip more than 10% of actions. Five of 18 comparisons
failed. The public and selected probability benchmarks changed roughly 22% to
61% of actions, and 13 scenario comparisons crossed editorial confidence
bands.

Then explain the win-probability follow-up. It predicted observed winners well
(AUC 0.8450) but failed counterfactual coherence at half-inning transitions.
This is the article's sharpest methodological lesson:

> Predicting what happened is not the same as correctly valuing what would have
> happened under a different call.

Do not publish the diagnostic run-versus-win action flips as alternative
recommendations. They are evidence that the rejected model matters, not usable
answers.

### 7. The tempting “optimal policy” result is an upper bound

**Purpose:** Defuse the largest number before readers mistake it for a promise.

Report the +0.909617-run fixed-0.60 result only after explaining that the
dynamic benchmark sees the entire remaining empirical sequence. Pair it
immediately with the shuffled-label result: an advantage survived even when
the fitted probability model had no useful label discrimination.

The supported interpretation is that privileged future allocation has value.
The unsupported interpretation is that an MLB team can realize the reported
gain or that the dynamic policy beats simple rules at decision time.

The observed league and hindsight-oracle values may appear in a small sidebar
or methods note—0.224861 and 0.742353 corrected-call runs per team-game—but not
as a ranking of policy quality because their information and outcome
conditions differ.

### 8. End with a shared evaluator, not a verdict

**Purpose:** Give the reader a useful conclusion without overclaiming.

The ending should return to the three prices. Baseball can estimate consequence
and model inventory. Challenge Threshold turns those quantities into the
minimum confidence required under declared assumptions. The player supplies the
belief; the metric supplies the price of acting on it.

**Suggested closing idea:** Challenge Threshold tells you how sure you need to
be. It does not tell you how sure you are.

## Recommended figures

Do not build publication figures until the draft passes factual review. The
editorial review permits the following four-figure set.

### Figure 1: The Three Prices of a Challenge

A conceptual diagram of correct challenge, failed challenge, and passed wrong
call. Show the common expected-run scale and the full threshold equation. This
is explanatory, not empirical advice.

### Figure 2: How to Read Challenge Threshold

A percentage spectrum with representative low- and high-threshold situations
under one named reference specification. These are evaluations of the game
state, not action recommendations.

### Figure 3: The Same Threshold, Different Beliefs

Show that a threshold remains fixed for a stated situation while people with
different evidence may place their confidence above or below it. Any confidence
values in this figure must be explicitly illustrative.

### Figure 4: One Metric, a Visible Range

Show the reference estimate and sanctioned sensitivity range for representative
states. Mark material instability rather than hiding it in a pooled average.

The Article 4 correction-value and option-value figures should be linked rather
than repeated. The G9 upper benchmark belongs in the methodology, not a main
figure. The originally proposed “Pascal ABS Challenge Playbook” figure should
not be produced.

## Sidebar candidates

### Why an unused challenge is not automatically wasted

Explain inventory retention after success, the difference between outcome and
decision quality, and why end-of-game inventory alone reveals neither the
player's evidence nor the value of prior passes.

### How a good prediction model can be a bad decision model

Use the rejected win model: strong aggregate prediction, wrong-sign
counterfactual transitions. Keep the example conceptual and avoid suggesting
the rejected values are close enough for use.

### Measured, modeled, assumed

A compact glossary keyed to the evidence hierarchy above. This would reinforce
Pascal's research identity and can become a recurring device in future
articles.

## Candidate callouts

Safe callouts:

- “Challenge Threshold tells you how sure you need to be—not how sure you are.”
- “The median correction was worth about one-tenth of a run.”
- “The decision depends on three prices, not one.”
- “The model could value a correction more reliably than it could reconstruct
  a player's confidence.”
- “Five of 18 stability comparisons crossed the preregistered failure line.”
- “A reproducible result can still be unfit for advice.”

Do not use:

- “Always challenge on 3-2.”
- “Teams leave value on the table.”
- “Players are too conservative with one challenge left.”
- “The optimal policy adds 0.91 runs per game.”
- “The public model knows whether the player should challenge.”

## Source map for editorial review

| Outline claim | Type | Primary source | Editorial restriction |
| --- | --- | --- | --- |
| Population and label fidelity | Measured | `output/input_audit.json` | Official challenged-pitch agreement only |
| Correction-value distribution | Modeled | `G5_RESULTS.md` | Incorrect-call population; constrained RE estimator |
| Article 4 concentration and inventory expiration | Modeled / measured | Article 4 analysis records | Do not infer decision error |
| Probability benchmark performance | Modeled | `G6_RESULTS.md` | Not player confidence |
| Inventory-value scenario spread | Modeled | `G7_RESULTS.md` | Fixed future path; named probability scenarios |
| Action instability | Modeled diagnostic | `G8_RESULTS.md` | No situational guidance |
| Rejected win sensitivity | Failed model diagnostic | `G8_OBJECTIVE_RESULTS.md` | Do not use for valuation |
| Exact-sequence effect size | Upper benchmark | `G9_RESULTS.md` | Nondeployable; pair with falsification |
| Reproducibility | Measured build property | `G10_RESULTS.md` | Does not upgrade scientific claims |

## Editorial decisions resolved

The editorial review in `EDITORIAL_REVIEW.md` locks the following choices:

1. foreground Challenge Threshold as a versioned reference evaluator;
2. keep the G9 upper benchmark in the companion methodology, not a main figure;
3. publish model-free or explicitly assumption-labeled threshold values and
   visible sensitivity ranges;
4. keep player confidence as a separate, unobserved input rather than a
   prerequisite for the metric;
5. publish under “How Sure Is Sure Enough to Challenge an ABS Call?” unless a
   later copy edit preserves the same metric-first framing; and
6. use no more than four main figures.

## Publication and distribution hooks

Recommended article length is roughly 1,900–2,300 words plus methods notes.
The main text should carry no more than four figures.

Safe newsletter subject lines:

- **How Sure Is Sure Enough to Challenge an ABS Call?**
- **Introducing Challenge Threshold**
- **The Three Prices Behind Every ABS Challenge**

Safe social sequence:

1. ask how sure a player needs to be;
2. introduce the three prices and the percentage scale;
3. show representative threshold values under a named reference version;
4. distinguish required confidence from the player's private belief; and
5. show the sensitivity range and explain why the metric is an evaluator rather
   than a verdict.

The primary page call to action should invite readers to subscribe for newly
published research, newsletter issues, public leaderboards, and competition
announcements. A secondary AnalytIQ beta invitation is appropriate only if it
does not imply that AnalytIQ currently implements a validated ABS challenge
playbook.

## Future research plan

The next research phase should not tune the current model until it produces a
playbook. It should attack the failed assumptions directly.

1. **Player-observed evidence study.** Collect or construct a defensible proxy
   for the hitter's and catcher's actual visual/auditory information. Validate
   offense and defense separately and prospectively.
2. **Belief calibration study.** Obtain confidence reports or another
   pre-outcome signal so estimated `p` represents decision-time belief rather
   than exact tracking or selected outcomes.
3. **Coherent transition model.** Build a state-transition simulator that
   rewrites the plate appearance and subsequent game path after a corrected
   call, including half-inning transitions.
4. **Win-objective validation.** Require monotone, counterfactually coherent
   win values before comparing run and win objectives in late/close states.
5. **Strategic interaction.** Couple both teams' inventories and policies so
   opponent response is modeled rather than canceled by construction.
6. **Prospective holdout.** Freeze a candidate policy and test calibration,
   stability, and value on a future untouched period before translating it for
   players.
7. **Human-factors translation.** Only after those gates pass, test whether a
   small set of memorable rules approximates the validated policy closely
   enough for real-time use.

## Reusable safeguards for future Pascal articles

- Freeze editorial effect and stability thresholds before viewing results.
- Track computational status separately from scientific status.
- Treat oracle access, exact future sequences, and selected populations as
  different estimands, not better versions of the same model.
- Require falsifications to test the claimed source of model gain. If the gain
  survives removal of the supposed signal, reject that interpretation.
- Stop prescriptive translation when plausible assumptions flip actions beyond
  the frozen limit, even if the code and effect size look strong.
- Require counterfactual coherence, not predictive performance alone, for
  decision models.
- Keep failed gates and null results in the main evidence trail.
- Run builds in isolated output directories; tests must not rewrite accepted
  historical fixtures in place.
- Keep large generated artifacts out of Git, but commit generators, hashes,
  concise results, and restore instructions.
- Make “measured, modeled, assumed” a standard editorial labeling system.

These safeguards should become the default starting checklist for the next
Pascal research article rather than being reconstructed after analysis begins.
