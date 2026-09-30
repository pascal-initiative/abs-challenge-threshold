# Pascal ABS Research

## Sprint 1 — Pilot Data Acquisition, Reconstruction, and Validation

**Project:** Pascal Initiative / Pascal Institute
**Research Area:** MLB Automated Ball-Strike Challenge System
**Sprint:** 1
**Pilot Period:** August 24–30, 2026
**Status:** Requirements
**Primary Deliverable:** Validated pitch-level research dataset

---

## 1. Purpose

Build a reproducible research pipeline for studying MLB's Automated Ball-Strike (ABS) Challenge System.

The broader research question is:

> **What determines whether an incorrect ball-strike call survives the ABS challenge system?**

This research is not intended to create another ABS challenge leaderboard.

Existing public work already measures challenge success, expected challenges, missed opportunities, challenge value, and aspects of challenge strategy.

The intended contribution of this project is to investigate why incorrect calls remain uncorrected, including possible effects from:

* batter recognition;
* catcher receiving;
* pitcher characteristics;
* pitch movement and location;
* umpire behavior;
* count and game situation;
* leverage;
* game progression; and
* challenge availability.

Sprint 1 does **not** attempt to answer those questions.

Sprint 1 establishes and validates the dataset required to answer them.

---

# 2. Sprint Objective

Produce a validated pitch-level dataset covering all MLB regular-season games from:

**August 24, 2026 through August 30, 2026, inclusive.**

The pipeline must identify every relevant called pitch and classify incorrect calls according to whether they were:

1. corrected through ABS;
2. left unchallenged despite a challenge being available; or
3. left unchallengeable because the affected team had exhausted its challenges.

The system must be reproducible and designed so the same pipeline can later be expanded from the pilot week to the complete 2026 MLB season.

---

# 3. Scope

## 3.1 Included

Sprint 1 includes:

* MLB regular-season games;
* completed games only;
* all pitches during the pilot period;
* called balls;
* called strikes;
* official ABS challenges;
* official challenge outcomes;
* game state;
* batter identity;
* pitcher identity;
* catcher identity;
* home-plate umpire identity;
* pitch characteristics;
* pitch location;
* challenge inventory;
* reconstruction of original umpire calls;
* identification of incorrect calls;
* deterministic classification of incorrect calls;
* validation against known official ABS outcomes;
* basic descriptive counts.

## 3.2 Excluded

Do not build the following during Sprint 1:

* player rankings;
* catcher rankings;
* pitcher rankings;
* umpire rankings;
* Challenge Decision Efficiency;
* run expectancy models;
* win probability models;
* leverage models;
* expected challenge models;
* machine-learning models;
* regression models;
* mixed-effects models;
* catcher-effect analysis;
* pitcher-effect analysis;
* pitch-shape analysis;
* early-versus-late significance testing;
* resource-management optimization;
* dashboards;
* web interfaces;
* APIs;
* production deployment;
* AnalytIQ integration.

These belong to later research sprints.

Do not expand scope simply because additional analysis appears easy.

---

# 4. Research Principle

The fundamental unit of analysis is the **called pitch**, not the challenge.

This distinction is critical.

Most existing ABS analysis begins with pitches that players chose to challenge.

This research ultimately needs to examine the larger population:

> **Every incorrect call, including those that were never challenged.**

Sprint 1 must therefore preserve the complete called-pitch opportunity universe.

---

# 5. Repository

Create a standalone repository/project.

Suggested name:

`pascal-abs-research`

Suggested structure:

```text
pascal-abs-research/
├── README.md
├── requirements.txt
├── src/
│   ├── fetch_games.py
│   ├── fetch_pitches.py
│   ├── fetch_abs.py
│   ├── parse_pitches.py
│   ├── reconstruct_inventory.py
│   ├── classify_calls.py
│   └── validate.py
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
├── notebooks/
│   ├── 01_pilot_validation.ipynb
│   └── 02_pilot_descriptive.ipynb
├── tests/
└── docs/
    ├── methodology.md
    └── data_dictionary.md
```

Equivalent organization is acceptable if there is a strong technical reason, but maintain clear separation among acquisition, transformation, validation, and analysis.

---

# 6. Reproducibility Requirements

The research must be reproducible from source data.

Raw downloaded data must never be modified in place.

Use three logical data layers:

### Raw

Exact or minimally wrapped source responses.

