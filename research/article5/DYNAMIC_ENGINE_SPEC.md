# ABS-05 Gate G7 Dynamic-Engine Specification

## Freeze status

This specification is frozen before the G7 implementation is run. G6 did not
identify player confidence, so every probability input below is an explicitly
named assumption or benchmark. No result may be described as an optimal MLB
player policy.

## Decision population and value

The reporting population is every observed legal called pitch with inventory
available: 312,228 decisions. The counterfactual future stream additionally
retains called pitches observed after inventory exhaustion, because a different
policy could still hold inventory at those pitches. Position-player pitching
and other rule-ineligible states remain excluded. Observed inventory therefore
does not censor a counterfactual policy's future opportunity stream.

The team entitled to challenge is the batting team after a called strike and
the fielding team after a called ball. Canonical correction value is the
G5-constrained expected-run change from flipping the call, using the recorded
pre-pitch count, outs, and bases. It excludes position-player pitching and
inventory-zero states from the decision population.

Canonical flip value intentionally holds secondary runner action outside the
engine. Validated G5 incorrect-call values remain the sensitivity source for
runner-action cases; the engine may not invent counterfactual placement.

## Empirical distribution

Build a chronological sequence of all potentially challengeable called-pitch
opportunities for each of the 4,390 team-games. Exact backward recursion is run over every complete
sequence, not a representative or mean opportunity. Averaging sequence results
therefore integrates the observed distribution of opportunity count, timing,
state, value, and game truncation.

This is an empirical-sequence benchmark. Correcting a call does not rewrite the
subsequent observed sequence, so `deltaW` is zero by construction rather than
demonstrated negligible. Thresholds using `C/(V+C)` must carry that label and
cannot replace the full preregistered formula in article guidance.

## Inventory mechanics

- Start with two units.
- Success earns the correction value and retains inventory.
- Failure earns zero and consumes one unit.
- Holding retains inventory.
- On crossing into any extra inning, inventory zero becomes one; positive
  inventory is not incremented.
- Game end terminates future option value.

Compute `W(0)`, `W(1)`, and `W(2)` and report marginal values `C(1)=W(1)-W(0)`
and `C(2)=W(2)-W(1)` separately. Concavity is tested, not assumed.

## Probability scenarios

- fixed confidence 0.50, 0.60, and 0.70;
- exact public-tracking full-fit benchmark;
- challenger-selected full-fit transport assumption.

The two fitted scenarios reuse the fixed G6 feature specification. Full-fit
predictions are simulation inputs, not point-in-time estimates. The
challenger-selected model is explicitly nontransportable under G6 and appears
only to show assumption sensitivity.

## Policies

- never challenge;
- fixed confidence cutoffs 0.50, 0.60, and 0.70;
- challenge when `p * V >= 0.05` runs;
- dynamic sequence policy choosing CHALLENGE when its expected value exceeds
  HOLD given the exact remaining empirical sequence.

At a decision with future marginal inventory cost `C`, the engine records the
simplified sequence threshold `C/(V+C)`. Ties hold.

## Validation and restriction

Gate G7 computational validation requires:

1. tiny synthetic sequences equal brute-force enumeration;
2. Monte Carlo simulation agrees with recursion within four simulation standard
   errors;
3. success retention, failure consumption, extra-inning grant, and truncation
   tests pass;
4. all 312,228 decisions and 4,390 team-games reconcile;
5. values are finite and nonnegative; and
6. two clean builds are byte-identical.

The engine remains scientifically restricted unless a state-transition model
validates nonzero `deltaW` and opponent/game-path responses. Passing the
computational gate permits model-free and assumption-labeled threshold research,
not a playbook.
