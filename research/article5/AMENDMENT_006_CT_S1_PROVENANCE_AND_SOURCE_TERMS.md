# ABS-05 Amendment 006 — CT-S1 Holdout Provenance and Source Terms

## Timing

Date: 2026-09-25

This amendment was written after Amendment 005 merged and before any CT-S1
confirmation acquisition or analysis. It records two issues found while
preparing the required acquisition receipt.

No post–September 10 source object was downloaded, opened, parsed, summarized,
or modeled during this review.

## Provenance correction

Amendment 005 stated too broadly that confirmation data had not been acquired.
The accepted Sprint 3 report already disclosed that September 10 schedule and
game-feed bytes were archived but excluded because the official daily challenge
total was unavailable. The raw receipt index also contains:

- a schedule response covering 2026-03-25 through 2026-09-10, SHA-256
  `e8f600a0c9a2bf6d64d752d746dc2cd25b5866c5f49f6f30aadfc14cfdcf86de`;
- a 1,825-byte September 10 Statcast response, SHA-256
  `c1703bd38919ac5304ed7f1e0f3eb225f385b969203db316cde88adc409462e3`;
  and
- September 10 game-feed bytes identified in the accepted Sprint 3 report.

Those objects were not part of the processed 2026-03-25 through 2026-09-09
analysis tables. This review did not open them or map the game-feed objects to
individual September 10 games.

To remove ambiguity, the CT-S1 untouched confirmation window changes to:

```text
2026-09-11 through 2026-09-27, inclusive
```

September 10 is excluded from both development and confirmation. The official
MLB schedule identifies September 27 as the final day of the 2026 regular
season. If a regular-season makeup is completed after September 27, it is
outside CT-S1 unless a new pre-acquisition amendment changes the end date.

The confirmation claim is now precise: no September 11–27 source data have been
acquired into or analyzed by this repository as of this amendment. It remains
an untouched temporal holdout relative to the repository, not a fully
prospective calendar trial.

## Source-terms review

The intended pipeline uses MLB Stats API game schedules and feeds plus Baseball
Savant Statcast and ABS resources. Baseball Savant publicly documents its CSV
downloads, including the 2026 ABS-aligned location fields. However, the current
MLB.com Terms of Use state that users must not use automated scripts to collect
information from or interact with MLB Digital Properties. The same terms also
limit reproduction and distribution absent permission.

Primary sources reviewed on 2026-09-25:

- MLB.com Terms of Use:
  `https://www.mlb.com/official-information/terms-of-use`
- Baseball Savant Statcast CSV documentation:
  `https://baseballsavant.mlb.com/csv-docs`
- MLB announcement of 2026 game times and September 27 final day:
  `https://www.mlb.com/news/mlb-announces-2026-game-times`

The existence of public endpoints, download controls, prior research use, or
the repository's historical acquisition does not by itself establish permission
for a new automated pull. Manual downloading is not treated as a workaround for
unclear reuse or publication rights.

This is a conservative research-governance determination, not legal advice.

## Owner-directed decision

After reviewing the source-terms warning, the owner explicitly directed Pascal
to continue the existing public-data process and accepted responsibility for
that decision. This instruction is recorded as **owner-directed risk
acceptance**, not as a finding that public availability places the source data
in the public domain or that the terms permit automation.

The source-authorization gate is therefore overridden by the owner for CT-S1
only. The resource, timing, provenance, immutability, and publication safeguards
remain controlling.

The preferred future resolution remains one of the following:

1. written permission or an applicable MLB license covering the intended
   collection and research use;
2. an alternative provider whose terms explicitly permit the required
   automated access, local preservation, analysis, and publication of derived
   results; or
3. a user-supplied dataset accompanied by a documented right to use it for this
   research and derived publication.

The owner-directed exception does not transfer legal judgment to the research
code and is not a reusable authorization for another article, season, source,
or acquisition window.

## Effect on CT-S1

- CT-S1 remains a proposed successor standard.
- The reference definition and validation cutoffs do not change.
- CT-2026 remains failed.
- No numerical Article 5 drafting is authorized.
- Local code design using synthetic fixtures may continue at R0.
- The bounded acquisition may execute only after the September 11–27 window is
  complete, every required source reports completeness, the guarded command is
  reviewed, and all frozen caps remain in force.