### Interim

Parsed and normalized data.

### Processed

Final research-ready tables.

All derived fields must be generated programmatically.

Do not manually correct records without documenting the correction and preserving the original value.

Every unexplained source discrepancy should remain discoverable.

---

# 7. Data Source Hierarchy

Use authoritative MLB/Baseball Savant data wherever possible.

## 7.1 MLB Game Data

Use MLB game/schedule and live game-feed data for:

* game identity;
* participants;
* play-by-play;
* pitch sequence;
* count;
* outs;
* runners;
* score;
* batter;
* pitcher;
* catcher;
* home-plate umpire;
* pitch characteristics;
* pitch coordinates.

Known public endpoints include the MLB schedule and game `feed/live` interfaces.

Do not assume that the MLB `hasReview` field represents the complete authoritative ABS challenge population.

## 7.2 Baseball Savant / Statcast

Use Baseball Savant as the preferred authoritative source for ABS challenge identification and official ABS outcomes when available.

The implementation should reconcile Savant challenge records with MLB game-feed pitch records.

## 7.3 External Research Sources

Public projects such as TapToChallenge, ABSScoreboard, and existing open-source ABS research may be used for:

* validation;
* methodology comparison;
* discrepancy investigation;
* implementation reference.

They must **not** silently become the authoritative underlying data source.

Document whenever an external source is used for validation.

---

# 8. Pilot Period

Process:

**2026-08-24 through 2026-08-30**

Filter to:

* MLB;
* regular season;
* completed games.

Create a game manifest containing at minimum:

```text
game_pk
game_date
away_team
home_team
venue
status
```

Record the expected and successfully processed game counts.

Any missing or failed game must be reported.

---

# 9. Pitch-Level Dataset

Create one record for every pitch.

At minimum capture the following where available.

## Game Identity

```text
game_pk
game_date
season
game_type
home_team_id
home_team
away_team_id
away_team
venue
```

## Game State

Capture the state applicable to the challenge decision.

```text
inning
half_inning
home_score
away_score
score_diff
outs
on_1b
on_2b
on_3b
balls
strikes
```

Prefer **pre-pitch/pre-decision state** wherever possible.

Document clearly whether each field represents pre-pitch or post-pitch state.

Do not silently mix the two.

## Pitch Identity

```text
at_bat_index
pitch_number
play_event_index
play_id
```

Create a deterministic unique pitch key if necessary.

## Participants

```text
batter_id
batter_name

pitcher_id
pitcher_name

catcher_id
catcher_name

umpire_id
umpire_name

bat_side
pitch_hand
```

Catcher identity is required for every relevant pitch, not only pitches challenged by catchers.

Home-plate umpire identity is required.

## Pitch Characteristics

Capture available Statcast/MLB fields including:

```text
pitch_type
pitch_name
release_speed
release_spin_rate
spin_axis
pfx_x
pfx_z
extension
release_pos_x
release_pos_y
release_pos_z
plate_x
plate_z
```

Preserve source units.

Document units in `data_dictionary.md`.

Do not transform movement variables for modeling during Sprint 1.

## Strike-Zone Information

Preserve all source zone-related values available, including:

```text
sz_top
sz_bot
```

If additional ABS-specific zone geometry is available, preserve it separately.

Do not overwrite source Statcast zone fields with derived ABS values.

---

# 10. Original Call

For each called pitch capture:

```text
original_call
```

Normalized values:

```text
BALL
STRIKE
```

For overturned challenges, ensure this represents the **umpire's original call before ABS review**, not the displayed post-review result.

Preserve the raw source call separately when useful.

---

# 11. Challenge Dataset

Create a challenge table containing one row per official ABS challenge.

Minimum fields:

```text
game_pk
pitch_key
game_date

challenger_id
challenger_name
challenger_role
challenge_team_id

original_call
official_abs_call

overturned
outcome
```

Allowed challenger roles:

```text
BATTER
CATCHER
PITCHER
UNKNOWN
```

Allowed outcomes:

```text
OVERTURNED
CONFIRMED
UNKNOWN
```

Unknown values must remain unknown rather than being guessed.

---

# 12. Challenge Inventory Reconstruction

ABS challenges are a scarce game resource.

Reconstruct challenge inventory sequentially for both teams.

For each relevant pitch, derive:

```text
offense_challenges_remaining
defense_challenges_remaining
affected_team_challenges_remaining
challenge_available
```

