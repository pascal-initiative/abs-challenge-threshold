"""Freeze Article 3 publication-validation artifacts without changing Sprint 4."""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path


ACCEPTED_SPRINT4_MANIFEST_SHA256 = "a7d68a88c60ac3b9247f23b77e7bb66283578560b9ef6a2d0c8547bdc45fde3a"
ACCEPTED_SPRINT4_HASH_LIST_SHA256 = "9274a9921f52ad8fe96b334f02368542c960631f5c5ca671fff841ea85230905"
ACCEPTED_SPRINT3_MANIFEST_SHA256 = "58abbfabb9318692e14199dcd6099fe847ae6497ef27e84e22cea45f9b5561d0"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n")


def write_csv_json(base: Path, rows: list[dict]) -> None:
    base.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"No rows for {base}")
    with base.with_suffix(".csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    base.with_suffix(".json").write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")


def claims_markdown(rows: list[dict]) -> str:
    lines = [
        "# Article 3 Final Publication Claims Matrix",
        "",
        "This matrix governs Article 3 wording. The machine-readable CSV and JSON are authoritative mirrors.",
    ]
    for index, row in enumerate(rows, 1):
        lines.extend([
            "",
            f"## {index}. {row['claim']}",
            "",
            f"- Status: **{row['status']}**",
            f"- Sprint 4 evidence: {row['sprint4_evidence']}",
            f"- Publication-safe wording: {row['publication_safe_wording']}",
            f"- Limitations: {row['limitations']}",
            f"- Prohibited wording: {row['prohibited_wording']}",
        ])
    return "\n".join(lines)


CLAIMS = [
    {
        "claim": "Historical batter recognition behavior contains information about future recognition beyond measured opportunity characteristics.",
        "status": "SUPPORTED",
        "sprint4_evidence": "Final temporal holdout: log loss -0.012760, Brier -0.004563, ROC AUC +0.018869 versus the accepted opportunity model.",
        "publication_safe_wording": "Historical batter recognition behavior contained information about future recognition beyond the measured characteristics of the opportunity.",
        "limitations": "One season; predictive, not causal; recognition is challenge action; unmeasured context may remain.",
        "prohibited_wording": "Batter identity proves who sees the strike zone best.",
    },
    {
        "claim": "Some batters differed in adjusted recognition behavior.",
        "status": "SUPPORTED_WITH_QUALIFICATION",
        "sprint4_evidence": "Empirical-Bayes batter effects remained after accepted opportunity adjustment; 123 batters met ranking support.",
        "publication_safe_wording": "The adjusted estimates show meaningful batter-to-batter differences in observed recognition behavior, with substantial uncertainty around many players.",
        "limitations": "Effects combine perception, decision, timing, instruction, and other unmeasured influences.",
        "prohibited_wording": "The leaderboard identifies the batters with the best eyes.",
    },
    {
        "claim": "Adjusted recognition showed temporal repeatability within the season.",
        "status": "SUPPORTED_WITH_QUALIFICATION",
        "sprint4_evidence": "168 supported batters; split-half Spearman 0.474 (95% interval 0.333 to 0.592), Pearson 0.561 (0.417 to 0.669).",
        "publication_safe_wording": "Adjusted recognition showed moderate within-season repeatability.",
        "limitations": "Ordered halves are not separate seasons; repeatability is not permanence or determinism.",
        "prohibited_wording": "Recognition is a stable, permanent trait.",
    },
    {
        "claim": "Raw recognition rate is not equivalent to adjusted recognition.",
        "status": "SUPPORTED",
        "sprint4_evidence": "Forty-six ranking-eligible batters moved at least 10 places after opportunity adjustment.",
        "publication_safe_wording": "Raw recognition rate and adjusted recognition answer different questions; opportunity difficulty materially changed some players' standings.",
        "limitations": "The adjusted model is an estimate, not ground truth.",
        "prohibited_wording": "The adjusted ranks reveal the true ordering.",
    },
    {
        "claim": "The batter-history signal was concentrated in moderate misses rather than obvious misses.",
        "status": "SUPPORTED_AS_SENSITIVITY_RESULT",
        "sprint4_evidence": "Moderate misses: log loss -0.011886, Brier -0.004278, ROC AUC +0.019507. Obvious misses: no improvement and only seven supported batters.",
        "publication_safe_wording": "In the prespecified difficulty sensitivity, the predictive gain appeared in moderate misses; the obvious-miss subgroup was too thin to support a strong comparative conclusion.",
        "limitations": "Subgroup evidence is secondary; obvious-miss support is sparse; no mechanism is identified.",
        "prohibited_wording": "Batters differ only on moderate misses, or moderate misses cause the batter effect.",
    },
    {
        "claim": "An adjusted batter-recognition leaderboard may be published.",
        "status": "SUPPORTED_WITH_EDITORIAL_CONTROLS",
        "sprint4_evidence": "Ranking threshold 30 opportunities; empirical-Bayes shrinkage; intervals; boundary rank correlation at least 0.941.",
        "publication_safe_wording": "These are shrinkage-adjusted estimates among batters with at least 30 opportunities; adjacent point ranks are often statistically indistinguishable.",
        "limitations": "Single-season estimates; most adjacent intervals overlap; rank numbers are display order, not proof of separation.",
        "prohibited_wording": "No. 10 is meaningfully better than No. 11 because the point estimate is higher.",
    },
    {
        "claim": "Recognition is a skill.",
        "status": "NOT_SUPPORTED_WITHOUT_QUALIFICATION",
        "sprint4_evidence": "Held-out predictive gain and moderate split-half repeatability support a repeatable component of behavior.",
        "publication_safe_wording": "The results are consistent with a repeatable batter-specific component of recognition behavior.",
        "limitations": "Observed challenge action is not a direct test of perception or innate ability.",
        "prohibited_wording": "ABS recognition is a proven innate skill.",
    },
    {
        "claim": "Recognition is persistent across seasons.",
        "status": "NOT_SUPPORTED",
        "sprint4_evidence": "No multi-season test was conducted.",
        "publication_safe_wording": "Whether the differences persist across seasons remains unknown.",
        "limitations": "Only within-season ordered halves and one future holdout are available.",
        "prohibited_wording": "The best recognizers will remain the best in future seasons.",
    },
    {
        "claim": "Batter vision, experience, plate discipline, coaching, confidence, cognition, or innate ability causes the effect.",
        "status": "NOT_SUPPORTED",
        "sprint4_evidence": "Sprint 4 did not test causal mechanisms.",
        "publication_safe_wording": "The analysis does not identify why batter histories differ.",
        "limitations": "Identity effects can proxy multiple measured and unmeasured processes.",
        "prohibited_wording": "The effect is caused by superior eyesight, discipline, experience, coaching, confidence, or intelligence.",
    },
]


