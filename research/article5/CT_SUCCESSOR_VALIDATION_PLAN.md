# Challenge Threshold Successor Validation Plan

## Purpose

This plan governs the prospective successor described in
`AMENDMENT_005_CT_SUCCESSOR_STANDARD.md`, with the provenance and source-terms
correction in `AMENDMENT_006_CT_S1_PROVENANCE_AND_SOURCE_TERMS.md`. It does not reopen CT-2026. The plan
tests whether one named reference implementation is stable enough on untouched
later data to serve as a transparent industry evaluator accompanied by model
spread and sampling uncertainty.

## Required gates

| Gate | Requirement | Failure consequence |
| --- | --- | --- |
| CTS0 review | Amendment, validation plan, version identity, and acquisition boundary are merged before confirmation data are touched. | Do not acquire data. |
| CTS1 acquisition | Owner-directed source-terms risk decision and bounded receipt are recorded; immutable cached raw files, hashes, caps, and request accounting reconcile. | Do not run, or stop and quarantine the pull. |
| CTS2 rules and population | ABS rules and source schema are materially compatible; legal-decision reconstruction reconciles to official records under the frozen rules. | Do not combine periods. |
| CTS3 frozen implementation | Confirmation uses the reviewed reference code and conventions with no outcome-driven tuning; protected development artifacts remain unchanged. | Stop confirmation. |
| CTS4 information timing | No future, outcome, correctness, challenge-result, or exact-sequence field enters reference action selection or a published state key. | Stop publication. |
| CTS5 support | At least 90% of candidate confirmation rows resolve under the frozen hierarchy; development schedules retain 200-row/100-game minimums and confirmation schedules require 50 rows/25 games. Comparisons are harmonized to the coarser supported level. | Suppress failing rows; stop if coverage is below 90%. |
| CTS6 temporal stability | On matched supported rows, median absolute reference-CT drift is at most 0.05, the 90th percentile is at most 0.10, and Spearman rank correlation is at least 0.80. | No numerical successor evaluator. |
| CTS7 contrast stability | Every representative contrast proposed for prose preserves direction in development, confirmation, and every core implementation; minimum absolute separation is at least 0.05 in both periods. | Drop the contrast; stop article examples if no ordinary contrast survives. |
| CTS8 model disclosure | Every core alternative is present; spread is kept separate from sampling intervals; rows with spread above 0.10 are flagged and never shown as an unlabeled point. | Stop publication. |
| CTS9 uncertainty | Game-clustered reference intervals use the frozen seed, reach the declared replicate count, and remain separate from model spread. | Publish no intervals. |
| CTS10 reproducibility | Two isolated confirmation builds are byte-identical and focused tests pass without modifying protected inputs. | Stop publication. |
| CTS11 claim review | Every public number maps to an artifact; wording follows the interpretation contract; no playbook, optimal-policy, or player-grading claim appears. | Return to editorial review. |

CTS9 and CTS10 use the seed, replicate count, interval construction, protected
input inventory, and zero-exclusion byte comparison frozen in
`CT_S1_ASSURANCE_SPEC.md` before confirmation acquisition.

## Why CTS6 differs from CT6

CT6 asked whether plausible implementations agreed within 0.10 for nearly all
states. That question failed and remains failed.

The successor is explicitly a named standard plus disclosed implementation
spread. CTS6 therefore asks a different, prospective question: whether the
unchanged named standard transports across time. CTS8 ensures that alternative
implementations remain visible. Neither gate allows model disagreement to be
misrepresented as statistical precision.

## Frozen temporal-stability calculation

Build development and confirmation schedules separately. The development
hierarchy retains the existing minimum of 200 rows and 100 distinct games. The
shorter confirmation window uses a predeclared minimum of 50 rows and 25
distinct games. Outs and inventory are never dropped.

For comparison, map both estimates to the coarser of the two supported
hierarchy levels. Record both original levels and the harmonized level. Do not
borrow confirmation outcomes into the development estimate or select a finer
level because its result is favorable.

