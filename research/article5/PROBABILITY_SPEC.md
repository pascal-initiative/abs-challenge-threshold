# ABS-05 Gate G6 Probability Specification

## Freeze status and prior visibility

This implementation specification is frozen before the Article 5 G6 build.
Article 4 benchmark results were already visible: the selected-challenge model
had modest discrimination but good aggregate calibration, and the all-pitch
public-geometry benchmark had strong discrimination and calibration. Therefore
G6 does not use a new model-selection contest or claim that its numerical
criteria were chosen blind to all prior evidence.

## Scientific question

The Challenge Threshold is model-free. G6 asks whether observable data can map
evidence available at the decision into a calibrated probability that a
challenge succeeds. The player's actual visual, proprioceptive, conversational,
and role-specific evidence is not observed. G6 must not disguise a benchmark as
that latent probability.

## Populations and targets

### Public-tracking benchmark

- Population: every legal called pitch in the locked snapshot with valid public
  tracking geometry, not conditioned on correctness or challenge action.
- Target: reconstructed call incorrect (`original_call != derived_abs_call`).
- Interpretation: probability of incorrectness given exact public tracking
  proximity and coarse context. This is not a player-perception model because
  exact unsigned boundary distance is not directly observed by the player.

### Challenger-selected benchmark

- Population: all 9,485 official challenges.
- Target: official outcome `OVERTURNED`.
- Interpretation: success among players who chose to challenge. It includes
  private selection information and cannot identify success for unchallenged
  decisions without an untestable transport assumption.

Article 3's temporal model is audited but not reused as `P(success)`: its target
is challenge recognition conditional on a known incorrect offensive call, not
incorrectness or overturn probability among all decisions. Defense receives no
player-perception model.

## Features

Both benchmarks use the fixed Article 4 S2 specification:

- unsigned distance to the reconstructed ABS boundary, clipped at 6 inches;
- offense/defense side implied by the call as made;
- nearest boundary edge, defined symmetrically inside and outside the zone;
- whether ball four or strike three is at stake.

No identity, inventory, challenge history, score, future outcome, signed
distance, raw coordinates, ABS result, correctness, or challenge action enters
the model. Exact unsigned distance is allowed only in artifacts labeled
`PUBLIC_TRACKING_BENCHMARK` or `CHALLENGER_SELECTED_BENCHMARK`; it is not added
to the player-information allowlist.

The code must reject a deliberately leaky canary containing signed distance.

## Evaluation

Use expanding monthly rolling-origin folds. For each test month, train only on
strictly earlier dates. March initializes the first fold and receives no
point-in-time prediction. No full-season or leave-one-month-out prediction can
support a point-in-time claim.

Report Brier score, log loss, ROC AUC, calibration intercept, calibration slope,
10-bin expected calibration error, and an expanding-window base-rate benchmark.
Also report calibration by:

- offense/defense side;
- challenger role for the selected benchmark;
- all 12 counts; and
- innings 1-3, 4-6, 7-9, and 10+.

A subgroup is supported for calibration interpretation only when it has at
least 500 observations, 100 positive outcomes, and 100 negative outcomes.
Unsupported groups remain in the artifact and cannot support guidance.

The predeclared aggregate benchmark calibration alerts are absolute intercept
above 0.10, slope outside 0.70-1.30, or ECE above 0.03. Subgroup alerts use ECE
above 0.05. Alerts do not convert a benchmark into a player model.

## Identification decision

G6 has separate outcomes:

1. **Build validity:** populations reconcile, folds are temporal, the feature
   gate and canary work, required calibration tables exist, and outputs are
   deterministic.
2. **Benchmark calibration:** each benchmark either passes or triggers its
   declared alerts.
3. **Player-probability identification:** passes only if the observed features
   represent player evidence and selection can be transported to all legal
   decisions. The current data do not observe either condition, so a benchmark
   calibration pass alone is insufficient.

If player probability is not identified, record G6 as scientifically
restricted and prohibit empirical evidence-to-action guidance. Model-free
threshold tables may continue. Later policy simulations may use named
benchmark or assumed probabilities only as sensitivities, never as estimates of
what a player knew.
