# Sprint 5 methodology

## Population and state reconstruction

The analysis reads the accepted 2026-03-25 through 2026-09-09 Sprint 3 snapshot. A legal offensive opportunity is a called strike with offensive inventory above zero; a legal defensive opportunity is a called ball with defensive inventory above zero. Position-player-pitching calls are excluded. The universe contains 312,228 pitches. Each PRE_PITCH state is advanced under HOLD and under reversal. Walks advance forced runners, loaded walks score one run, strikeouts add an out, and third-out strikeouts advance the half inning.

## Run expectancy and win probability

RE288 uses 12 counts × 3 out states × 8 base states. Empirical future half-inning runs from immutable MLB feeds are smoothed toward base/out means with a 40-observation prior. `delta_RE` is oriented to the challenging side. Home win probability uses a deterministic histogram-gradient-boosting classifier with inning, half, score differential, outs, bases, and count; final game outcomes are targets only. Expanding monthly validation trains strictly before each test month. Counterfactual WP is converted to the challenging team's perspective.

## Overturn probability and selection

The primary probability model uses only pre-decision geometry, pitch, count, state, side, and inventory. A challenge-propensity model is fit on every legal opportunity; the outcome model is fit on actual challenge results with clipped inverse-propensity weights. This addresses selection on recorded covariates but not private perception. A population geometry model trained on derived physical correctness is retained only as a sensitivity value and never as a predictor in the primary model. Temporal calibration is evaluated only on later actual challenges.

## Sequential policy

Future option value is solved by backward induction over a representative empirical distribution of future challenge-type opportunities. For inventory k, the challenge branch is `p × (gain + V[k]) + (1-p) × V[k-1]`; the hold branch is `V[k]`. The recursion retains inventory after success and loses one after failure. Expected remaining opportunity count declines with inning/half/out state, while future gain scales with current WP leverage. `required_confidence = marginal_resource_value / (delta_WP + marginal_resource_value)`. The preregistered indifference band is ±0.00025 WP and the strong-decision threshold is 0.0025 WP.

## Validation, sensitivity, and benchmarks

Overturn, RE, and WP models use expanding calendar-month tests. The policy is backtested by held-out segment and tested under ±15% overturn calibration, half/1.5× resource cost, a 10% WP-value reduction, and half/double indifference bands. Stability is reported both across all decisions and as Jaccard overlap of the actionable challenge sets; 0.75 actionable overlap is the minimum framework gate and values below 0.90 are labeled sensitive. Benchmarks are immediate value only, a fixed 0.1 percentage-point failure cost, a 60% confidence rule, and a declining 60/50/40% threshold proxy. Public context: [MLB/Savant definitions](https://baseballsavant.mlb.com/leaderboard/abs-challenges?page=0&pageSize=50&sort=n_challenges&sortDir=desc), [Palmer Bellman implementation](https://github.com/professorpalmer/abs-challenge), and [ABScharts methodology](https://abscharts.com/writeup/methodology/).

Hindsight future events appear only in outputs labeled `HINDSIGHT_DESCRIPTIVE` or `HINDSIGHT_POLICY_SIMULATION`; they never alter earlier ex-ante decisions. Player/team rankings remain unsupported.
