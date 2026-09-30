# ABS-05 Preregistration Implementation Amendment 001

**Date:** 2026-09-25  
**Stage:** After the first Gate G5 implementation was run and failed; before the
corrected implementation was run.  
**Scope:** Correction-value implementation only. The estimand, population,
primary objective, downstream gates, and Article 4 counterfactual states do not
change.

## Evidence that required the amendment

The first implementation projected count values independently within each
outs/base stratum. It eliminated all 40 within-stratum count-ordering violations
but left four exact eligible correction values at -0.011925 runs. Each was a
3-0, two-out state with a runner on third: ball four changes the base state, so
the relevant logical constraint crossed strata and was absent.

The run also confirmed that the 40 eligible ambiguous rows comprise 38 rows with
Article 4 runner-placement alternatives and two catcher-interference rows with
no reconstructed corrected state, alternatives, or prior bounds. Finite bounds
cannot be produced for those two rows without inventing a counterfactual.

Claude supplied the one permitted targeted correction review after this named
gate failure. The orchestrator independently accepted the global-projection and
structurally-unvalued recommendations, while expressing terminal comparisons
directly as sibling outcomes from the same pre-pitch state.

## Amendment A: joint terminal-transition constraints

Replace the independent 12-state projections with one weighted least-squares
projection over all 288 count/outs/base states. Retain the `n_pitches + 40`
weights and the original within-stratum count constraints.

For each pre-pitch state, define outcome value as:

`runs scored on the transition + RE(successor state)`.

Add the missing terminal sibling constraints:

- at 3 balls and fewer than 2 strikes, canonical walk value must be at least
  the value after the strike outcome (`RE(3, strikes + 1, outs, bases)`);
- at 2 strikes and fewer than 3 balls, the value after the ball outcome
  (`RE(balls + 1, 2, outs, bases)`) must be at least canonical strikeout value;
- at a full count, canonical walk value must be at least canonical strikeout
  value.

A canonical walk advances only forced runners. One run is added only with the
bases loaded, and future RE begins at 0-0 in the forced successor base state.
A canonical strikeout preserves bases and begins at 0-0 with one additional out;
with two outs its future value is zero. Runs scored on a transition are constants
and are never included again in successor RE.

These constraints define estimator coherence. They do not overwrite or
reclassify any Article 4 replay state.

## Amendment B: structurally unvalued ambiguity

Replace the implementation requirement that all 40 eligible ambiguous rows
have finite bounds with this reconciliation:

- all 38 rows having Article 4 reconstructed alternative states must retain
  finite, ordered constrained-value bounds across every alternative;
- the two `R5_UNSUPPORTED_MOVEMENT` catcher-interference rows remain in the row
  ledger as `AMBIGUOUS_STRUCTURALLY_UNVALUED`, with their reason codes and null
  point/bound values;
- those two rows are excluded only from valued summaries, not from population
  accounting or eligibility.

Gate G5 stops if the counts are not exactly 40 = 38 bounded + 2 structurally
unvalued, if the global program is infeasible, if any exact eligible correction
value remains below tolerance, or if an accepted Article 4 input hash changes.
