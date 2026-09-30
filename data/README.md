# Data

This folder explains where the research data came from, how it was acquired and validated, and how to obtain the complete data set. The download receipts are stored here because they are the permanent record of what was collected. The tables that support each article are stored with that article in `articles/<article>/data/`, and the raw source files and pitch-level tables are published separately because of their size.

## Sources

Every input came from one of two public MLB services. We did not use any third-party research data set or model.

| Source | Endpoint | What it supplied |
| --- | --- | --- |
| MLB Stats API | `/api/v1/schedule` | The regular-season games played on each date |
| MLB Stats API | `/api/v1.1/game/{game_pk}/feed/live` | Every pitch in order, player names, and the home-plate umpire |
| Baseball Savant | `statcast_search/csv`, one request per day | Pre-pitch count, outs, runners, and score, plus pitch location, movement, and the 2026 ABS zone boundaries |
| Baseball Savant | `leaderboard/services/abs/{team_id}`, one request per team | The official record of every ABS challenge and its outcome |
| Baseball Savant | `/abs` dashboard | Independent daily challenge totals used to confirm that no challenge was missing |

## How the data was acquired

We collected data in three windows. A pilot week from August 24 through August 30, 2026 was used to build and test the pipeline before any season-level analysis. The season snapshot, acquired on September 10, covers March 25 through September 9 and is the basis for Articles 1 through 4 and the development period of Article 5. September 10 was downloaded but excluded because its official daily challenge total was not yet available. The confirmation window, September 11 through September 27, was downloaded on September 28, only after the Article 5 reference model had been frozen, so it served as a true holdout. A small additional download on September 24 retrieved the Braves games used in the Article 4 case study.

Each request was saved exactly as received, under a file name equal to the SHA-256 hash of its contents, and logged in an append-only receipt that records the URL, retrieval time, content type, size, and hash. Failed requests were logged as well. A stored response was never edited or replaced, and every later step ran offline from those stored bytes, checking each hash before use. This design matters because MLB revises its public data after games are played. Downloading the same URL today can return different numbers, so the stored responses, not the URLs, are the authoritative record of what we analyzed.

## How the data was validated

The game feed and Statcast count pitches differently, because Statcast includes automatic balls and strikes from pitch-timer violations while the feed does not. The pipeline therefore matches the two sources plate appearance by plate appearance, pairs the physical pitches in order, and refuses to join a plate appearance whose sequences do not line up. Pre-pitch game state comes from Statcast, so no information from after the pitch enters the tables.

We then reconstructed the ABS strike zone from MLB's published rules: a 17-inch-wide zone at the middle of the plate, bounded at 27 percent and 53.5 percent of the batter's certified height, with any overlap by the ball counting as a strike. The ball radius of 1.45 inches comes from Baseball Savant's own zone visualization and was fixed before we compared any results. Before a data set could be released, the reconstructed call had to agree with at least 99 percent of official challenge outcomes, every challenge had to be matched to its pitch, and every game had to be accounted for. The pipeline also replays each team's challenge inventory pitch by pitch, so we know whether a challenge was actually available when each incorrect call occurred.

| Window | Games | Physical pitches | Official challenges | Agreement with reconstruction |
| --- | ---: | ---: | ---: | ---: |
| Pilot, August 24 to 30 | 93 | 27,569 | 447 | 447 (100.0%) |
| Season, March 25 to September 9 | 2,195 | 645,793 | 9,485 | 9,482 (99.97%) |
| Confirmation, September 11 to 27 | 230 | 67,355 | 1,050 | 1,049 (99.90%) |

Agreement on challenged pitches does not prove the reconstruction is perfect for every unchallenged pitch, because challenged pitches are a selected sample. It does show that the geometry reproduces ABS rulings closely where the official answer is known. The pipeline methodology is documented in [docs/methodology.md](../docs/methodology.md), and the field definitions are in [docs/data_dictionary.md](../docs/data_dictionary.md).

## Receipts

The `receipts/` folder holds the receipt log for each download window. Each line is one request, and the `sha256` field identifies the stored response in the full data set, so any raw file can be traced back to the exact URL and time it was retrieved.

| File | Requests |
| --- | ---: |
| [pilot-2026-08-24-to-08-30.jsonl](receipts/pilot-2026-08-24-to-08-30.jsonl) | 136 |
| [season-2026-03-25-to-09-10.jsonl](receipts/season-2026-03-25-to-09-10.jsonl) | 2,430 |
| [confirmation-2026-09-11-to-09-27.jsonl](receipts/confirmation-2026-09-11-to-09-27.jsonl) | 312 |
| [article4-braves-case-study.jsonl](receipts/article4-braves-case-study.jsonl) | 13 |

## The full data set

The complete data set is published at [pascalinitiative.com/data/abs-challenge-threshold](https://www.pascalinitiative.com/data/abs-challenge-threshold/) as four archives. Each one stores its files under their original repository paths, so extracting them at the root of this repository restores the environment the code expects. Most visitors will only need the analysis archive, while the raw sources are needed only to rebuild everything from the original MLB responses.

| Archive | Size | Contents |
| --- | ---: | --- |
| `abs-challenge-threshold-analysis.tar.gz` | 103 MB | All analysis outputs, including the pitch-level and opportunity-level tables held back from this repository |
| `abs-challenge-threshold-ct-s1.tar.gz` | 95 MB | Every Article 5 CT-S1 table, from the prepared inputs through the sampling intervals and reproducibility checks |
| `abs-challenge-threshold-season-tables.tar.gz` | 236 MB | The processed pitch and challenge tables for the pilot week and the season snapshot |
| `abs-challenge-threshold-raw-sources.tar.gz` | 522 MB | Every stored MLB response for all download windows, with its receipt log |

To verify the downloads and restore them, run these commands from the repository root with the archives and `SHA256SUMS` in the same folder:

```bash
shasum -a 256 -c SHA256SUMS
for archive in abs-challenge-threshold-*.tar.gz; do tar -xzf "$archive"; done
```

The data is published for research and verification. It remains the property of MLB and is subject to the [MLB.com Terms of Use](https://www.mlb.com/official-information/terms-of-use).
