# ABS-05 Amendment 002 — G8 Objective-Scale Follow-up

**Date:** 2026-09-25
**Timing:** After inspection and acceptance of the original G8 failure
**Authorization:** Owner requested continuation within G8 after merging the
failed stability gate

## What this amendment does not change

The original G8 result is permanent: five available sensitivity/inventory
comparisons exceeded the preregistered 10% flip ceiling. This follow-up cannot
change that failure, redefine the fixed top-value population, select a more
favorable reference, or authorize a playbook. Its only purpose is to investigate
the two mandatory sensitivities previously recorded as unavailable.

## Win-probability sensitivity

Build a deterministic decision-time home win-expectancy model from the locked
2,195-game snapshot. The target is the final home-team win from the immutable
game-feed object. Tied or non-final games are rejected rather than assigned an
outcome.

The model uses only pre-pitch state:

- inning, capped at 10 for extra innings;
- top or bottom half;
- pre-pitch home and away scores; and
- the G5 constrained expected runs remaining in the current half-inning.

Define home state advantage as home score minus away score, plus constrained
remaining-half run expectancy when the home team bats and minus it when the
away team bats. Fit a regularized logistic model with a separate intercept and
nonnegative state-advantage slope for each inning/half phase. Give every game
equal total fitting weight so long games do not dominate. No player identity,
tracking geometry, challenge behavior, challenge outcome, same-game future
state, or realized runs after the decision is a predictor.

Evaluate with expanding monthly rolling-origin folds. Every test date must be
strictly later than every training date. Report overall and late/close Brier
score, log loss, AUC, calibration intercept, calibration slope, and 10-bin ECE,
along with the expanding home-win-rate baseline.

The model is acceptable for a fixed-path sensitivity only if:

1. all 2,195 games have a unique final winner;
2. temporal ordering and the feature allowlist pass;
3. overall Brier score and log loss both improve on the expanding baseline;
4. overall 10-bin ECE is at most 0.03, absolute calibration intercept at most
   0.10, and calibration slope between 0.70 and 1.30;
5. late/close rows have both outcome classes, at least 500 rows, and 10-bin ECE
   at most 0.05; and
6. full-fit counterfactual correction values are finite, fewer than 0.1% are
   negative beyond `1e-9`, and none are negative in the fixed G8 top-value
   population.

For each legal called pitch, value the call-stands and corrected successor
states using canonical no-secondary-runner-action transitions. Explicitly
handle inning changes, game-ending top halves, bottom-half losses, ties entering
extras, and walkoffs. Orient the win-probability change to the entitled team.

If the model passes, substitute these local win-probability changes for run
correction values in the G7 recursion with the fixed 0.60 probability anchor.
This is a **fixed-observed-path additive sensitivity**, not a fully coupled game
simulation. Compare its actions with the already frozen top-value reference for
one and two units. If the model fails, retain diagnostics but keep the mandatory
sensitivity unavailable.

## Opponent-policy sensitivity

Under G7, each team's future opportunity sequence and inventory are independent
and the corrected call does not rewrite the game path. On that restricted model,
the opponent's expected policy value is the same additive term under CHALLENGE
and HOLD, so it cancels from the focal action comparison. Prove this algebraically
in the report and verify it in executable paired-sequence tests for a
league-typical fixed policy and an optimized opponent policy.

Passing this check closes opponent **policy accounting only within the G7
separable model**. It does not model opponent response, strategic interaction,
or changed future states, and it does not resolve `deltaW=0`.

## Outputs and status

Produce rolling predictions, calibration tables, full-fit win-probability
correction diagnostics, top-value action flips if valid, opponent-invariance
tests, validation JSON, a human-readable report, and a deterministic manifest.
Two clean builds must be byte-identical.

The final status must preserve both facts:

- original G8 stability gate: **FAILED**; and
- objective follow-up: pass, fail, or incomplete on its own terms.

No result from this amendment may authorize situational advice or a Pascal ABS
Challenge Playbook.

## Resource ceiling

Resource class remains R0: locked local data and local computation only. No live
API, paid source, hosted database, GitHub Actions, Vercel, Supabase, Odds API,
or additional Claude exchange is authorized.
