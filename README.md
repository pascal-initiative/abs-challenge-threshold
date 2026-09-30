# ABS Challenge Threshold

This repository holds the Pascal Institute's research on Major League Baseball's Automated Ball-Strike (ABS) challenge system during the 2026 season, along with the five articles that research produced. The series began with a simple question about how often hitters challenge an incorrect called strike, and it gradually became a study of decision-making under uncertainty. A player has about two seconds to decide whether the umpire missed a pitch, the resource he risks is limited, and the answer arrives almost immediately. That combination makes an ABS challenge an unusually clean place to separate the quality of a decision from its outcome.

Everything here is built from public MLB data. We reconstructed the ABS strike zone from Statcast tracking and tested it against every official challenge before relying on it, and the reconstruction agreed with 9,482 of the 9,485 challenges made from March 25 through September 9. The articles explain the findings for a general reader. The methodology, research records, code, and data tables are included so that anyone who wants to check our work, or build on it, has what they need.

## The articles

| | Article | What it asks |
| --- | --- | --- |
| 1 | [One in Five: Inside the ABS Recognition Gap](articles/01-one-in-five/) | How often do hitters challenge an incorrect called strike? About one time in five, 2,112 of 10,755 opportunities. |
| 2 | [The Challenge Threshold](articles/02-the-challenge-threshold/) | How do the pitch, the count, and the game situation shape whether a hitter asks ABS to review a call? |
| 3 | [Who Sees the Miss?](articles/03-who-sees-the-miss/) | After accounting for how recognizable a missed call was, does a hitter's history still predict what he does next? |
| 4 | [What Is a Challenge Worth?](articles/04-what-is-a-challenge-worth/) | What is correcting a call worth in expected runs, and what is a challenge worth when it is saved for later? |
| 5 | [Pricing an ABS Challenge](articles/05-pricing-an-abs-challenge/) | How strong does the evidence need to be before challenging is worth the risk? This article introduces Challenge Threshold and the Decision Opportunity Score. |

Articles 1 through 4 are published at [pascalinitiative.com](https://www.pascalinitiative.com/research-insights/). Article 5 is included as Draft 3. Each article folder holds the article, its methodology, its figures, and a `data/` folder with the tables behind it.

## How the repository is organized

```text
articles/    The five articles, each with methodology, figures, and supporting tables
data/        How the data was acquired, the download receipts, and the link to the full data set
src/         Core pipeline: acquisition, pitch parsing, ABS geometry, validation, and sprint analyses
research/    Analysis code and research records for Articles 2, 4, and 5
docs/        Methodology, data dictionaries, and validation reports from each research sprint
notebooks/   Read-only notebooks for inspecting the persisted reports
tests/       Unit, source-fixture, and reproducibility tests
```

A reader who wants the conclusions should start in `articles/`. A reader who wants to verify a specific number should open that article's `data/` folder, where a short README names the script that produced each table. The research was organized into numbered sprints before it was organized into articles, so the code still uses those names. Sprint 1 built and validated the pipeline on a pilot week, Sprints 2 and 3 studied hitter recognition and support Articles 1 and 2, Sprint 4 supports Article 3, and Sprint 5 is the resource-management work that preceded Article 4. The code keeps the layout of the original research repository so that the scripts run without modification once the full data set is restored.

## Where the data came from

All data came from two public MLB sources: the MLB Stats API, which supplied schedules and pitch-by-pitch game feeds, and Baseball Savant, which supplied Statcast tracking and the official record of every ABS challenge. Each download was stored under its SHA-256 hash and logged in an append-only receipt, and every later step ran offline from those stored bytes. The pipeline was designed to fail rather than publish when sources disagreed, and it would not release a data set unless the reconstructed zone agreed with at least 99 percent of official challenge outcomes. [data/README.md](data/README.md) explains the full acquisition and validation process.

## The full data set

This repository contains derived results only. The raw MLB responses and pitch-level tables total about 4.6 GB, far beyond what GitHub is designed to hold, so they are published separately at [pascalinitiative.com/data/abs-challenge-threshold](https://www.pascalinitiative.com/data/abs-challenge-threshold/) as four compressed archives (about 0.9 GB together). Each archive stores its files under their original repository paths, so extracting all four at the root of this repository restores the complete research environment. [data/README.md](data/README.md) lists the archives and explains how to verify them.

## Reproducing the research

The analyses were run with Python 3.9.6, and the pinned package versions are in the `requirements-sprint*-lock.txt` files. After restoring the full data set, `python3 -m pytest` runs the test suite, and the README in each `research/` subfolder gives the exact commands for that article. Several tests re-run complete analyses and write their outputs in place, and chart images are not byte-identical across operating systems and library builds, so those determinism tests are best run on a copy you are willing to regenerate. Acquisition is the only step that uses the network. Re-running it will not reproduce our bytes exactly, because MLB revises its data after publication, which is why the original responses are preserved in the full data set.

## Terms and limits

The underlying data belongs to MLB and is subject to the [MLB.com Terms of Use](https://www.mlb.com/official-information/terms-of-use). This is independent research and is not affiliated with or endorsed by Major League Baseball. Our findings are observational. They describe what players did and what our models estimate a decision was worth, but public data cannot tell us what a player saw, how confident he was, or what his team instructed him to do, and none of this work should be read as a playbook for when to challenge.
