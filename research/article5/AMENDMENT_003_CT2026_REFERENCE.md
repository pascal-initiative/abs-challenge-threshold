# ABS-05 Amendment 003 — CT-2026 Reference Evaluator

## Timing and authority

Date: 2026-09-25

This is a post-G10, pre-CT-2026-implementation amendment. G5 through G10
results, including the G8 stability failure and G9 exact-future falsification,
were known. No CT-2026 distributional reference values had been computed or
inspected when this amendment and its specifications were frozen.

The owner clarified the intended public product during editorial review:
Challenge Threshold should operate like a versioned baseball evaluator. It
prices the confidence required by the situation “in a vacuum”; player
confidence, ability, and behavior remain external inputs rather than quantities
the metric must estimate.

## Reason for amendment

The frozen preregistration already states:

> The threshold itself is primary and model-free. Mapping evidence to `p` is a
> separate secondary layer.

It also states that failure to identify player probability does not invalidate
model-free threshold tables. The first editorial review over-weighted the G6
perception limitation and under-weighted this distinction.

At the same time, G9 showed that the G7 exact-sequence benchmark can benefit
from privileged future allocation even after correctness labels are shuffled.
Publishing an average of those exact-sequence marginal costs as the CT reference
would preserve part of the wrong information advantage.

The amendment therefore authorizes a new downstream reference evaluator while
retaining all original failed gates and prohibited interpretations.

## Changes authorized

1. Define **CT-2026** as a versioned, expected-run reference evaluator reporting
   the break-even confidence required under named assumptions.
2. Use fixed `p=0.60` as the standard convention for pricing future inventory.
   This was the G8 reference anchor frozen before stability results; choosing it
   here does not depend on which value is most attractive.
3. Replace exact-future action selection with non-clairvoyant, state-based fitted
   policy iteration over the empirical distribution of complete team-game
   sequences.
4. Treat G7 exact-sequence values as mechanics validation and a
   privileged-information upper diagnostic only.
5. Publish one CT-2026 reference value plus a separate approved model range and
   sampling interval where validation permits.
6. Version and archive the September 9 snapshot; do not silently replace it
   with a later full-season estimate.
7. Add sequential gates CT1 through CT10. Numerical CT values cannot enter
   article prose before those gates pass.

## Relationship to the original preregistration

The original preregistration named league-typical opponent policy as primary
and optimized opponent policy as a sensitivity. CT-2026's fixed-0.60 convention
is a new publication reference standard, not a relabeling of that original
primary analysis. League-typical Article 4 values and exact-sequence G7 values
remain separately labeled diagnostic comparisons. Strategic opponent response
remains unmodeled and CT-2026 may not claim to optimize a coupled game.

The simplified formula retains `deltaW=0` by construction. CT-2026 must carry
that restriction and may not be described as demonstrating `deltaW` negligible.
The rejected win-probability model is not revived.

## Conclusions potentially affected

This amendment can support:

- a CT-2026 reference table over validated states;
- neutral low/middle/high comparisons of required confidence;
- representative state examples selected mechanically; and
- the claim that Challenge Threshold is a standardized situation evaluator.

It cannot support:

- a player's estimated confidence;
- evidence-to-action advice;
- judgment of an observed challenge or pass;
- an optimal MLB policy;
- a win-probability threshold;
- a coupled opponent strategy; or
- the Pascal ABS Challenge Playbook.

## Required artifacts

- `CT2026_SPEC.md` and its frozen hash;
- `CT2026_VALIDATION_PLAN.md`;
- implementation, focused tests, and deterministic manifests;
- the CT1-CT10 validation packet; and
- an updated claim ledger and publication registry.

## Resources

Resource class remains R0. Use only the locked local snapshot and local
computation. No new data, live APIs, paid source, hosted system, GitHub Actions,
Vercel, Supabase, Odds API, or additional Claude exchange is authorized.