SOURCES = [
    {
        "outlet": "Baseball Savant / MLB",
        "title": "ABS Challenge Leaderboard",
        "url": "https://baseballsavant.mlb.com/leaderboard/abs-challenges",
        "accessed": "2026-09-20",
        "status": "ACCESSIBLE",
        "prior_work_established": "Public player challenge rates and actual-versus-expected challenges/overturns using pitch location, inventory, runners, count, and outs.",
        "pascal_boundary": "Pascal must not claim to invent context adjustment or player ABS leaderboards; its narrower addition is the held-out value of point-in-time batter history among legal incorrect-called-strike opportunities.",
    },
    {
        "outlet": "Baseball Savant / MLB",
        "title": "ABS Metrics Documentation",
        "url": "https://baseballsavant.mlb.com/abs-metrics-documentation",
        "accessed": "2026-09-20",
        "status": "ACCESSIBLE",
        "prior_work_established": "Official definitions for challenge opportunities, reasonable opportunities, confidence, expected metrics, and challenge-skill/run-value decompositions.",
        "pascal_boundary": "Use official terminology as context, but keep Pascal's frozen recognition contract and avoid treating official use of 'skill' as validation of Pascal's behavioral mechanism.",
    },
    {
        "outlet": "MLB.com",
        "title": "There's loads of ABS data from last season. What does it all mean?",
        "url": "https://www.mlb.com/news/abs-challenge-system-statistical-breakdown-2025",
        "accessed": "2026-09-20",
        "status": "ACCESSIBLE",
        "prior_work_established": "Triple-A challenge rates, success rates, count/inning patterns, player spreads, and context-adjusted expected overturns were publicly discussed before Article 3.",
        "pascal_boundary": "Do not claim first evidence of player differences or first adjustment for opportunity context.",
    },
    {
        "outlet": "FanGraphs",
        "title": "Who's Getting Their Money's Worth From the ABS Challenge System?",
        "url": "https://blogs.fangraphs.com/whos-getting-their-moneys-worth-from-the-abs-challenge-system/",
        "accessed": "2026-09-20",
        "status": "ACCESSIBLE",
        "prior_work_established": "Player and team challenge value, success, and rankings framed through run value and the limited deployment of the skill.",
        "pascal_boundary": "Pascal's outcome is recognition action on actual legal misses, not realized challenge value or success.",
    },
    {
        "outlet": "SABR Analytics Conference",
        "title": "When to Challenge a Pitch? A Reinforcement Learning Approach to ABS Challenge Strategy",
        "url": "https://sabr.org/analytics/presentations",
        "accessed": "2026-09-20",
        "status": "ACCESSIBLE_ABSTRACT",
        "prior_work_established": "A held-out, sequential decision framework for challenge strategy using simulated ABS opportunities and run optimization.",
        "pascal_boundary": "Article 3 is not a normative strategy or inventory-optimization study.",
    },
    {
        "outlet": "Baseball-Reference",
        "title": "2026 MLB Automated Ball-Strike Challenge Analysis",
        "url": "https://www.baseball-reference.com/friv/abs-challenges.shtml",
        "accessed": "2026-09-20",
        "status": "INDEXED_BUT_PAGE_BLOCKED",
        "prior_work_established": "A public descriptive ABS challenge analysis and player/team reference surface exists.",
        "pascal_boundary": "Do not imply comprehensive review of inaccessible methodology; acknowledge the public descriptive landscape.",
    },
    {
        "outlet": "TapToChallenge",
        "title": "ABS Player Metrics",
        "url": "https://www.taptochallenge.com/players",
        "accessed": "2026-09-20",
        "status": "ACCESSIBLE",
        "prior_work_established": "Independent player decision-quality and expected-aggressiveness metrics are already public.",
        "pascal_boundary": "Pascal's differentiation is its accepted population, future prediction test, shrinkage, and frozen evidence chain—not the existence of a player metric.",
    },
    {
        "outlet": "ABS Charts",
        "title": "The Full Story — The ABS Challenge",
        "url": "https://abscharts.com/writeup/the-full-story/",
        "accessed": "2026-09-20",
        "status": "ACCESSIBLE",
        "prior_work_established": "Independent season-scale work has quantified missed calls, unchallenged value, challenge success, and team value.",
        "pascal_boundary": "Do not claim first season-scale ABS audit or first analysis of unchallenged misses.",
    },
    {
        "outlet": "SSRN working paper",
        "title": "Avoiding Being Caught: Strike Calling in the ABS Era",
        "url": "https://doi.org/10.2139/ssrn.7242822",
        "accessed": "2026-09-20",
        "status": "ABSTRACT_ACCESSIBLE",
        "prior_work_established": "Academic work studies how the challenge regime changes umpire behavior and strategic incentives.",
        "pascal_boundary": "It addresses umpire response and system incentives, not Pascal's batter-history prediction estimand.",
    },
    {
        "outlet": "arXiv / FAccT",
        "title": "Inside Baseball: The Automated Ball-Strike System as an Object Lesson in Technological Rule Enforcement",
        "url": "https://arxiv.org/abs/2605.16237",
        "accessed": "2026-09-20",
        "status": "ACCESSIBLE",
        "prior_work_established": "ABS is a sociotechnical implementation whose ground truth and operational design require qualification.",
        "pascal_boundary": "Supports careful language about reconstructed geometry and behavior, but does not test batter recognition effects.",
    },
    {
        "outlet": "Baseball Prospectus",
        "title": "Targeted ABS recognition/challenge search",
        "url": "https://www.baseballprospectus.com/",
        "accessed": "2026-09-20",
        "status": "NO_DIRECTLY_RELEVANT_ACCESSIBLE_RESULT_IDENTIFIED",
        "prior_work_established": "No directly relevant accessible player-recognition study was identified in the targeted search.",
        "pascal_boundary": "This is not evidence of absence and must not support a priority claim.",
    },
]


