# CT-S1 Uncertainty and Reproducibility Specification

## Freeze status

This specification freezes CTS9 and CTS10 before confirmation acquisition. It
does not declare either gate passed. The actual gates require confirmation
artifacts produced after CTS1--CTS8 succeed.

## CTS9: conditional sampling uncertainty

The reference sampling interval uses a deterministic game-clustered percentile
bootstrap with:

- games as the resampling unit;
- seed `20260926`;
- 2,000 replicates;
- the 2.5th and 97.5th percentiles; and
- the named reference implementation held fixed.

Within each replicate, sample the period's games with replacement, retaining
all eligible opportunity rows from each sampled game. Recompute the mean
marginal continuation cost for each supported state and inventory level. Map
the two cost quantiles to CT through the frozen reference correction value.
Because `C / (V + C)` is monotone in nonnegative `C`, the transformed endpoints
retain their order.

The procedure does not refit the probability convention, correction-value
estimator, state hierarchy, future-use action rule, or alternative-model grid.
It is a conditional finite-game-sample interval for the named implementation,
not a comprehensive uncertainty interval.

Every published interval must contain all 2,000 finite replicates. A state with
any nonfinite replicate receives no sampling interval. Sampling columns use
the `sampling_` prefix and remain separate from `model_spread_` columns in data,
figures, and prose.

## CTS10: paired isolated builds

Run the complete accepted confirmation build twice from separate empty output
directories and separate derived caches. Both runs use the same executable,
frozen inputs, hashes, seed, and configuration. Neither run may write to an
accepted input or the other's output directory.

Before run A, hash every protected source, raw receipt, raw object, processed
input, preregistration, amendment, specification, and accepted development
artifact. Hash the same inventory after run B and fail immediately on any
difference.

Compare the two output trees with no exclusions. Relative file sets, byte
sizes, and SHA-256 values must match for every CSV, JSON, Markdown, manifest,
and other generated file. Wall-clock metadata keys such as `generated_at`,
`run_at`, and `timestamp` are prohibited from generated JSON. Record versioned
source dates as scientific data fields, not runtime timestamps.

CTS10 also requires the focused Article 5 tests and every prior successor gate
status to reproduce. A preserved scientific failure is deterministic evidence;
it must not be converted into a build success by omission.

## Required validation artifacts

After confirmation, the build must emit:

- a per-state CTS9 interval table and completeness audit;
- protected-input hashes before and after both builds;
- commands and exit statuses for both builds;
- one comparison row for every generated file;
- runtime-metadata audit;
- focused-test results;
- gate-level JSON and human-readable reports; and
- a final decision memo that distinguishes computational reproducibility from
  scientific acceptance.

## Resource boundary

The assurance build is R0 after the separately authorized, bounded acquisition
is cached. It uses local CPU and immutable local inputs only. It makes zero
GitHub Actions, Vercel, Supabase, Odds API, hosted-database, or publication
calls. Claude's later bounded independent review is not a substitute for CTS9
or CTS10 executable evidence.
