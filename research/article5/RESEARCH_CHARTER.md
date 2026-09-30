# ABS-05 Research Charter — The Challenge Threshold

## Goal

Answer: **When should a player challenge an ABS call?**

Develop a defensible decision-time framework that puts the benefit of correcting
an incorrect call and the future value lost after a failed challenge on a common
expected-run-differential scale. The primary product is the **Challenge
Threshold**: the minimum subjective probability of an overturn required for
CHALLENGE to have greater expected value than HOLD.

The desired result is situational guidance, not absolute rules. Thresholds may
vary with count, outs, runners, inning, score-related game truncation, challenge
inventory, side, and the evidence reasonably available to the player.

## Starting evidence

Reuse the validated ABS-04 population and methodology. Among 20,124 eligible
incorrect calls with determinable counterfactual values, median correction value
was about 0.11 runs and median established decision value—estimated probability
of success times correction value—was about 0.06 runs. Value was concentrated:
the top 10% held about 30% of correctable value, the top 20% held 44%, and full
counts were about 3% of opportunities but 11% of value.

ABS-04 estimated the option value of one retained challenge under league-typical
use at about 0.080 runs at the start of the first and 0.008 by the ninth. These
are policy-dependent benchmarks, not the cost term for a new optimal policy.
Successful challenges retain inventory; only failed challenges consume a unit.

## Required distinctions

- An opportunity is a potentially correctable ball/strike call.
- A challenge is the observed player action.
- A challenge unit is inventory retained after success and lost after failure.
- Correction value is the expected-run change if an incorrect call is fixed.
- Decision value retains its ABS-04 definition: estimated probability of success
  times correction value.
- Option value is the expected future value of retained inventory under a named
  policy.
- Challenge Threshold is reserved for the validated break-even probability.

## Scientific objective

Measure the required confidence, not player intelligence or blame. A failed
challenge can be rational; an unused unit is not proof of a mistake; observed
inventory associations are not causal; realized subsequent runs are not the
value of the decision.

Actively seek evidence that invalidates the framework. Stop before article
conclusions if decision-time probability is poorly identified, option value is
too assumption-sensitive, rules invalidate the formulation, policy results are
not stable, or the available data cannot support situational thresholds.

## Expected research products

- one row per legal called-pitch decision with state, model inputs, hypothetical
  correction value, inventory values, threshold, and explicitly labeled
  measured/modeled/assumed fields;
- representative and extreme scenario tables;
- threshold surfaces with uncertainty;
- simple-policy comparisons;
- staged sensitivity and falsification results;
- a draft findings outline only after validation.