FIGURE_POLICY = [
    {"figure": "Raw vs adjusted recognition", "decision": "INCLUDE", "article_use": "Primary explanatory figure", "publication_rule": "Plot all 243 publication-eligible batters; encode opportunity support; show uncertainty; explain that adjustment is model-based."},
    {"figure": "Temporal stability", "decision": "INCLUDE", "article_use": "Evidence and guardrail for repeatability", "publication_rule": "Use 168 supported batters and print Spearman 0.474 with its 0.333–0.592 interval; avoid a permanent-skill caption."},
    {"figure": "Adjusted leaderboard", "decision": "OPTIONAL", "article_use": "Top-10 table or compact interval plot", "publication_rule": "Main article: at most top 10. Download: frozen top 25. Always retain opportunities, raw/expected rates, shrinkage estimate, and interval; ranks are point-order only."},
    {"figure": "Player case-study comparison", "decision": "INCLUDE", "article_use": "Explain why adjustment changes interpretation", "publication_rule": "Use only Harper, Kurtz, and Aranda from the accepted artifact; show intervals and avoid negative ability labels."},
]


GATES = [
    {"gate": "Methodology", "result": "PASS", "basis": "Accepted Sprint 4 methods and artifacts were verified and left unchanged."},
    {"gate": "Claim Accuracy", "result": "PASS", "basis": "The final claims matrix restricts claims to future prediction, adjusted behavior, and moderate within-season repeatability."},
    {"gate": "Uncertainty Communication", "result": "PASS", "basis": "Publication policy requires opportunity counts, shrinkage, intervals, and explicit treatment of overlapping adjacent ranks."},
    {"gate": "Leaderboard Publication", "result": "PASS", "basis": "A top-10 article display and frozen top-25 download are supportable under the specified controls; bottom rankings are omitted."},
    {"gate": "Prior-Work Positioning", "result": "PASS", "basis": "The memo credits official, journalistic, independent, SABR, and academic work and makes no priority claim."},
    {"gate": "Novelty / Differentiation", "result": "PASS", "basis": "Differentiation is limited to the held-out batter-history test inside Pascal's accepted population and evidence architecture."},
    {"gate": "Figure Data", "result": "PASS", "basis": "Every publication figure dataset is a byte-identical frozen copy of an accepted Sprint 4 artifact."},
    {"gate": "Article 3", "result": "READY_TO_DRAFT", "basis": "The quantitative basis, claims, uncertainty rules, positioning, and frozen data are publication-ready; drafting remains a separate step."},
]


