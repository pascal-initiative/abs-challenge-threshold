# Reproducible Article Research Workflow

This workflow is the reusable operating plan for Pascal research articles. It
turns an editorial idea into evidence without allowing the desired story to
become the analysis specification.

## Roles and review budget

The orchestrator owns the question, preregistration, data lineage, acceptance
gates, integration, and final interpretation. A specialist may critique one
bounded methodological package. One targeted correction is allowed only when
a named acceptance gate fails. The owner must approve any further iteration.

## Required stages

### 0. Identity and recovery

Assign an immutable article ID, working title, research directory, data window,
and status in `PUBLICATION_REGISTRY.md`. Confirm that source is versioned and an
off-machine, checksum-verified backup exists.

### 1. Charter

Record the question, audience, intended contribution, non-goals, known prior
evidence, terminology, resource ceiling, and scientific stop conditions. A
charter expresses the destination; it does not prescribe the result.

### 2. Preregistration

Before confirmatory modeling, freeze:

- populations and denominators;
- outcome and predictor definitions;
- decision-time information set and leakage blacklist;
- primary estimators and temporal split;
- uncertainty, sensitivity, and falsification tests;
- stop/go gates and minimum meaningful effect;
- required outputs and claim rules.

Record the preregistration SHA-256 in the run manifest. Later changes require a
dated amendment that states whether it was made before or after viewing results.

### 3. Provenance and acquisition

Prefer the accepted locked snapshot. New acquisition requires a source,
license/terms review, expected request and byte counts, caching plan, immutable
receipt, retry bound, and authorization class. Raw data are immutable. Derived
tables are generated, never hand-edited.

### 4. Exploration

Exploration may test feasibility and reveal data defects. It lives in an
explicit `exploratory/` area and cannot silently change confirmatory gates.
Promising exploratory findings must be tested on an untouched period or labeled
exploratory in the article.

### 5. Confirmatory build

Every published number must be generated from code. The build writes a manifest
with code hash, input hashes, environment versions, seeds, row counts, output
hashes, and gate results. Use isolated output directories for determinism tests.

### 6. Validation

Validate population reconciliation, joins, missingness, duplicates, legal
states, temporal ordering, leakage, calibration, sensitivity, effect size,
uncertainty, and byte-for-byte determinism. Include negative controls and a
deliberately leaky canary that the feature gate must reject.

### 7. Interpretation gate

Maintain a claim ledger. Each candidate statement identifies its denominator,
type (measured, modeled, or assumed), artifact, uncertainty, gate, approved
wording, and prohibited overstatement. No playbook is produced until the model
and stability gates pass.

### 8. Draft and publication

The first editorial output is a findings outline, not polished prose. It leads
with supported results, includes counterevidence and limitations, and marks
open editorial decisions. Publication, CMS changes, and social posts remain
owner-controlled external actions.

## Resource defaults

Research begins at R0: local cached inputs, targeted tests, and no hosted
services. Standard pull-request CI is R1 when a remote exists. Hosted previews
or staging are R2 and intentional. Live metered APIs, production data, paid
sources, backfills, and publication are R3 and require owner approval.

Use staged sensitivity testing: run one-factor-at-a-time variants first, then
only the small set of jointly adverse combinations capable of changing a
conclusion. Do not run a combinatorial grid for completeness alone.
