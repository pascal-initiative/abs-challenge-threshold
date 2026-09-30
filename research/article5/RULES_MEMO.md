# ABS-05 Rules Memo

Verified 2026-09-25 from official MLB sources. Archive retrieval metadata in the
first implementation manifest. If a rule changes, create a dated memo revision;
do not silently change the engine.

## Confirmed mechanics

- Each club begins with two ABS challenges.
- A successful challenge is retained; an unsuccessful challenge consumes one.
- Only the batter, pitcher, or catcher may initiate a challenge.
- The request must be immediate and may not use help from the dugout or other
  players. MLB describes the operational window as roughly two seconds.
- If a runner play or checked-swing appeal follows the pitch, the ABS request may
  be made after that play concludes.
- Position-player pitching and the period immediately after a replay review are
  non-challengeable situations described by MLB.
- In an extra inning, a team with no challenge entering the inning is awarded
  one. The model must not treat this as a general increment above one.
- The 2026 zone is a two-dimensional rectangle at the middle of the plate: 17
  inches wide, top at 53.5% and bottom at 27% of certified player height; any
  part of the ball touching the zone is a strike.
- Umpires preserve runner-play outcomes they judge unaffected by the corrected
  call. Runner placement can therefore require judgment; ambiguous Article 4
  counterfactuals remain bounded rather than guessed.

## Primary sources

- [MLB approval and core rules](https://www.mlb.com/press-release/press-release-mlb-announces-abs-challenge-system-coming-to-the-major-leagues-beginning-in-the-2026-season)
- [MLB 2026 system overview](https://www.mlb.com/news/ball-strike-challenge-system-2026)
- [MLB detailed 2026 rules explainer](https://www.mlb.com/news/abs-challenge-system-mlb-2026)
- [Baseball Savant ABS dashboard](https://baseballsavant.mlb.com/abs)

## Remaining rule checks

Before postseason or cross-season use, verify whether challenge allotment,
extra-inning treatment, or postseason mechanics differ. Timeliness or assistance
denials are not equivalent to Hawk-Eye confirmation; the dataset must determine
whether they appear in official challenge records before treating them as
probability-model failures.