Inventory must reflect the state **before the challenge decision**.

Successful challenges retain the challenge.

Unsuccessful challenges consume one challenge.

The implementation must account for the official 2026 MLB challenge rules.

Document all inventory rules in `methodology.md`.

Create tests covering at minimum:

* successful challenge;
* unsuccessful challenge;
* consecutive successful challenges;
* exhaustion of first challenge;
* exhaustion of final challenge;
* offensive challenge;
* defensive challenge;
* extra innings if applicable.

Do not infer a recognition failure when no challenge was legally available.

---

# 13. Determining the Correct ABS Call

This is the most important validation problem in Sprint 1.

Develop a reproducible method for determining whether the original umpire call was correct under the 2026 ABS system.

Preserve separately:

```text
original_call
derived_abs_call
official_abs_call
```

Do not assume the historical Statcast `sz_top` and `sz_bot` rectangle exactly represents the 2026 ABS zone.

Document the 2026 ABS geometry and measurement rules used.

The derived method must first be tested against pitches with known official ABS outcomes.

---

# 14. Validation Gate

Before classifying unchallenged pitches, compare:

```text
derived_abs_call
```

against:

```text
official_abs_call
```

for every official challenge in the pilot.

Produce:

```text
official_challenges
matched_challenges
unmatched_challenges
agreement_count
disagreement_count
agreement_rate
```

Also break agreement down by:

```text
original called strike
original called ball
overturned
confirmed
```

Every disagreement must be output to a separate discrepancy table containing enough information for manual investigation.

Target validation:

**≥ 99% agreement**

This is a research-quality target, not permission to manipulate the methodology until the target is reached.

If agreement is below 99%, stop downstream incorrect-call classification and investigate.

Do not hide discrepancies.

Do not automatically discard disagreement records.

---

# 15. Incorrect Call Classification

After the validation gate succeeds, classify every relevant called pitch.

Primary field:

```text
survival_class
```

Allowed values:

### CORRECT_CALL

Original umpire call agrees with the derived ABS call.

### CORRECTED

Original umpire call was incorrect and was successfully challenged.

### SURVIVED_RECOGNITION

Original umpire call was incorrect.

A challenge was legally available to the affected team.

The pitch was not successfully challenged.

This category should preserve whether the pitch was:

```text
NOT_CHALLENGED
CHALLENGED_BUT_CONFIRMED
```

if the data permits that distinction.

Do not collapse unexpected discrepancies.

### SURVIVED_RESOURCE

Original umpire call was incorrect.

The affected team had no challenge available.

### UNKNOWN

Insufficient information exists for a defensible classification.

Unknown is preferable to an unsupported assumption.

---

# 16. Offensive and Defensive Populations

Maintain the distinction between:

### Offensive recognition opportunities

Incorrect **called strikes** affecting the batter/offense.

### Defensive recognition opportunities

Incorrect **called balls** affecting the defense.

Do not combine these populations in later descriptive summaries without also reporting them separately.

The perception and decision processes are different.

---

# 17. Pilot Descriptive Report

After successful validation, produce basic descriptive statistics only.

At minimum report:

```text
games processed
total pitches
called pitches
called strikes
called balls

incorrect calls
incorrect called strikes
incorrect called balls

incorrect calls corrected
incorrect calls surviving with challenge available
incorrect calls surviving because challenge unavailable
unknown classifications
```

Calculate:

```text
incorrect_call_rate

correction_rate

survival_rate

recognition_survival_rate

resource_constrained_survival_rate
```

Define every metric explicitly in the methodology.

---

# 18. Initial Descriptive Breakdowns

For `SURVIVED_RECOGNITION` pitches, provide simple counts and rates by:

```text
pitch_type
inning
count
outs
base_state
challenges_remaining
batter
pitcher
catcher
umpire
```

Also provide descriptive distributions for:

```text
release_speed
pfx_x
pfx_z
plate_x
plate_z
distance_from_abs_boundary
```

These are exploratory summaries only.

Do not interpret them as causal effects.

Do not rank players based on the one-week sample.

---

# 19. Data Quality Report

Produce a data-quality summary containing:

* missing pitch locations;
* missing movement data;
* missing catcher IDs;
* missing umpire IDs;
* missing challenge matches;
* duplicate pitch keys;
* impossible counts;
* impossible challenge inventory;
* unknown classifications;
* failed game downloads;
* source discrepancies.

