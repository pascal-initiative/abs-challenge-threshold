# ABS-05 Validation Plan

All gates are sequential. A downstream pass cannot override an upstream failure.

| Gate | Pass condition | Failure consequence |
| --- | --- | --- |
| G0 Rules | Rules memo covers eligibility, timing, grants, zone, runner plays, and scope. | Stop rule-dependent modeling. |
| G1 Provenance | All accepted input hashes, row counts, and protected-file checks reconcile. | Stop. |
| G2 Population | Every legal called pitch has one key; duplicates, missing states, and exclusions reconcile. | Stop. |
| G3 Leakage | Feature allowlist passes; every blacklisted field is rejected; leaky canary is caught. | Stop probability modeling. |
| G4 Label fidelity | Public geometry agrees with official challenged outcomes at least 99%, with all disagreements audited by boundary distance. | Stop empirical probability mapping. |
| G5 Correction value | Monotonicity holds by construction; replay spot checks pass; ambiguous bounds are retained; estimator sensitivities are reported. | Stop threshold computation. |
| G6 Probability | Rolling-origin calibration is reported overall and by side/role/count/inning; no unsupported subgroup is used. | Publish model-free thresholds only. |
| G7 Dynamic engine | Tiny synthetic cases match brute-force enumeration; independent game simulation agrees within Monte Carlo error; success retains and failure consumes inventory. | Stop policy comparison. |
| G8 Stability | Among the top correction-value decile, recommended action flips on no more than 10% of rows across plausible primary sensitivities; important scenario thresholds do not cross editorial categories without disclosure. | No situational playbook. |
| G9 Effect size | Dynamic policy improves on the best simple non-oracle policy by at least 0.01 expected runs per team-game and its game-clustered 95% interval excludes zero. | Report no demonstrable practical improvement; a threshold framework may still be described. |
| G10 Reproducibility | Two clean builds in separate output directories are byte-identical except explicitly timestamped metadata. | Not ready to draft. |

The G8 and G9 values are preregistered editorial thresholds, not claims about a
universal baseball standard. Report sensitivity to both.

## Falsification and negative controls

- Label shuffling must collapse apparent policy gains.
- A model containing signed distance should achieve suspiciously high
  discrimination and must be blocked by the schema gate.
- Compare early-to-late opportunity distributions for learning or drift.
- Compare player-observed challenge success with matched leakage-free estimates;
  a persistent advantage is evidence that the model omits private information.
- Test whether `C(2) <= C(1)` rather than assuming it.
- Measure `deltaW`; if it is material relative to `V`, prohibit the simplified
  threshold formula.
- Report run-scale versus win-scale disagreement for late, close situations.

## Required human-reviewable outputs

- population and join reconciliation;
- feature timing/allowlist audit;
- correction-value diagnostics;
- probability calibration report;
- marginal inventory-value curves;
- threshold table and stability map;
- scenario table with ordinary and extreme cases;
- policy comparison with uncertainty;
- sensitivity and falsification summary;
- deterministic run manifest and claim ledger.
