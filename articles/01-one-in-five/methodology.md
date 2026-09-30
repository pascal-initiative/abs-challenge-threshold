# ABS Recognition Study Methodology

This appendix documents the fixed research population, reconstruction,
validation, terminology, and temporal tests behind “One in Five: Inside
the ABS Recognition Gap.”

## Scope and frozen snapshot

The analysis covers 2,195 MLB regular-season games from March 25 through
September 9, 2026. The accepted snapshot contains 645,793 physical
pitches. Every published Article 1 number was frozen after a separate
publication-validation review; the date range was not expanded
afterward.

| Funnel stage | Count | Denominator |
| --- | --- | --- |
| Physical pitches | 645,793 | All physical pitches |
| Called pitches | 336,095 | Physical pitches |
| Called strikes | 103,768 | Called pitches |
| Estimated incorrect called strikes | 11,704 | Called strikes |
| Legal recognition opportunities | 10,755 | Estimated incorrect called strikes |
| Challenged | 2,112 | Legal recognition opportunities |
| Not challenged | 8,643 | Legal recognition opportunities |

## Reconstructed ABS geometry

Pascal reconstructed the 2026 ABS decision environment from public pitch
location and strike-zone measurements. A pitch was classified by whether
the modeled ball intersected the reconstructed ABS zone. The source
measurements were retained separately from derived classifications, and
boundary distance was stored as a signed value before conversion to
inches.

**Terminology:** an unchallenged pitch never received an
official ABS ruling. The article therefore calls a reconstruction-based
classification an *estimated incorrect call*, not an official
overturn.

## Official-decision validation

The reconstruction was compared with all 9,485 official ABS challenge
decisions in the snapshot. It agreed on 9,482 decisions, or 99.968
percent. All three disagreements were preserved. Two were within 0.005
inches of the reconstructed boundary; the third involved a substantial
difference in the source zone-top value.

## Recognition population

The reconstructed zone classified 11,704 called strikes as estimated
incorrect. Of these, 10,755 occurred while the batter had a legal
challenge available. The exclusions were 789 opportunities after the
affected team had exhausted its challenges and 160 pitches subject to
the position-player-pitching restriction. There were no unknown or other
exclusions.

Recognition is an observable action: a batter challenged a legal
estimated incorrect called strike. Challenge outcome is not part of this
definition. The recognition rate is therefore 2,112 divided by 10,755,
or 19.64 percent.

## Boundary sensitivity

The publication review repeated the analysis after excluding every pitch
whose absolute reconstructed boundary distance was at or below 0.05,
0.10, 0.25, and 0.50 inches. The recognition rate rose from 19.64
percent with no exclusion to 22.51 percent under the 0.50-inch
exclusion. The positive association between miss distance and challenge
action remained under every threshold.

## Temporal predictive testing

Fixed logistic-regression specifications were evaluated with expanding
monthly holdouts: each test month followed all training observations.
The model blocks added geometry first, then measured pitch
characteristics, then situation. Situation included count, outs,
runners, inning, score differential, and remaining challenge inventory.
A later batter analysis estimated player information from earlier games
and evaluated it on later observations.

Situation produced a substantial held-out improvement. The
pitch-characteristic block did not add validated held-out predictive
value beyond geometry in the accepted specification. These are
predictive findings, not causal claims.

## Publication validation

Before drafting, Pascal separately checked upstream artifact integrity,
all three geometry disagreements, boundary sensitivity, funnel
arithmetic, metric definitions, representative examples, prior work,
claim language, and frozen publication numbers. The review also
distinguished recognition rate from overall challenge rate, challenge
success rate, and correction rate.

This appendix describes the accepted Article 1 analysis. Future articles
may examine batter differences, feature contributions, and
challenge-resource management, each under its own validation scope.
