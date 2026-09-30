# Sprint 3 requirements snapshot

Sprint 3 follows the attached “Full-Season Offensive Recognition Study” direction supplied on 2026-09-10. The execution scope is the 2026 MLB regular season through 2026-09-09, the latest date complete across the schedule, game-feed, Statcast, team-level ABS, and official dashboard sources at execution. The primary outcome is whether a batter challenges an incorrect called strike while a legal challenge is available. Sprint 1 and Sprint 2 artifacts are immutable.

The implementation retains the validated Sprint 1 geometry and classification method, requires at least 99% agreement with official ABS outcomes, uses expanding-window temporal validation as primary, reports fixed A→B→C→D model comparisons, gates identity publication on held-out contribution and preregistered support, preserves resource-constrained and defensive populations, and produces the required data, artifacts, figures, documentation, manifest, notebook, and tests.
