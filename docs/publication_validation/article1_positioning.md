# Article 1 Positioning Memo

## What the article is

Article 1 is a season-scale empirical audit of what happens after the reconstructed zone identifies an estimated incorrect called strike and the batter has a legal challenge available. It introduces a reproducible research program built from an independently reconstructed, frozen 2026 snapshot, official-decision validation, a fully reconciled funnel, temporal prediction, and a separate adversarial publication review.

**Central research question:** When an estimated incorrect called strike occurs and the batter can challenge, what happens next?

**Recommended core positioning:** Pascal Institute independently reconstructed and validated a fixed 2026 MLB ABS dataset, followed the full path from estimated umpire error to player challenge behavior, tested which observable factors improved future prediction of that behavior, and separately challenged the resulting publication claims.

## What the article is not

It is not the first study of unchallenged errors, a claim that most players failed to see a mistake, a causal explanation of why any player challenged, or an evaluation of whether players used challenges well. It does not present reconstructed unchallenged pitches as official ABS decisions.

## Existing work we are building on

Baseball Savant publishes challenge and expected-challenge metrics. MLB and FanGraphs have examined challenge frequency, challengeable pitches, miss magnitude, situation, and value. SABR research, ABS Charts, TapToChallenge, and public open-source projects have studied dynamic inventory and sequential strategy. Pascal should cite this work as the foundation and comparison set.

## Pascal's specific contribution

The contribution is the combination of an independent reconstruction; a fixed 645,793-pitch season-to-date snapshot; validation against 9,485 official decisions; an explicit funnel from all pitches to challenged and unchallenged estimated errors; separate definitions for recognition, challenge rate, success, and correction; expanding temporal tests of geometry, pitch, situation, and batter effects; and an adversarial validation layer that freezes claims and numbers before drafting.

## Strongest headline finding

Batters challenged 2,112 of 10,755 legally challengeable estimated incorrect called strikes, or 19.64%—about one in five. This is a reconstructed-error statistic, not an official ruling on every pitch.

## Supporting findings

- Larger reconstructed misses were more likely to be challenged across every boundary sensitivity threshold.
- Situation substantially improved temporal held-out prediction.
- The accepted pitch-characteristic block added no validated held-out value beyond geometry; this does not show that pitch characteristics never matter.
- Batter identity improved future prediction after observed opportunity difficulty was accounted for; the result does not measure eyesight.

## Appropriate Sprint 5 teaser

Challenge exhaustion sometimes preceded later estimated errors that the team could no longer challenge. Present this as a descriptive bridge to later work, without judging the earlier challenges or claiming the sequential-strategy question as new.

## Claims requiring qualification

Use “estimated incorrect call” or “reconstructed incorrect call” for unchallenged pitches. Describe model results as predictive associations. Pair the 99.968% validation figure with disclosure that three disagreements remain. Describe Pascal as an independently validated season-scale extension of prior work.

## Claims to avoid

- Nobody has studied this.
- This is the first analysis of unchallenged ABS errors.
- Pascal discovered that most bad calls aren't challenged.
- Previous ABS research only looked at actual challenges.
- Our model proves why players challenge.
- ABS officially ruled all 11,704 pitches incorrect.
- Players failed to notice four out of five mistakes.
- Pitch movement does not matter.
- Players waste or mismanage their challenges.
- Pascal's analysis is unprecedented or uniquely comprehensive.

## Recommended article structure

1. **Opening:** Lead with the 19.64% recognition result and its denominator.
2. **What ABS actually does:** Explain the correction mechanism and legal challenge constraint.
3. **How Pascal built the dataset:** Introduce the frozen reconstruction and official validation.
4. **The funnel:** Present 11,704 estimated errors, 10,755 legal opportunities, 2,112 challenged, and 8,643 not challenged.
5. **What predicts a challenge:** Geometry supported; situation strongly supported; no validated incremental value from the pitch block.
6. **Batter differences:** Preview the adjusted temporal result without publishing the Sprint 4 leaderboard.
7. **When challenges run out:** Use the limited Sprint 5 teaser.
8. **Prior work and where Pascal fits:** Credit official and independent work before describing the combined design.
9. **What comes next:** Introduce the research series as a proposed roadmap.

## Revised gate

Methodology = PASS; Boundary Robustness = PASS; Claim Accuracy = PASS; Novelty / Differentiation = PASS; Article 1 = READY_TO_DRAFT. Publication still requires Pascal research-lead and editorial review.