CASE_POLICY = [
    {"batter": "Bryce Harper", "decision": "USE", "role": "Strong positive adjusted example", "editorial_note": "State 31 opportunities and the wide interval; do not generalize beyond the snapshot or call the result eyesight."},
    {"batter": "Nick Kurtz", "decision": "USE", "role": "Opportunity-adjustment example", "editorial_note": "His adjusted interval spans zero. Use to show a raw standing can decline after adjustment, not as a negative recognizer."},
    {"batter": "Jonathan Aranda", "decision": "USE", "role": "Near-expectation comparison", "editorial_note": "Use as the neutral comparator; his adjusted interval spans zero."},
]


POSITIONING = """# Article 3 Positioning and Prior-Work Memo

## Publication decision

Article 3 is **READY_TO_DRAFT** around one claim: historical batter recognition behavior improved prediction of future recognition after the accepted opportunity model accounted for measured geometry and situation. This is a predictive behavioral result, not a test of eyesight, cognition, plate discipline, or causation.

## Where this article fits

- Article 1, *One in Five: Inside the ABS Recognition Gap*, established the opportunity funnel and the size of the recognition gap.
- Article 2, *The Challenge Threshold*, established how geometry and situation shape whether an opportunity is recognized.
- Article 3 asks whether batter history adds prospective information after those measured opportunity characteristics are held constant.

## Prior work and differentiation

Official [Baseball Savant leaderboards](https://baseballsavant.mlb.com/leaderboard/abs-challenges) already publish player challenge rates and actual-versus-expected metrics using location and game context, and its [metrics documentation](https://baseballsavant.mlb.com/abs-metrics-documentation) explicitly defines challenge opportunities and challenge-skill measures. MLB has publicly described Triple-A player spreads and context-adjusted expected results. FanGraphs and independent sites have examined player rankings, run value, missed opportunities, and decision quality. SABR work has modeled optimal challenge strategy. Academic work has studied umpire incentives and ABS as a sociotechnical system.

Pascal should therefore make no “first,” “only,” or “nobody has studied this” claim. The defensible contribution is the combination of: a frozen population limited to legal incorrect-called-strike opportunities; an accepted opportunity-difficulty model; a point-in-time batter history feature; a future temporal holdout; empirical-Bayes shrinkage; ordered split-half stability; boundary, support, and difficulty sensitivity; and a pre-draft claims audit.

## Novelty statement approved for use

“Building on official and independent ABS challenge metrics, Pascal tested a narrower prospective question: within legal incorrect-called-strike opportunities, did a batter’s prior recognition behavior improve prediction of what he would do next after measured opportunity difficulty was accounted for?”

## Language not approved

Do not claim that Pascal invented context-adjusted challenge metrics, created the first player leaderboard, proved a new innate skill, identified the best eyes in baseball, or established multi-season persistence.
"""


