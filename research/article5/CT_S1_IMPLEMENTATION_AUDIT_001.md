# CT-S1 Implementation Audit 001: Missing Cutoff Alternatives

## Finding

Before executing CTS3 on confirmation outcomes, the adapter audit compared the
successor code's required core-variant tuple with Amendment 005. The code and
model-schema list omitted the already-approved future-use cutoff alternatives
`0.00` and `0.10`, although the amendment explicitly includes them in CT Model
Spread.

No CT-S1 model, threshold, drift, model spread, or contrast result had been
computed when this mismatch was identified.

## Correction

Add `cutoff_0.00` and `cutoff_0.10` to the required core grid and schema. The
CTS3 adapter must evaluate both using fixed probability `0.60`, constrained
correction values, and the otherwise unchanged reference mechanics.

This is conformance to the merged standard, not a post-result amendment. A
complete-grid assertion and model-spread tests prevent silent omission.
