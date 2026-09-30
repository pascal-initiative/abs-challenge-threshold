"""PV-1 positioning-only revision for Article 1."""
from __future__ import annotations

import argparse, hashlib, json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n")


def claims_matrix() -> str:
    rows = [
        ("A", "Pascal's reconstructed 2026 ABS geometry agreed with 9,482 of 9,485 official decisions, or 99.968%.", "SUPPORTED_WITH_QUALIFICATION", "Accepted validation report and disagreement audit", "One material source-zone-height discrepancy and two microscopic edge discrepancies.", "Public-data reconstructions are common inputs to ABS analysis; this exact frozen reconstruction was independently checked against every official decision in the snapshot.", "Independent reconstruction, exact official validation, and preservation of all disagreements.", "Pascal's public-data reconstruction agreed with 9,482 of 9,485 official ABS challenge decisions (99.968%); the three disagreements are preserved and audited."),
        ("B", "The reconstructed ABS zone identified 11,704 incorrect called strikes.", "SUPPORTED_WITH_QUALIFICATION", "Publication funnel", "Unchallenged pitches lack official adjudication.", "Prior public work has analyzed unchallenged misses and expected opportunities.", "A frozen, reproducible season-scale classification connected to an explicitly validated funnel.", "The reconstructed zone classified 11,704 called strikes as estimated incorrect calls during the accepted snapshot."),
        ("C", "Of those, 10,755 occurred with a legal batter challenge available.", "SUPPORTED", "Sprint 3 population audit", "Excludes 789 resource-constrained and 160 position-player-pitching pitches.", "Expected-opportunity and inventory concepts already appear in Baseball Savant and independent analysis.", "Exact legal-opportunity accounting within Pascal's independently reconstructed snapshot.", "Of those estimated incorrect called strikes, 10,755 occurred while a legal batter challenge was available."),
        ("D", "Batters challenged 2,112 of 10,755, or 19.64%.", "SUPPORTED", "Boundary sensitivity and metric audit", "Recognition is challenge action regardless of outcome.", "Existing public research also studies missed and expected challenge opportunities.", "The statistic comes from Pascal's frozen, validated season-scale funnel and survives preregistered boundary exclusions.", "Batters challenged 2,112 of 10,755 legally challengeable estimated incorrect called strikes (19.64%)."),
        ("E", "Larger misses were more likely to be challenged.", "SUPPORTED", "Boundary sensitivity", "Association, not causation.", "Miss magnitude and location are established predictors in public analysis.", "Pascal verifies the association across a fixed full snapshot and every preregistered uncertainty band.", "The farther an estimated incorrect strike lay beyond the reconstructed boundary, the more likely the batter was to challenge."),
        ("F", "Situation substantially improved prediction.", "SUPPORTED", "Temporal model sensitivity", "Predictive contribution only.", "Baseball Savant, MLB, FanGraphs, and other work already use game context.", "Pascal quantifies incremental value using a fixed feature block and expanding temporal holdouts.", "Game situation substantially improved held-out prediction of whether a batter challenged an estimated incorrect called strike."),
        ("G", "Pitch characteristics did not add validated held-out predictive value beyond geometry.", "SUPPORTED_WITH_QUALIFICATION", "Temporal model sensitivity", "A null incremental block result does not show pitch characteristics never matter.", "Public work considers pitch location and characteristics in challenge behavior.", "Pascal reports a preregistered incremental temporal block comparison rather than a general claim of irrelevance.", "Pitch type, velocity, movement, spin, extension, and release characteristics did not add validated held-out predictive value beyond geometry in the accepted model."),
        ("H", "Batter identity adds information about future recognition after difficulty adjustment.", "SUPPORTED", "Sprint 4 temporal validation", "Do not call this eyesight or direct perception.", "Player challenge and success leaderboards already exist.", "Pascal tests whether prior batter behavior improves future prediction after observed opportunity difficulty is accounted for.", "Batter identity added held-out predictive information about future recognition behavior after opportunity difficulty was accounted for."),
        ("I", "Challenge exhaustion sometimes leaves teams unable to correct later errors.", "SUPPORTED_WITH_QUALIFICATION", "Sprint 5 exhaustion sequences", "Descriptive teaser; no judgment about earlier challenge quality.", "SABR, ABS Charts, TapToChallenge, and open-source work address sequential strategy and resource value.", "Pascal contributes a linked descriptive result within its broader reconstructed research program; Article 1 does not claim the policy idea as novel.", "In the accepted snapshot, challenge exhaustion sometimes preceded later estimated errors that the team could no longer challenge."),
    ]
    cols = ["Claim", "Proposed wording", "Classification", "Evidence", "Qualification", "Prior-work context", "Pascal contribution", "Preferred wording"]
    lines = ["# Article 1 Claims Matrix", "", "This revision retains every accepted quantitative result and adds prior-work context so the preferred wording does not imply ownership of established ABS questions.", "", "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def novelty_matrix() -> pd.DataFrame:
    return pd.DataFrame([
        ("Unchallenged misses and missed challenge opportunities", "ALREADY_WELL_COVERED", "Baseball Savant expected metrics, FanGraphs, ABS Charts, and newsletters already study missed or expected opportunities.", "Pascal does not claim the topic as novel."),
        ("Context affects challenge behavior", "ALREADY_WELL_COVERED", "Official expected-challenge work and independent analyses already incorporate count, game state, value, or inventory.", "Pascal adds a fixed temporal block comparison."),
        ("Sequential resource value and challenge exhaustion", "ALREADY_WELL_COVERED", "SABR reinforcement-learning research, ABS Charts, TapToChallenge, and public Bellman implementations address sequential strategy.", "Article 1 uses Pascal's accepted Sprint 5 result only as a descriptive teaser."),
        ("Frozen reconstructed season-scale error funnel", "MEANINGFUL_EXTENSION", "Prior work studies similar populations, but Pascal links a fixed 645,793-pitch snapshot through every denominator and freezes publication values.", "Reproducible end-to-end accounting is the extension."),
        ("Independent validation against 9,485 official decisions", "MEANINGFUL_EXTENSION", "Pascal checks its public-data geometry against the complete official-challenge set in the accepted snapshot and preserves all three disagreements.", "The validated implementation supports, but does not create, the broader research question."),
        ("Temporal geometry, pitch, situation, and batter comparisons", "MEANINGFUL_EXTENSION", "The predictors are not new; the fixed incremental blocks and expanding monthly holdouts provide additional evidence.", "Differentiate by validation design rather than predictor discovery."),
        ("Separate adversarial publication validation", "DISTINCT_IMPLEMENTATION_OR_VALIDATION", "PV-1 audits integrity, boundary uncertainty, terminology, claims, prior work, and frozen numbers before drafting.", "This describes Pascal's workflow; it is not a claim that no one else validates publications."),
    ], columns=["contribution", "classification", "evidence", "positioning_implication"])


POSITIONING = """# Article 1 Positioning Memo

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
"""


TITLES = """# Article 1 Title Options

## Recommendation

**One in Five: Inside the ABS Recognition Gap**

It foregrounds the strongest validated result, identifies the subject as recognition behavior, and avoids treating reconstructed errors as official rulings. A deck should define the denominator: “A season-scale audit of 10,755 legally challengeable estimated incorrect called strikes.”

## Current working title

**The Errors ABS Doesn't Fix** remains usable if the opening immediately explains that ABS acts only after a legal player challenge and that unchallenged errors are reconstructed estimates. On its own, it can sound as though ABS officially adjudicated every miss, so it is not the preferred title.

## Alternatives

1. **One in Five: Inside the ABS Recognition Gap** — strongest balance of result and precision.
2. **When Hitters Challenge** — accessible, though less specific about the denominator.
3. **From Bad Call to Challenge** — clear funnel framing; use “estimated bad call” in the deck.
4. **What Happens After an Estimated Bad Call?** — precise and question-led.
5. **The ABS Recognition Gap** — concise, but “recognition” must be defined immediately.
6. **Inside Baseball's Challenge Decision** — emphasizes behavior without a novelty claim.
7. **The Called Strikes That Went Unchallenged** — concrete; the reconstruction caveat belongs in the deck.
8. **How Often Do Hitters Challenge an Estimated Miss?** — maximally clear, less literary.
9. **A Season of ABS Decisions** — broad and suitable for a series opener.
"""


PRIOR_WORK = """# Article 1 Prior-Work Framing

## Article-ready section

Pascal's analysis builds on a growing body of public ABS work. [Baseball Savant](https://baseballsavant.mlb.com/leaderboard/abs-challenges?page=0&pageSize=50&sort=n_challenges&sortDir=desc) publishes challenge and expected-challenge metrics, while [MLB](https://www.mlb.com/news/abs-spring-training-2026-takeaways) and [FanGraphs](https://blogs.fangraphs.com/an-early-nerdy-look-at-the-challenge-system/) have examined challenge frequency, pitch location, missed opportunities, game context, and run or win value. [SABR research](https://sabr.org/analytics/presentations), [ABS Charts](https://abscharts.com/writeup/methodology/), [TapToChallenge](https://www.taptochallenge.com/challenges), and [open-source projects](https://github.com/professorpalmer/abs-challenge) have also treated limited challenges as a sequential resource problem. Pascal's contribution is the combined implementation: an independently reconstructed and frozen 2026 MLB snapshot, validation against 9,485 official decisions, a reconciled funnel from all physical pitches to unchallenged estimated errors, temporal tests of observable predictors, and a separate adversarial review of boundary uncertainty, terminology, claims, and publication numbers.

## Approved differentiation language

### Short

Pascal independently reconstructed and validated a fixed 2026 MLB ABS snapshot, then extended prior public work through a reproducible recognition funnel and temporal predictive tests.

### Medium

Public analysts already study ABS challenges, missed opportunities, context, and limited-inventory strategy. Pascal builds on that work with an independently reconstructed 645,793-pitch snapshot, validates the geometry against 9,485 official decisions, follows every denominator from called pitches to legal estimated-error opportunities, and tests recognition predictors on future months.

### Full

This study does not claim to originate analysis of unchallenged misses, expected challenges, contextual decision-making, or sequential challenge value. Baseball Savant, MLB, FanGraphs, SABR researchers, ABS Charts, TapToChallenge, newsletters, and open-source projects provide relevant prior work. Pascal's narrower contribution is a combined reproducible research design: reconstruct a fixed 2026 MLB ABS environment from public data; validate it against the complete set of 9,485 official decisions in the snapshot; reconcile the full funnel from 645,793 physical pitches to legal, challenged, and unchallenged estimated errors; evaluate geometry, pitch, situation, and batter information with expanding temporal holdouts; and subject the proposed public claims to a separate integrity, boundary, terminology, novelty, and number-freeze review.

## Prohibited positioning

Do not use “first,” “nobody has studied this,” “previously unknown,” “unprecedented,” “unique analysis of missed calls,” “Pascal discovered that most bad calls aren't challenged,” “previous ABS research only looked at actual challenges,” or “our model proves why players challenge.” Avoid any wording that converts a reconstructed classification into an official ruling or a predictive association into a causal mechanism.
"""


SERIES = """# Article 1 Series Plan

Article 1 should establish the shared research system—reconstruction, legal opportunity, recognition, action, inventory, and outcome—then show how later articles ask narrower questions. The labels and order below are a working roadmap rather than a publication commitment.

| Working installment | Role in the series | Scope guardrail |
|---|---|---|
| Article 1 — Overarching recognition study | Introduce the validated funnel and one-in-five result. | No novelty claim over missed-opportunity research. |
| Article 2 — Batter recognition | Examine adjusted batter differences and uncertainty. | Do not equate behavior with eyesight or publish unsupported rankings. |
| Article 3 — Geometry, pitch, and situation | Explain temporal feature-block evidence. | Predictive contribution, not causal explanation. |
| Article 4 — Challenge resource management | Study future option value and exhaustion. | Credit prior sequential-strategy work and preserve Sprint 5 sensitivity. |
| Article 5 — Good decisions versus good outcomes | Separate ex-ante quality from realized success. | Avoid moral or player-intelligence judgments. |
| Future defensive recognition work | Extend the framework to catcher or defense decisions. | Treat as future research until separately validated. |

Suggested series introduction: “This article begins a continuing audit of how MLB's ABS challenge system moves from umpire call to recognition, challenge decision, resource use, and outcome. Later installments will examine batter differences, predictive factors, and resource management using the same frozen and auditable framework.”
"""


def run(root: Path) -> None:
    docs = root / "docs/publication_validation"
    art = root / "artifacts/publication_validation"
    manifest_path = art / "positioning_revision_manifest.json"
    changed = [docs / "article1_claims_matrix.md", art / "novelty_matrix.csv"]
    created = [docs / "article1_positioning.md", docs / "article1_title_options.md",
               docs / "article1_prior_work.md", docs / "article1_series_plan.md", manifest_path]
    initial = json.loads((art / "run_manifest.json").read_text())
    existing = json.loads(manifest_path.read_text()) if manifest_path.exists() else None
    prior_hashes = (existing["replaced_file_prior_hashes"] if existing else
                    {str(p.relative_to(root)): sha(p) for p in changed})
    quantitative = [art / "article1_numbers.json", art / "boundary_sensitivity.csv", art / "model_sensitivity.csv",
                    art / "publication_funnel.csv", art / "metric_definitions.csv", art / "boundary_disagreement_audit.csv"]
    quant_before = {str(p.relative_to(root)): sha(p) for p in quantitative}

    write(docs / "article1_claims_matrix.md", claims_matrix())
    novelty_matrix().to_csv(art / "novelty_matrix.csv", index=False, lineterminator="\n")
    write(docs / "article1_positioning.md", POSITIONING)
    write(docs / "article1_title_options.md", TITLES)
    write(docs / "article1_prior_work.md", PRIOR_WORK)
    write(docs / "article1_series_plan.md", SERIES)

    quant_after = {str(p.relative_to(root)): sha(p) for p in quantitative}
    if quant_before != quant_after:
        raise RuntimeError("Positioning revision changed accepted quantitative research")
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    manifest = {
        "revision": "PV-1 novelty, differentiation, and Article 1 positioning",
        "execution_timestamp": now,
        "upstream_pv1_run_manifest_hash": (existing["upstream_pv1_run_manifest_hash"] if existing else sha(art / "run_manifest.json")),
        "upstream_pv1_output_hashes": (existing["upstream_pv1_output_hashes"] if existing else initial["output_hashes"]),
        "replaced_file_prior_hashes": prior_hashes,
        "quantitative_research_hashes_before": quant_before,
        "quantitative_research_hashes_after": quant_after,
        "no_quantitative_research_changed": quant_before == quant_after,
        "files_changed": [str(p.relative_to(root)) for p in changed],
        "files_created": [str(p.relative_to(root)) for p in created],
        "source_inventory_hash": sha(docs / "source_inventory.md"),
        "claims_matrix_hash": sha(docs / "article1_claims_matrix.md"),
        "novelty_matrix_hash": sha(art / "novelty_matrix.csv"),
        "created_file_hashes": {str(p.relative_to(root)): sha(p) for p in created[:-1]},
        "revised_gates": {"methodology": "PASS", "boundary_robustness": "PASS", "claim_accuracy": "PASS",
                          "novelty_differentiation": "PASS", "article1": "READY_TO_DRAFT"},
        "publication_authority": "Pascal research-lead and editorial review remain required."
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--root", type=Path, default=Path("."))
    run(ap.parse_args().root.resolve())