LANGUAGE = """# Skill-Language Decision

## Decision

Prefer **recognition behavior**, **batter-specific recognition tendency**, or **repeatable component of recognition behavior**.

The unqualified noun **skill** should not appear in the title, headline, chart title, leaderboard label, or declarative conclusion. It may appear only in a question (“Is this a skill?”) or in a sentence that immediately supplies the qualification: the data show future predictive information and moderate within-season repeatability, but the observed outcome is challenge action and the mechanism is unknown.

“Recognition” is the accepted research label, but every methodology treatment should define it as a legal challenge action on an eligible incorrect called strike. A batter may perceive an error and decline to challenge; coaching, timing, inventory judgment, or other unmeasured factors may contribute. The evidence supports individual differences in behavior, not direct measurement of perception.
"""


LEADERBOARD = """# Leaderboard and Bottom-Ranking Policy

## Adjusted leaderboard

Publication is supportable with controls. The article should show **no more than the top 10** ranking-eligible batters. A downloadable table may retain the accepted top 25. Every display must include opportunities, recognized opportunities, raw rate, expected rate, shrinkage-adjusted estimate, and uncertainty interval. A note must state that the 30-opportunity threshold is evidence-driven, empirical-Bayes shrinkage protects against small samples, and most adjacent intervals overlap.

Rank numbers are a sorting aid. Prose may identify a strongly supported positive estimate, but it may not infer that neighboring positions are meaningfully different. The full 123-player ranking-eligible table remains research support, not an article-length public ranking.

## Bottom rankings

**OMIT PUBLIC BOTTOM RANKINGS.** Sprint 4's `SUPPORTED_WITH_CAUTION` gate permits consideration, not an editorial obligation. Negative characterization carries a higher burden, many intervals overlap zero or one another, and the outcome mixes action with perception and unmeasured strategy. Do not print a bottom table, “worst recognizer” label, or named negative roundup.

Nick Kurtz may appear only as an adjustment case: his estimate is near zero and its interval spans zero. He is not evidence for a negative ability claim.
"""


CASES = """# Case-Study Recommendations

Use the three accepted Sprint 4 examples; do not add players.

- **Bryce Harper:** 31 opportunities, 21 recognized, 67.7% raw versus 20.6% expected, adjusted +36.7 percentage points (interval +22.3 to +50.2). Use as the strongly positive adjusted example, while foregrounding the modest opportunity count and uncertainty.
- **Nick Kurtz:** 39 opportunities, 9 recognized, 23.1% raw versus 26.6% expected, adjusted -3.0 points (-12.0 to +8.2). Use to explain that adjustment can lower a raw standing; do not call him a poor recognizer.
- **Jonathan Aranda:** 43 opportunities, 9 recognized, 20.9% raw versus 20.4% expected, adjusted approximately 0.0 points (-8.7 to +11.3). Use as the well-supported near-expectation comparison.

These examples form an explanatory contrast—strong positive, adjustment-driven reinterpretation, and league-expectation comparator—without celebrity-based selection or a negative-player frame.
"""


