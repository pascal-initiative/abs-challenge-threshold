# CT-S1 Figure Gate Results

Date: 2026-09-28

Decision: **PASS — READY FOR OWNER FIGURE REVIEW**

This gate produced four reproducible publication-figure drafts for the
owner-approved CT-S1 article prose. It did not modify `pascal-site`, deploy an
asset, authorize publication, create a playbook, grade a player, or issue a
challenge recommendation.

## Deliverables

1. **The Three Prices of an ABS Challenge** — a conceptual expected-run
   comparison with pass explicitly defined as the zero baseline.
2. **Same Situation. One Count Changes.** — the one prespecified ordinary
   comparison that met the published display rule, shown without turning it
   into a universal count rule.
3. **One Reference. Two Kinds of Uncertainty.** — conditional sampling
   intervals and CT Model Spread shown as separate objects.
4. **Stable Through Time. Sensitive to Definition.** — temporal stability of
   the frozen reference placed beside, but not netted against, convention
   disagreement.

Each figure has a source CSV, SVG, PNG, caption, alt text, content-class label,
claim IDs, and explicit prohibitions. `manifest.json` records content hashes,
the Python and Matplotlib versions, and the continuing publication
restrictions.

## Review outcome

One bounded Claude visual and accessibility review returned **PASS WITH
CORRECTIONS**. The two blocking presentation risks were corrected: Figure 1
now makes its payoff baseline explicit, and Figures 2 and 3 now state in the
image that the thresholds are neither player confidence nor player rules.
Supported nonblocking corrections improved contrast, direct labeling,
uncertainty separation, denominator clarity, and image/caption/alt-text
agreement. No second reviewer exchange occurred.

The remaining publication-stage requirement is responsive mobile treatment,
especially for the three-card Figure 1 and two-panel Figure 4. That work
belongs to the later site-integration gate and must preserve all protective
text at the final rendered size.

## Reproducibility and validation

The builder validates the content-addressed public-claim sources before
rendering. The focused test builds the package twice and byte-compares every
generated artifact. The complete Article 5 suite passes with the new tests.

Accepted status is limited to **ready for owner figure review**. Site
integration, deployment, public release, a practical playbook, and player
grading remain unauthorized.
