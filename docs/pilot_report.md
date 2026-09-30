# Pilot results — August 24–30, 2026

**Validation passed: 447/447 official calls agree (100%).** All 93 completed regular-season games are accounted for. All official challenge pitches match; no validation disagreements were found.

| Count | All | Offense: original strikes | Defense: original balls |
|---|---:|---:|---:|
| Called pitches | 14,310 | 4,396 | 9,914 |
| Incorrect calls | 965 | 509 | 456 |
| Corrected | 249 | 96 | 153 |
| Survived with challenge available | 672 | 388 | 284 |
| Survived after exhaustion | 32 | 15 | 17 |
| Unknown classifications | 12 | 10 | 2 |

There are 27,569 total physical pitches. All 12 unknown called-pitch classifications are incorrect calls with POSITION_PLAYER_PITCHING; they remain in the incorrect-call denominator.

| Rate | All | Offense | Defense |
|---|---:|---:|---:|
| incorrect_call_rate | 6.74% | 11.58% | 4.60% |
| correction_rate | 25.80% | 18.86% | 33.55% |
| survival_rate | 72.95% | 79.17% | 66.01% |
| recognition_survival_rate | 69.64% | 76.23% | 62.28% |
| resource_constrained_survival_rate | 3.32% | 2.95% | 3.73% |

The survival rate above counts the two classified survival categories. Correction and survival do not sum to 100% because the legal-restriction UNKNOWN cases remain in the denominator. These are descriptive pilot counts, with no player rankings or causal interpretation.

## Data quality

| Check | Count |
|---|---:|
| missing_pitch_locations | 0 |
| missing_movement_data | 0 |
| missing_catcher_ids | 0 |
| missing_umpire_ids | 0 |
| missing_challenge_matches | 0 |
| duplicate_pitch_keys | 0 |
| impossible_counts | 0 |
| impossible_challenge_inventory | 0 |
| pitch_rows_deleted | 0 |

The source audit preserves **117 automatic nonpitch records** (0.423% of 27,686 Statcast records) and **37 documented pitch-number offsets**. Automatic events are outside the physical-pitch universe; no physical pitches are excluded. There are no failed downloads or unexplained source discrepancies.

## Validation details

| Group | Official challenges | Agreements | Disagreements |
|---|---:|---:|---:|
| confirmed | 198 | 198 | 0 |
| original_called_ball | 259 | 259 | 0 |
| original_called_strike | 188 | 188 | 0 |
| overturned | 249 | 249 | 0 |

Daily official challenge totals are 52, 91, 68, 26, 79, 72, and 59, each independently reconciled to the official dashboard. The empty discrepancy CSV retains a header so downstream readers can distinguish zero discrepancies from a missing artifact.

## Detailed exploratory output

See `data/processed/recognition_breakdowns.csv` for counts and three explicitly named rates by pitch type, inning, count, outs, base state, remaining challenges, batter, pitcher, catcher, and umpire. Identity groups are sorted by identifier. `recognition_distributions.json` contains release speed, movement, location, and boundary-distance summaries, each split by offensive and defensive opportunity. [Methodology](methodology.md) defines all denominators and limitations.