STRUCTURE = """# Article 3 Title and Structure Recommendations

## Recommended title

**Beyond Challenge Rate: What Batter History Adds**

## Alternatives

1. **Who Recognizes the Miss? Adjusting ABS Challenges for Opportunity**
2. **The Batter Signal in ABS Recognition**
3. **After the Challenge Threshold: Do Batter Differences Repeat?**
4. **What Raw ABS Challenge Rates Miss**

Avoid “Baseball's Best Eyes,” “The Best and Worst ABS Challengers,” and unqualified “Recognition Skill” titles.

## Recommended structure

1. Bridge from Article 1's one-in-five gap and Article 2's opportunity threshold.
2. Explain why raw recognition rate is confounded by opportunity difficulty.
3. State the prospective test: accepted baseline versus point-in-time batter history on future opportunities.
4. Report the held-out metric improvements, with log loss and Brier first and AUC as supporting discrimination.
5. Show raw versus adjusted recognition and the three player cases.
6. Present moderate within-season split-half repeatability.
7. Localize the sensitivity result to moderate misses without turning it into a mechanism claim.
8. If space permits, show the controlled top-10 adjusted table.
9. Close with what the study cannot tell us: perception, cause, permanence, and future seasons.

The article should not lead with Harper or the leaderboard. The held-out comparison is the article's evidentiary spine.
"""


METHODS = """# Methodology Disclosure and Limitations Notes

## Required methodology box

- Snapshot: accepted Sprint 4, covering 2026-03-25 through 2026-09-09.
- Population: 10,755 legal incorrect-called-strike opportunities; 2,112 recognized; 602 batters.
- Outcome: `recognized = 1` only when the batter challenged the eligible opportunity; challenge success and outcome are not used.
- Baseline: accepted Sprint 3 situation model with approved non-batter geometry and context features.
- Batter information: only prior recognition history available before each opportunity; minimum 20 prior opportunities in the primary predictive model.
- Temporal test: train through July 31; final holdout August 1–September 9; 2,830 holdout opportunities.
- Adjustment: empirical-Bayes normal random effect with shrinkage; publication threshold 20 opportunities and ranking threshold 30.
- Held-out result: log loss 0.43033 to 0.41757; Brier 0.13598 to 0.13142; ROC AUC 0.75399 to 0.77286.
- Stability: 168 batters with at least 10 opportunities in each ordered half; Spearman 0.474 (0.333–0.592).

## Required limitations

The analysis covers one partial MLB season and cannot establish multi-season persistence. Challenge action is a behavioral outcome, not a direct perception test. Batter identity may proxy coaching, team policy, confidence, timing, communication, or unmeasured pitch and game context. The baseline controls only accepted measured features. Intervals quantify estimate uncertainty under the accepted model but do not exhaust model uncertainty. The moderate-miss result is a subgroup sensitivity; the obvious-miss subgroup has only seven supported batters. Adjacent leaderboard ranks usually overlap and must not be narrated as distinct tiers. Results describe the accepted snapshot and should not be projected automatically to a different ABS zone, rule set, or season.
"""


ADVERSARIAL = """# Adversarial Publication Review

## Attempts to narrow or invalidate the narrative

1. **Challenge action could be mistaken for perception.** This challenge succeeds as a warning: the outcome cannot reveal whether a batter saw the miss but declined to act. Publication language is restricted to recognition behavior as operationally defined.
2. **Identity could be mistaken for cause.** This challenge succeeds. Batter history adds prediction, but identity does not identify vision, discipline, experience, coaching, confidence, or cognition.
3. **In-sample fit could create a false player signal.** The finding survives the future holdout, improving log loss, Brier score, and ROC AUC. This challenge does not invalidate the central predictive claim.
4. **Boundary-adjacent pitches could drive the result.** Predictive improvement survives every accepted exclusion through 0.5 inches, and ranking correlations remain at least 0.941. This challenge fails to remove the finding.
5. **Small samples and extreme players could create the leaderboard.** Empirical-Bayes shrinkage, support thresholds, and sensitivity analyses reduce this risk, but player-level intervals remain wide. The leaderboard is supportable only with the stated controls.
6. **Moderate repeatability could be sold as permanent skill.** The split-half association is moderate, not deterministic, and no cross-season evidence exists. Any permanence claim is rejected.
7. **Point ranks could imply meaningful separation.** Most adjacent intervals overlap. The article may use point order only as navigation and may not convert it into head-to-head claims.
8. **The result might be driven by obvious misses.** It is not: the predictive gain is concentrated in the moderate group. However, sparse obvious-miss support prevents a strong “no effect” conclusion there.
9. **The result might disappear under stricter history support.** The primary 20-history model improves all headline metrics; the 30-history version retains only small gains. This narrows the claim: historical information is useful at the selected evidence-based threshold, not uniformly strong under every restriction.
10. **Prior work might erase the novelty.** It erases broad priority claims about adjusted ABS player metrics. It does not erase Pascal's narrower prospective estimand and validation design.

## Editorial conclusion

The central narrative survives only in its narrow form: prior batter behavior adds modest but consistent future predictive information beyond the accepted opportunity model, and adjusted effects show moderate within-season repeatability. The evidence does not support a perception mechanism, permanent trait, exact ordinal hierarchy, or public negative ranking.
"""