No silent row deletion.

If records must be excluded, report:

```text
reason
row_count
percentage_of_population
```

---

# 20. Testing

Automated tests are required.

Test at minimum:

### Pitch parsing

* called ball;
* called strike;
* swinging strike;
* foul;
* ball in play.

### Challenge parsing

* batter challenge;
* catcher challenge;
* pitcher challenge;
* overturned;
* confirmed.

### Original-call reconstruction

Verify that an overturned displayed result does not overwrite the original umpire call.

### Inventory

Verify challenge retention and depletion.

### Classification

Verify each:

```text
CORRECT_CALL
CORRECTED
SURVIVED_RECOGNITION
SURVIVED_RESOURCE
UNKNOWN
```

### Determinism

Running the pipeline twice against identical raw inputs must produce identical processed outputs.

---

# 21. Documentation

Create `docs/methodology.md`.

It must explain:

1. data sources;
2. pilot date range;
3. game inclusion criteria;
4. pitch extraction;
5. participant identification;
6. original-call reconstruction;
7. official challenge matching;
8. ABS zone reconstruction;
9. challenge inventory reconstruction;
10. survival classification;
11. known limitations;
12. validation results.

Create `docs/data_dictionary.md` documenting every processed field, including:

```text
field name
description
source
unit
raw/derived status
nullable status
```

---

# 22. Provenance

Where practical, preserve provenance for important fields.

For example:

```text
source_game_feed
source_savant
source_derived
```

A future researcher should be able to determine whether a value came directly from MLB, Baseball Savant, or Pascal's transformation logic.

---

# 23. Research Integrity Requirements

Do not optimize the pipeline to produce an interesting result.

Do not remove observations because they contradict expectations.

Do not use hindsight game outcomes when reconstructing the information available at the challenge decision.

Do not classify an unchallengeable pitch as a player recognition failure.

Do not describe correlations as causal effects.

Do not construct player/catcher/pitcher/umpire rankings from the pilot week.

Document uncertainty.

Preserve unexpected results.

---

# 24. Sprint Deliverables

Sprint 1 is complete when the repository contains:

### 1. Reproducible acquisition pipeline

Capable of downloading/reconstructing the August 24–30 pilot.

### 2. Raw source data

Stored or reproducibly retrievable according to repository/data-size constraints.

### 3. Processed pitch-level dataset

One row per pitch with required game, participant, pitch, call, and challenge fields.

### 4. Official challenge dataset

One row per known ABS challenge.

### 5. Challenge inventory reconstruction

For both teams throughout each game.

### 6. ABS validation report

Including agreement rate and every discrepancy.

### 7. Survival-class dataset

Created only after the validation gate passes.

### 8. Pilot descriptive report

Counts and simple distributions.

### 9. Data-quality report

Including missingness and exclusions.

### 10. Automated tests

Covering parsing, challenge reconstruction, inventory, and classification.

### 11. Methodology

`docs/methodology.md`

### 12. Data dictionary

`docs/data_dictionary.md`

---

# 25. Acceptance Criteria

Sprint 1 is accepted when:

* all final MLB regular-season games from August 24–30 are accounted for;
* every pitch has a deterministic key;
* called balls and strikes can be identified;
* batter, pitcher, catcher, and home-plate umpire are captured wherever source data permits;
* official ABS challenges are matched to pitches;
* original umpire calls are preserved correctly;
* challenge inventory is reconstructed sequentially;
* derived ABS calls are validated against official ABS results;
* validation agreement is reported transparently;
* discrepancies are preserved for investigation;
* incorrect calls receive deterministic survival classifications after validation;
* basic descriptive counts are produced;
* the entire pipeline can be rerun;
* automated tests pass;
* methodology and data dictionary are complete.

---

# 26. Stop Conditions

Stop and report rather than improvising if:

* an authoritative ABS challenge source cannot be reliably accessed;
* official challenges cannot reliably be matched to MLB pitches;
* catcher identity cannot be reconstructed reliably;
* challenge inventory rules cannot be determined;
* ABS geometry cannot be reproduced with sufficient accuracy;
* validation agreement remains below 99%;
* material differences appear between MLB, Savant, and validation sources.

A stop condition is a research finding, not a sprint failure.

Document the issue and recommend the next investigation.

---

# 27. Future Research — Context