Create one row per matched harmonized state and inventory level. Do not weight
states by how favorable their result is.

```text
absolute drift = abs(CT_confirmation - CT_development)
```

Report the median, 90th percentile, maximum, and Spearman rank correlation.
CTS6 passes only if all three frozen conditions pass:

```text
median absolute drift <= 0.05
90th percentile absolute drift <= 0.10
Spearman correlation >= 0.80
```

Ties use average ranks. Rows undefined in either period are excluded from the
matched calculation but counted in support and exclusion reporting. Inventory
levels are evaluated separately and jointly; the joint gate is controlling.

These cutoffs were selected before confirmation acquisition. They are
publication-readiness conventions, not universal scientific constants.

## Frozen representative-contrast selection

Candidate contrasts are generated mechanically from supported rows:

- same call/count/outs/bases/half/score/role/inventory, early versus late;
- same state, one versus two units;
- same non-count state, ordinary count versus terminal count; and
- ordinary bases-empty/no-out examples nearest the reference median.

No contrast may be selected because its confirmation result is attractive. A
contrast is article-eligible only if its direction is the same in development,
confirmation, and every core implementation and its absolute reference
separation is at least 0.05 in both periods. Failure may reduce the example set;
it may not be repaired by manual substitution outside the frozen rules.

## Model spread and row labels

Every eligible row contains:

- successor version;
- reference CT;
- CT Model Spread low, high, and width;
- reference sampling interval;
- support level, rows, and games;
- development-to-confirmation drift;
- objective and run-expectancy estimator;
- reference future-use convention; and
- permitted-use label.

Rows with model-spread width greater than 0.10 receive
`MATERIAL_MODEL_DISAGREEMENT`. This is disclosure, not suppression by itself.
Rows with an undefined required alternative receive
`INCOMPLETE_MODEL_SPREAD` and cannot appear as a compact public point estimate.

## Required falsifications and canaries

- A deliberately blacklisted future/correctness field must fail the feature
  gate.
- Changing later opportunities may change evaluated continuation value but may
  not change the current fixed-policy action.
- Exact-future dynamic values must remain labeled privileged upper diagnostics
  and must not enter the reference table.
- Random row ordering within a team-game must be rejected rather than silently
  evaluated.
- A protected-input mutation canary must cause the build to fail.
- A presentation test must fail any row that displays a material reference CT
  without its model-spread label.

## Required outputs

- confirmation acquisition receipt and immutable hash manifest;
- population and rules reconciliation;
- matched-state temporal-stability table;
- reference table with model-spread and sampling fields;
- representative-contrast audit;
- excluded/suppressed-row audit;
- gate-level `VALIDATION.json` and human-readable report;
- two-build reproducibility record;
- updated claim ledger and publication registry; and
- a concise decision memo stating whether numerical drafting may begin.

Large generated artifacts remain ignored. Commit generators, tests, schemas,
hashes, and human-reviewable summaries.

## Stopping rules

Stop before numerical article drafting if:

- any CTS0-CTS6 or CTS8 gate fails;
- no ordinary representative contrast passes CTS7;
- the metric cannot be described without implying player belief;
- the confirmation period contains materially different ABS rules that cannot
  be separately versioned;
- a correction requires inspecting and retuning against confirmation outcomes;
  or
- paired builds are not byte-identical.

Do not respond to failure by changing drift cutoffs, omitting difficult states,
removing required alternatives, or reclassifying the confirmation period as
development without a new owner-approved research program.

## Resource ceiling

Planning remains R0. Confirmation acquisition is R3. Amendment 006 records the
owner-directed source-terms risk decision; execution remains date-gated and
bounded by the reviewed receipt. The acquisition uses local caching and zero
GitHub Actions, Vercel, Supabase, and Odds API calls. Analysis after acquisition
returns to R0 unless separately approved.