REPORT = """# ABS Article 3 — Publication Validation Report

## Decision

**Article 3: READY_TO_DRAFT.** The accepted Sprint 4 evidence supports a narrowly framed article about the prospective information in historical batter recognition behavior after measured opportunity difficulty is accounted for. It does not support claims about eyesight, causation, innate ability, or multi-season persistence.

| Gate | Result |
|---|---|
| Methodology | PASS |
| Claim Accuracy | PASS |
| Uncertainty Communication | PASS |
| Leaderboard Publication | PASS |
| Prior-Work Positioning | PASS |
| Novelty / Differentiation | PASS |
| Figure Data | PASS |
| Article 3 | **READY_TO_DRAFT** |

## Core publication finding

On the final temporal holdout, adding point-in-time batter history improved log loss from 0.43033 to 0.41757, Brier score from 0.13598 to 0.13142, and ROC AUC from 0.75399 to 0.77286. Among 168 batters with support in both ordered halves, adjusted recognition had a Spearman correlation of 0.474 (95% interval 0.333 to 0.592). The publication-safe interpretation is that historical batter behavior contains modest prospective information beyond measured opportunity characteristics and shows moderate within-season repeatability.

## Editorial controls

- Use “recognition behavior,” not unqualified “skill.”
- Define recognition as challenge action, not perception.
- Lead with the held-out model comparison, not a player ranking.
- Limit the article leaderboard to the top 10; retain the frozen top 25 as downloadable data.
- Show opportunities, shrinkage-adjusted estimates, intervals, and overlap caveats.
- Omit bottom rankings and all “worst” labels.
- Use only the accepted Harper, Kurtz, and Aranda case studies.
- Describe the moderate-miss pattern as secondary sensitivity evidence.
- Make no priority claim over Savant's contextual expected metrics or existing player ABS analyses.

## Figure decisions

- Raw versus adjusted recognition: **INCLUDE**.
- Temporal stability: **INCLUDE**.
- Adjusted leaderboard: **OPTIONAL**; top 10 maximum in the article.
- Player case-study comparison: **INCLUDE**.

## Boundary

This package authorizes drafting preparation only. It does not draft Article 3, create branded graphics, alter Sprint 4, or authorize publication.
"""


def verify_upstream(root: Path) -> tuple[dict, dict]:
    sprint4 = root / "artifacts/sprint4"
    manifest_path = sprint4 / "run_manifest.json"
    if sha256(manifest_path) != ACCEPTED_SPRINT4_MANIFEST_SHA256:
        raise RuntimeError("Accepted Sprint 4 manifest hash mismatch")
    if sha256(sprint4 / "artifact_hashes.sha256") != ACCEPTED_SPRINT4_HASH_LIST_SHA256:
        raise RuntimeError("Accepted Sprint 4 hash-list mismatch")
    manifest = json.loads(manifest_path.read_text())
    if manifest["accepted_sprint3"]["accepted_manifest_sha256"] != ACCEPTED_SPRINT3_MANIFEST_SHA256:
        raise RuntimeError("Sprint 3 inheritance mismatch")
    actual = {}
    for rel, expected in sorted(manifest["output_artifact_hashes"].items()):
        path = root / rel
        observed = sha256(path)
        if observed != expected:
            raise RuntimeError(f"Immutable Sprint 4 artifact mismatch: {rel}")
        actual[rel] = observed
    return manifest, actual


