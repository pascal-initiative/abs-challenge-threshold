# Sprint 3 methodology

## Acquisition and source hierarchy

The acquisition archived content-addressed MLB schedules, final game feeds, daily Statcast CSVs, 30 team-level ABS extracts, the ABS dashboard, and documentation. The cutoff is 2026-09-09, the latest date complete in every required source. Dedicated ABS records define challenges; dashboard totals audit completeness; feeds provide pitch sequences, participants, and pre-pitch state; Statcast provides measurements. Receipts record URLs, timestamps, bytes, and SHA-256 hashes.

## Validation and population

The Sprint 1 geometry, physical-pitch sequence join, matching, and sequential inventory were reused. All 9,485 challenges matched and 9,482 agreed (99.968%). Classification fails closed below 99%, on incomplete totals, material conflicts, duplicate keys, or inventory failures. An opportunity is an original STRIKE, derived ABS BALL, and legal pre-pitch offensive challenge. `recognized=1` means the batter challenged; outcome is unused. Exhaustion, position-player pitching, and unknowns remain separate.

## Models and validation

Model A contains geometry. Model B adds pitch family, speed, movement, spin, extension, release position, and handedness. Model C adds inning, offense score differential, count, outs, base state, and challenges remaining. D adds regularized identity indicators. Numeric pitch-shape gaps use training-fold medians; categorical gaps use training-fold modes. Geometry and situation fields may not be missing.

Primary evaluation uses expanding monthly windows with `max(training_date) < min(test_date)` and intact games. Metrics are ROC AUC, PR AUC, log loss, Brier score, calibration intercept/slope, and 10-bin ECE. Five-fold group-by-game CV is secondary. Seed=20260325; L2 C=1 is fixed.

## Identity, replication, and sensitivity

Identity contribution requires delta log loss <= -0.001, delta Brier <= -0.0005, and at least 10 entities with 30+ opportunities. Publication requires 20+; ranking requires 30+. Outcomes are shrunk toward Model C expected rates with prior weight 20; approximate 95% intervals use adjusted-binomial standard errors. Boundary replication requires a positive directional estimate and temporal usability. Added blocks require delta log loss <= -0.001 and delta AUC >= 0.002. Sensitivities fix C at 0.25, 1, and 4 and shift the initial temporal boundary.

## Limits

Only supported identity classes receive conditional tables/figures. Results are observational, repeated observations remain dependent, intervals are approximate, source data may be revised, and omitted variables may explain associations. No estimate is interpreted as causal, optimal, deceptive, or an accuracy metric.
