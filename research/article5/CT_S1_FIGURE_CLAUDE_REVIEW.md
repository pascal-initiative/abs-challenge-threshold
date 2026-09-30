# CT-S1 Figure Claude Review

Date: 2026-09-28

Reviewer: Claude Opus 5.5, Medium

Review exchanges: 1

Decision: **PASS WITH CORRECTIONS**

## Scope

Claude received exactly five attachments: the four rendered PNG drafts and
`figures/FIGURE_REVIEW.md`. The prompt limited the response to visual,
accessibility, caption, alt-text, and interpretive review. It prohibited web
search, new analysis, article rewriting, file edits, new facts, a playbook,
player grades, universal count rules, and challenge/preserve commands.

Claude returned one response. No follow-up or correction exchange occurred.

## Blocking findings

1. Figure 1 could be read as double-counting `V`. The displayed equation uses
   pass as the zero baseline, but the third card made the opportunity cost of
   passing look like another payoff term.
2. Figures 2 and 3 used a “required confidence” axis without an in-image
   warning that the values are neither observed player confidence nor a
   player-facing rule. Detached from their captions, the figures could be
   misread as challenge instructions.

## Corrections accepted and implemented

- Figure 1 now states that pass is the zero baseline and that the pass card
  restates the same `V` as an opportunity cost rather than adding a payoff.
- Figure 1 names the formula `CT-S1 Challenge Threshold` and defines `V` and
  `C`; the unexplained `Delta W` notation was removed.
- Figures 2 and 3 now say in the image that CT-S1 is a reference evaluator,
  not player confidence or a player rule. Their axis label repeats the
  distinction.
- Figure 2 removes the connector that could resemble an interval, directly
  labels development and confirmation values, replaces undefined “qualified”
  wording, and identifies the fixed game-state values.
- Figure 3 vertically separates the conditional sampling interval from CT
  Model Spread, uses flat range caps, labels interval endpoints, describes
  the marks by shape as well as color, and warns that interval overlap is not
  a paired test. It also cross-references the separately validated directional
  result in Figure 2.
- Figure 4 removes the unexplained high-precision rank correlation, labels
  drift as absolute and development-to-confirmation, defines material spread
  in the panel title, replaces unexplained shade changes with one color per
  panel, removes “temporal transport” jargon, uses dark text on gold bars, and
  adds a visible panel divider.
- Gold text was darkened while the gold graphic mark was retained, improving
  text contrast without making meaning color-dependent.
- Alt text and captions were reconciled with the revised images and now carry
  the same baseline, non-rule, uncertainty, direction, and denominator
  disclosures.

## Deferred to site integration

Claude recommended stacked mobile presentations for Figures 1 and 4. This
research-only gate does not edit or deploy the site. The publication gate must
provide responsive image treatment or stacked responsive variants and verify
the protective labels at the final rendered mobile width. This is a required
site-integration check, not authorization to publish.

## Findings not adopted verbatim

- The draft's white text on Figure 4 was replaced with dark text rather than
  retaining white and changing the bar shade.
- Figure 3's interval legend remains, but its wording now describes mark shape
  and its marks are spatially separated. This preserves the two distinct
  uncertainty objects without introducing another claim.
- No second Claude response was requested; the repository's executable and
  visual checks remain the acceptance authority.

## Strongest risk identified by Claude

Readers may interpret the prominent 60% and 67% values as a player-facing
two-strike challenge rule if the non-confidence and non-rule disclosures are
lost, especially at small display sizes.

## Resource accounting

- External reviewer: one Claude Cowork task
- Model setting: Opus 5.5, Medium
- Uploaded material: four PNG files and one Markdown review brief
- Web, API, Vercel, Supabase, Odds API, and GitHub Actions use: none
- Follow-up Claude exchanges: none