def run(root: Path) -> None:
    manifest, upstream_before = verify_upstream(root)
    docs = root / "docs/publication_validation/article3"
    artifacts = root / "artifacts/publication_validation/article3"
    figures = artifacts / "figure_data"
    figures.mkdir(parents=True, exist_ok=True)

    write_text(docs / "publication_validation_report.md", REPORT)
    write_text(docs / "positioning_prior_work.md", POSITIONING)
    write_text(docs / "skill_language_decision.md", LANGUAGE)
    write_text(docs / "leaderboard_policy.md", LEADERBOARD)
    write_text(docs / "case_studies.md", CASES)
    write_text(docs / "title_article_structure.md", STRUCTURE)
    write_text(docs / "methodology_limitations.md", METHODS)
    write_text(docs / "adversarial_review.md", ADVERSARIAL)
    write_text(docs / "final_publication_claims_matrix.md", claims_markdown(CLAIMS))

    write_csv_json(artifacts / "final_publication_claims_matrix", CLAIMS)
    write_csv_json(artifacts / "source_inventory", SOURCES)
    write_csv_json(artifacts / "figure_policy", FIGURE_POLICY)
    write_csv_json(artifacts / "publication_gates", GATES)
    write_csv_json(artifacts / "case_study_policy", CASE_POLICY)

    frozen_sources = {
        "figure1_raw_vs_adjusted": "artifacts/sprint4/figure1_raw_vs_adjusted",
        "figure2_temporal_stability": "artifacts/sprint4/figure2_temporal_stability",
        "figure3_adjusted_leaderboard": "artifacts/sprint4/figure3_adjusted_leaderboard",
        "figure4_case_studies": "artifacts/sprint4/figure4_case_studies",
    }
    frozen_map = []
    for name, source_base in frozen_sources.items():
        for suffix in (".csv", ".json"):
            source_rel = source_base + suffix
            source = root / source_rel
            destination = figures / (name + suffix)
            shutil.copyfile(source, destination)
            if sha256(source) != sha256(destination):
                raise RuntimeError(f"Frozen figure mismatch: {name}{suffix}")
            frozen_map.append({
                "publication_artifact": str(destination.relative_to(root)),
                "sprint4_source": source_rel,
                "sha256": sha256(destination),
                "byte_identical": True,
            })
    write_csv_json(artifacts / "frozen_figure_source_map", frozen_map)

    # Verify every accepted Sprint 4 output again after all publication writes.
    _, upstream_after = verify_upstream(root)
    if upstream_before != upstream_after:
        raise RuntimeError("Sprint 4 changed during publication validation")

    integrity = {
        "status": "VERIFIED_UNCHANGED",
        "accepted_sprint4_manifest": "artifacts/sprint4/run_manifest.json",
        "accepted_sprint4_manifest_sha256": ACCEPTED_SPRINT4_MANIFEST_SHA256,
        "accepted_sprint4_hash_list_sha256": ACCEPTED_SPRINT4_HASH_LIST_SHA256,
        "accepted_sprint3_manifest_sha256": ACCEPTED_SPRINT3_MANIFEST_SHA256,
        "verified_sprint4_outputs": len(upstream_after),
        "population": manifest["accepted_sprint3"]["population"],
    }
    (artifacts / "upstream_integrity.json").write_text(json.dumps(integrity, indent=2) + "\n")

    manifest_path = artifacts / "run_manifest.json"
    output_paths = sorted(
        p for p in list(docs.rglob("*")) + list(artifacts.rglob("*"))
        if p.is_file() and p != manifest_path and p.name not in {"artifact_hashes.sha256"}
    )
    outputs = {str(p.relative_to(root)): sha256(p) for p in output_paths}
    validation_manifest = {
        "package": "ABS Article 3 publication validation",
        "status": "READY_TO_DRAFT",
        "execution_date": "2026-09-20",
        "upstream": integrity,
        "publication_decisions": {
            "skill_language": "QUALIFIED_ONLY_PREFER_RECOGNITION_BEHAVIOR",
            "leaderboard": "PASS_TOP_10_ARTICLE_TOP_25_DOWNLOAD",
            "bottom_rankings": "OMIT",
            "case_studies": ["Bryce Harper", "Nick Kurtz", "Jonathan Aranda"],
        },
        "gates": {row["gate"]: row["result"] for row in GATES},
        "output_artifact_hashes": outputs,
    }
    manifest_path.write_text(json.dumps(validation_manifest, indent=2, ensure_ascii=False) + "\n")

    hash_paths = output_paths + [manifest_path]
    hash_text = "".join(f"{sha256(p)}  {p.relative_to(root)}\n" for p in sorted(hash_paths))
    (artifacts / "artifact_hashes.sha256").write_text(hash_text)


if __name__ == "__main__":
    run(Path(__file__).resolve().parents[1])
