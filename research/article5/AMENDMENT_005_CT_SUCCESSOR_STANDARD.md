# ABS-05 Amendment 005 — Challenge Threshold Successor Standard

## Timing and status

Date: 2026-09-25

This amendment was written **after** the CT-2026 fixed-policy build and its CT6
sensitivity failure were inspected. The known results include the 97.0523%
material-range share and the one-factor sensitivity decomposition recorded in
`CT2026_FIXED_POLICY_RESULTS.md`.

This amendment cannot change, reinterpret, or rescue the CT-2026 result.
CT-2026 remains failed and its numerical table remains prohibited from public
use. This document defines a prospective successor research program. Amendment
006 later identified pre-existing September 10 raw bytes and corrected the
untouched confirmation window to September 11–27; no data from that corrected
window had been acquired or inspected in this repository when Amendment 006 was
written.

The immutable research identity is **CT-S1**. If all successor gates pass, the
candidate public version name is **Challenge Threshold Standard 1**. It must
not be labeled CT-2026 or presented as the result of the failed CT-2026 build.

## Why a successor is scientifically defensible

The CT-2026 failure established that plausible modeling conventions do not
collapse to one assumption-insensitive number. It did not invalidate the
conditional break-even identity:

```text
Challenge Threshold = C / (V + C)
```

where `V` is immediate correction value and `C` is the future inventory value
under a declared policy and objective.

Many accepted baseball metrics are standards rather than natural constants.
Their meaning comes from a stable definition, named implementation, versioned
inputs, and reproducibility. Alternative WAR systems need not agree for each
system to remain interpretable. The same principle can apply to Challenge
Threshold, but only if Pascal stops implying that disagreement among approved
models is ordinary sampling noise.

The successor therefore separates two questions:

1. **Is the named reference implementation stable and reproducible on new
   data?**
2. **How much do other defensible implementations disagree with it?**

The first is a validation question. The second is a required disclosure, not a
test that every model must produce nearly the same number.

## Product definition

The public object, if validation succeeds, is a three-part record rather than
an unlabeled point estimate:

### CT Reference

The required-confidence percentage produced by one frozen, named
implementation. The successor candidate retains the convention selected before
CT-2026 sensitivity results were viewed:

```text
future probability convention = 0.60
future challenge-use rule      = p * V >= 0.05 expected runs
correction-value estimator     = constrained partially pooled count-aware RE
objective                      = expected runs for the challenging team
```

The convention is a standardization choice, not an estimate of player belief
and not a claim that this future-use policy is optimal.

### CT Model Spread

The minimum and maximum threshold across the complete frozen alternative set.
It measures implementation disagreement. It must be displayed beside the
reference whenever the spread is material and must never be described as a
sampling confidence interval.

The alternative set remains:

- future probability conventions 0.50 and 0.70;
- future expected-value cutoffs 0.00 and 0.10 runs;
- approved correction-value estimators;
- extra-inning restoration off; and
- bounded ambiguous-case treatments when applicable.

Public-tracking and selected-transport probabilities remain diagnostics and do
not define the model-spread endpoints.

### CT Sampling Interval

A game-clustered interval around the reference implementation, produced with a
frozen seed. It measures finite-sample uncertainty while holding the reference
definition fixed. It must be visually and verbally distinct from CT Model
Spread.

## Interpretation contract

The durable statement remains:

> **Challenge Threshold tells you how sure you need to be under a named value
> model. It does not tell you how sure you are.**

If confirmed, the metric may support:

- comparing the price of ABS decisions on a common required-confidence scale;
- describing how a named reference model evaluates supported situations;
- showing how much modeling choices move that evaluation;
- annual or rule-version recalculation; and
- broadcast, coaching, journalistic, and fan discussion that preserves the
  distinction between situation value and private belief.

It may not support:

- claims that the reference number is uniquely correct;
- grading a player's challenge or pass without defensible decision-time belief;
- describing a failed challenge as a bad decision;
- an automated or empirical Pascal playbook;
- color bands labeled challenge/preserve;
- claims of optimal team strategy; or
- hiding material model spread behind the reference value.

## Development and confirmation split

The locked 2026-03-25 through 2026-09-09 snapshot is now a **development
dataset** for the successor standard. All prior CT results from it are known and
may be used to design presentation, diagnostics, and code tests. It cannot
confirm the successor.

The intended untouched confirmation window, as corrected by Amendment 006, is:

```text
2026-09-11 through 2026-09-27 under materially unchanged MLB ABS challenge
rules
```

No data from that corrected window may be acquired, summarized, or inspected
until the source-authorization gate in Amendment 006 is resolved and the owner
separately approves the final executable receipt. If the rules or source schema
changed materially, stop and version a different study rather than combining
regimes.

This is an untouched temporal holdout relative to the repository's locked
analysis snapshot. It is not described as a fully prospective trial because
some games occurred before this amendment was written.

## Confirmation estimands

The successor confirmation asks whether the frozen reference implementation is
transportable enough to function as a versioned standard.

For state rows supported in both development and confirmation periods, compare:

- reference CT level;
- rank ordering across states;
- inventory-cost schedule;
- sampling uncertainty;
- coverage under the frozen backoff hierarchy; and
- direction of mechanically selected state contrasts.

The model-spread distribution is reported in full. Wide spread does not by
itself fail the successor, because the successor explicitly defines that spread
as part of the public metric. It does prohibit compact presentation that omits
the alternatives and may suppress individual scenarios under the rules in the
validation plan.

## Safeguard against post-result rescue

This successor changes the estimand and public product after observing CT-2026.
Accordingly:

- it receives a new version identity and cannot be called a successful
  CT-2026 build;
- no CT-2026 numerical row can be relabeled as a successor confirmation result;
- confirmation thresholds are frozen before acquisition;
- the existing reference code must be applied without tuning to confirmation
  outcomes;
- any correction after acquisition requires a dated amendment and a preserved
  failure record; and
- a failed confirmation ends numerical Article 5 development for this data
  cycle unless the owner explicitly authorizes a new research program.

## Article consequences

Before confirmation, Article 5 may be drafted only as a framework-and-research
article. It may explain the equation, the distinction between threshold and
belief, why CT-2026 failed, and why standardized metrics require versions. It
may not publish scenario-level CT numbers.

If every required successor gate passes, a later claim review may authorize a
versioned reference evaluator with visible model spread. Passing does not
authorize a playbook or player-decision grading.

## Resource authorization

This amendment authorizes R0 planning, code review, and local tests only. It
does not authorize data acquisition.

Before any confirmation pull, produce a bounded acquisition receipt stating:

- source and terms;
- exact date window;
- expected request count and byte ceiling;
- cache and retry policy;
- immutable raw-data destination and hashes;
- Google Drive backup procedure; and
- confirmation that GitHub Actions, Vercel, Supabase, and Odds API are not
  involved unless separately approved.

The owner must approve that receipt before execution.
