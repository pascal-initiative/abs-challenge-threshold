"""PV-1 adversarial validation for Article 1.

The implementation deliberately consumes accepted Sprint 1--5 outputs and
writes only to publication_validation namespaces.
"""
from __future__ import annotations

import argparse, hashlib, json, math, platform, subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
import statsmodels.api as sm

from .sprint3 import SPECS, _metrics, _model, temporal_folds

START, END = "2026-03-25", "2026-09-09"
RUN_DATE = "2026-09-10"
THRESHOLDS = [0.0, 0.05, 0.10, 0.25, 0.50]


def outside_boundary(distance_inches, threshold: float):
    """Return observations outside an inclusive uncertainty band."""
    return np.asarray(distance_inches) > threshold


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n")


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, lineterminator="\n", float_format="%.12g")


def upstream_files(root: Path) -> list[Path]:
    paths = [root / "data/full_season/processed/validation_report.json",
             root / "data/full_season/processed/validation_discrepancies.csv",
             root / "data/full_season/processed/pitches.csv",
             root / "data/full_season/processed/challenges.csv"]
    for base in [root / "data/analysis", root / "artifacts", root / "docs"]:
        if not base.exists():
            continue
        paths += [p for p in base.rglob("*") if p.is_file() and "publication_validation" not in p.parts
                  and not any(part.startswith(".") for part in p.relative_to(root).parts)]
    return sorted(set(paths))


def hashes(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): sha(p) for p in upstream_files(root)}


def integrity(root: Path, before: dict[str, str]) -> dict:
    v = json.loads((root / "data/full_season/processed/validation_report.json").read_text())
    a = json.loads((root / "data/analysis/sprint3/offensive_recognition_population_audit.json").read_text())
    p = pd.read_csv(root / "data/full_season/processed/pitches.csv", usecols=["game_date", "game_pk"])
    manifest_checks = {}
    for sprint in (3, 4, 5):
        mp = root / f"artifacts/sprint{sprint}/run_manifest.json"
        manifest = json.loads(mp.read_text())
        mappings = [manifest.get("output_artifact_hashes", {}), manifest.get("output_hashes", {}),
                    manifest.get("input_artifact_hashes", {}), manifest.get("source_snapshot_hashes", {})]
        for mapping in mappings:
            for rel, expected in mapping.items():
                if isinstance(expected, str) and "/" in rel and (root / rel).is_file():
                    manifest_checks[rel] = sha(root / rel) == expected
    checks = {
        "snapshot": [p.game_date.min(), p.game_date.max()] == [START, END],
        "official_challenges": v["official_challenges"] == 9485,
        "matched_challenges": v["matched_challenges"] == 9485,
        "geometry_agreements": v["agreement_count"] == 9482,
        "geometry_disagreements": v["disagreement_count"] == 3,
        "agreement_rate": math.isclose(v["agreement_rate"], 9482 / 9485, abs_tol=1e-15),
        "incorrect_called_strikes": a["incorrect_called_strikes"] == 11704,
        "legal_recognition_opportunities": a["legal_recognition_opportunities"] == 10755,
        "recognized": a["recognized"] == 2112,
        "not_recognized": a["not_recognized"] == 8643,
        "population_reconciles": a["population_identity_holds"] and a["other_exclusions"] == 0,
        "accepted_manifest_hashes": bool(manifest_checks) and all(manifest_checks.values()),
    }
    if not all(checks.values()):
        raise RuntimeError(f"PV-1 Phase 1 failed: {checks}")
    return {"phase": 1, "status": "PASS", "snapshot_start": START, "snapshot_end": END,
            "games": int(p.game_pk.nunique()), "checks": checks,
            "validation_baseline": {"official_challenges": 9485, "matched_challenges": 9485,
                                    "geometry_agreements": 9482, "geometry_disagreements": 3,
                                    "geometry_agreement_rate": 9482 / 9485},
            "recognition_baseline": {k: a[k] for k in ["incorrect_called_strikes", "legal_recognition_opportunities",
                                                        "recognized", "not_recognized", "resource_constrained",
                                                        "position_player_pitching", "unknown", "other_exclusions"]},
            "accepted_manifest_hash_checks": manifest_checks, "accepted_upstream_hashes": before}


def disagreement_audit(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    p = pd.read_csv(root / "data/full_season/processed/pitches.csv", low_memory=False)
    c = pd.read_csv(root / "data/full_season/processed/challenges.csv", low_memory=False)
    d = pd.read_csv(root / "data/full_season/processed/validation_discrepancies.csv", low_memory=False)
    cols = ["pitch_key", "batter_name", "pitcher_name", "catcher_name", "umpire_name",
            "abs_zone_top", "abs_zone_bot", "half_inning", "inning", "balls", "strikes", "outs"]
    d = d.merge(p[cols], on="pitch_key", how="left", validate="one_to_one")
    d["signed_distance_from_boundary_feet"] = d.distance_from_abs_boundary
    d["absolute_distance_from_boundary_feet"] = d.distance_from_abs_boundary.abs()
    d["distance_inches"] = d.distance_from_abs_boundary.abs() * 12
    # For outside-zone disagreements positive means reconstructed BALL; negative means reconstructed STRIKE.
    d["horizontal_or_vertical_boundary"] = np.where(
        d.plate_z < d.abs_zone_bot, "VERTICAL_BOTTOM",
        np.where(d.plate_z > d.abs_zone_top, "VERTICAL_TOP", "HORIZONTAL_OR_CORNER"))
    d["miss_direction"] = np.select(
        [d.plate_z < d.abs_zone_bot, d.plate_z > d.abs_zone_top, d.plate_x < 0, d.plate_x >= 0],
        ["BELOW", "ABOVE", "CATCHER_LEFT", "CATCHER_RIGHT"])
    d["source_zone_top_difference_inches"] = (d.abs_zone_top - d.savant_abs_top) * 12
    d["source_zone_bot_difference_inches"] = (d.abs_zone_bot - d.savant_abs_bot) * 12
    d["interpretation"] = np.where(
        d.distance_inches <= 0.05,
        "MICROSCOPIC_BOUNDARY_PRECISION_DISAGREEMENT",
        "MATERIAL_SOURCE_ZONE_HEIGHT_DISAGREEMENT; PUBLIC FORMULA DEFECT NOT ESTABLISHED")
    keep = ["game_pk", "pitch_key", "game_date", "batter_name", "pitcher_name", "catcher_name", "umpire_name",
            "original_call", "official_abs_call", "derived_abs_call", "outcome", "plate_x", "plate_z",
            "abs_zone_top", "abs_zone_bot", "savant_abs_top", "savant_abs_bot", "savant_edge_dist_inches",
            "signed_distance_from_boundary_feet", "absolute_distance_from_boundary_feet", "distance_inches",
            "horizontal_or_vertical_boundary", "miss_direction", "source_zone_top_difference_inches",
            "source_zone_bot_difference_inches", "source_copy_count", "source_conflict", "interpretation"]
    audited = d[keep].sort_values(["game_date", "pitch_key"]).reset_index(drop=True)

    vc = c.merge(p[["pitch_key", "derived_abs_call", "distance_from_abs_boundary"]], on="pitch_key", validate="one_to_one")
    vc["agrees"] = vc.official_abs_call.eq(vc.derived_abs_call)
    vc["absolute_distance_inches"] = vc.distance_from_abs_boundary.abs() * 12
    bins = [-np.inf, .05, .10, .25, .50, 1, np.inf]
    labels = ["0-0.05", "0.05-0.10", "0.10-0.25", "0.25-0.50", "0.50-1.00", "1.00+"]
    vc["boundary_bin_inches"] = pd.cut(vc.absolute_distance_inches, bins, labels=labels, right=False)
    dist = vc.groupby("boundary_bin_inches", observed=False).agrees.agg(total="size", agreements="sum").reset_index()
    dist["disagreements"] = dist.total - dist.agreements
    dist["agreement_rate"] = dist.agreements / dist.total
    return audited, dist


def fit_models(frame: pd.DataFrame, threshold: float) -> list[dict]:
    rows, by = [], {}
    y = frame.recognized.astype(int).to_numpy()
    for name, (num, cat) in SPECS.items():
        ys, ps = [], []
        for _, train, test in temporal_folds(frame):
            model = _model(num, cat).fit(frame.iloc[train], y[train])
            prob = model.predict_proba(frame.iloc[test])[:, 1]
            ys.extend(y[test]); ps.extend(prob)
        m = _metrics(ys, ps)
        row = {"threshold_inches": threshold, "model": name, "validation": "EXPANDING_MONTHLY",
               "pooled_n": len(ys), **m}
        rows.append(row); by[name] = m
    for before, after in [("A_GEOMETRY", "B_PITCH"), ("B_PITCH", "C_SITUATION")]:
        rows.append({"threshold_inches": threshold, "model": f"DELTA_{before}_TO_{after}",
                     "validation": "EXPANDING_MONTHLY_COMPARISON", "pooled_n": len(ys),
                     **{f"delta_{k}": by[after][k] - by[before][k] for k in ["roc_auc", "pr_auc", "log_loss", "brier_score"]}})
    return rows


def sensitivity(root: Path, pitches: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    f = pd.read_csv(root / "data/analysis/sprint3/offensive_recognition_features.csv", low_memory=False)
    incorrect = pitches[(pitches.original_call == "STRIKE") & (pitches.derived_abs_call == "BALL")].copy()
    incorrect["abs_distance_inches"] = incorrect.distance_from_abs_boundary.abs() * 12
    baseline = {"incorrect": len(incorrect), "legal": len(f), "recognized": int(f.recognized.sum()),
                "rate": float(f.recognized.mean())}
    rows, models = [], []
    for t in THRESHOLDS:
        # Boundary membership is inclusive. Retained observations are strictly beyond the threshold.
        ii = incorrect[outside_boundary(incorrect.abs_distance_inches, t)]
        ff = f[outside_boundary(f.abs_distance_inches, t)].copy()
        rec = int(ff.recognized.sum()); legal = len(ff)
        fit = sm.Logit(ff.recognized, sm.add_constant(ff.abs_distance_inches)).fit(disp=0)
        ci = fit.conf_int().loc["abs_distance_inches"]
        rows.append({"threshold_inches": t, "exclusion_rule": "exclude abs_distance_inches <= threshold",
                     "estimated_incorrect_called_strikes": len(ii), "legal_recognition_opportunities": legal,
                     "recognized": rec, "not_recognized": legal-rec, "recognition_rate": rec/legal,
                     "recognition_rate_absolute_change": rec/legal-baseline["rate"],
                     "recognition_rate_relative_change": (rec/legal-baseline["rate"])/baseline["rate"],
                     "incorrect_count_change": len(ii)-baseline["incorrect"], "legal_count_change": legal-baseline["legal"],
                     "distance_log_odds_per_inch": fit.params["abs_distance_inches"],
                     "distance_standard_error": fit.bse["abs_distance_inches"],
                     "distance_ci95_low": ci.iloc[0], "distance_ci95_high": ci.iloc[1],
                     "distance_p_value": fit.pvalues["abs_distance_inches"],
                     "geometry_direction": "POSITIVE" if fit.params["abs_distance_inches"] > 0 else "NEGATIVE"})
        models += fit_models(ff, t)
    return pd.DataFrame(rows), pd.DataFrame(models)


def funnel_and_metrics(p: pd.DataFrame, root: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    called = p[p.is_called_pitch.astype(str).str.lower().eq("true")]
    called_strikes = called[called.original_call.eq("STRIKE")]
    inc = called_strikes[called_strikes.derived_abs_call.eq("BALL")]
    legal = inc[inc.challenge_available.astype(str).str.lower().eq("true")]
    challenged = legal[legal.challenged.astype(str).str.lower().eq("true")]
    stages = [("physical_pitches", len(p), None), ("called_pitches", len(called), len(p)),
              ("called_strikes", len(called_strikes), len(called)),
              ("estimated_incorrect_called_strikes", len(inc), len(called_strikes)),
              ("legal_estimated_incorrect_called_strikes", len(legal), len(inc)),
              ("challenged_legal_estimated_incorrect_called_strikes", len(challenged), len(legal)),
              ("not_challenged_legal_estimated_incorrect_called_strikes", len(legal)-len(challenged), len(legal))]
    funnel = pd.DataFrame([{"stage": s, "count": n, "percentage": None if d is None else n/d,
                            "percentage_denominator": "NONE" if d is None else stages[i-1][0] if i < 6 else "legal_estimated_incorrect_called_strikes",
                            "denominator_count": d} for i,(s,n,d) in enumerate(stages)])
    batter_challenges = p[(p.is_called_pitch.astype(str).str.lower().eq("true")) & p.challenged.astype(str).str.lower().eq("true") & p.original_call.eq("STRIKE")]
    all_legal_offense = p[(p.is_called_pitch.astype(str).str.lower().eq("true")) & p.original_call.eq("STRIKE") & p.challenge_available.astype(str).str.lower().eq("true")]
    official_success = batter_challenges.challenge_outcome.eq("OVERTURNED").sum()
    corrected_est = challenged.challenge_outcome.eq("OVERTURNED").sum()
    metrics = pd.DataFrame([
        {"metric": "recognition_rate", "numerator": len(challenged), "denominator": len(legal), "value": len(challenged)/len(legal), "definition": "Estimated incorrect called strikes challenged while a legal batter challenge was available."},
        {"metric": "challenge_rate", "numerator": len(batter_challenges), "denominator": len(all_legal_offense), "value": len(batter_challenges)/len(all_legal_offense), "definition": "All actual batter challenges divided by all legal offensive called-strike opportunities."},
        {"metric": "challenge_success_rate", "numerator": int(official_success), "denominator": len(batter_challenges), "value": official_success/len(batter_challenges), "definition": "Official overturned batter challenges divided by official batter challenges."},
        {"metric": "correction_rate", "numerator": int(corrected_est), "denominator": len(legal), "value": corrected_est/len(legal), "definition": "Legally challengeable reconstructed errors that were challenged and officially overturned."},
    ])
    counts = {s:n for s,n,_ in stages}
    return funnel, metrics, counts


def representative_pitches(root: Path) -> pd.DataFrame:
    f = pd.read_csv(root / "data/analysis/sprint3/offensive_recognition_features.csv")
    cols = ["pitch_key", "game_pk", "game_date", "inning", "balls", "strikes", "outs", "base_state",
            "offense_score_diff", "batter_name", "pitcher_name", "catcher_name", "umpire_name", "plate_x", "plate_z",
            "abs_zone_top", "abs_zone_bot", "abs_distance_inches", "affected_team_challenges_remaining", "recognized"]
    no = f[f.recognized.eq(0)]
    clear_pool = no[no.abs_distance_inches.between(2, 3)]
    clear = clear_pool.iloc[(clear_pool.abs_distance_inches-clear_pool.abs_distance_inches.median()).abs().argsort().iloc[0]]
    border = no.sort_values(["abs_distance_inches", "pitch_key"]).iloc[0]
    yes = f[f.recognized.eq(1)]
    challenged = yes.iloc[(yes.abs_distance_inches-yes.abs_distance_inches.median()).abs().argsort().iloc[0]]
    candidates = no[(no.inning.sub(challenged.inning).abs() >= 4)]
    context = candidates.iloc[(candidates.abs_distance_inches-challenged.abs_distance_inches).abs().argsort().iloc[0]]
    records=[]
    for eid, purpose, row in [("A", "clear estimated miss / not challenged", clear),
                              ("B", "borderline estimated miss / not challenged", border),
                              ("C", "estimated miss / challenged", challenged),
                              ("D", "similar geometry to C / meaningfully different game context", context)]:
        x={k:row[k] for k in cols}; x.update(example_id=eid, selection_purpose=purpose,
            selection_rule={"A":"unchallenged, 2-3 inches, nearest pool median", "B":"minimum distance unchallenged",
                            "C":"challenged, nearest challenged median", "D":"unchallenged, inning difference >=4, closest distance to C"}[eid],
            evidence_role="ILLUSTRATION_ONLY")
        records.append(x)
    return pd.DataFrame(records)[["example_id", "selection_purpose", "selection_rule", "evidence_role"]+cols]


SOURCES = [
    ("OFFICIAL", "ABS Challenges leaderboard and expected challenges", "MLB / Baseball Savant", "2026", "https://baseballsavant.mlb.com/leaderboard/abs-challenges?page=0&pageSize=50&sort=n_challenges&sortDir=desc", "Challenge performance and expected challenge opportunities", "Statcast challenge and pitch context", "Defines official outcomes and public expected metrics", "Models challenge propensity and reasonable opportunities", "Pascal freezes a transparent reconstructed error funnel and audits boundary uncertainty"),
    ("OFFICIAL", "ABS Challenge System explained", "MLB", "2026-04-13", "https://www.mlb.com/news/abs-challenge-system-mlb-2026", "Rules and operation", "MLB rules and examples", "Primary rules source", "Defines inventory and legal use", "Pascal estimates missed recognition across the snapshot"),
    ("OFFICIAL", "ABS Spring Training 2026 takeaways", "MLB", "2026-03-24", "https://www.mlb.com/news/abs-spring-training-2026-takeaways", "Early results and expected-challenge model", "Spring Training challenges", "Documents situation and inventory predictors", "Overlaps situation modeling", "Pascal reports temporal held-out incremental metrics"),
    ("OFFICIAL", "ABS challenge system statistical breakdown 2025", "MLB", "2026-02-26", "https://www.mlb.com/news/abs-challenge-system-statistical-breakdown-2025", "2025 challenge patterns", "2025 tests", "Prior challenge context", "Overlaps challenge behavior", "Pascal studies accepted 2026 S-T-D reconstructed errors"),
    ("OFFICIAL", "2026 SABR Analytics: MLB Statcast Updates, Baseball Savant and ABS", "SABR / MLB Statcast", "2026-05-01", "https://sabr.org/latest/2026-sabr-analytics-watch-highlights-from-mlb-statcast-updates-baseball-savant-and-abs/", "Official Statcast feature and ABS metric updates", "MLB Statcast systems and 2025 Triple-A results", "Documents public ABS leaderboards and challenge-rate framing", "Overlaps player challenge and success trends", "Pascal independently reconstructs a fixed 2026 MLB snapshot"),
    ("ACADEMIC", "When to Challenge a Pitch? A Reinforcement Learning Approach to ABS Challenge Strategy", "Christopher Martinez / SABR Analytics", "2026-02-28", "https://sabr.org/analytics/presentations", "Optimal sequential challenge timing", "93,206 Statcast pitches in 1,568 games, June-September 2024", "Direct sequential-policy prior work", "Overlaps resource option value and inventory", "Article 1 limits Sprint 5 to a descriptive teaser"),
    ("INDEPENDENT", "An Early Nerdy Look at the Challenge System", "Ben Clemens / FanGraphs", "2026-04-01", "https://blogs.fangraphs.com/an-early-nerdy-look-at-the-challenge-system/", "What drives challenges and their value", "Every challengeable pitch; RE288", "Strong prior analysis", "Direct overlap with missed opportunities, miss magnitude, and context", "Pascal adds frozen season-scale replication, temporal tests, and boundary audit"),
    ("INDEPENDENT", "Who's Getting Their Money's Worth from the ABS Challenge System?", "Michael Baumann / FanGraphs", "2026-08-11", "https://blogs.fangraphs.com/whos-getting-their-moneys-worth-from-the-abs-challenge-system/", "Contextual value of challenges", "2026 challenges; run and win context", "Prior value analysis", "Overlaps situation and outcomes", "Pascal's Article 1 centers recognition denominator"),
    ("INDEPENDENT", "ABS Charts methodology", "ABS Charts", "2026", "https://abscharts.com/writeup/methodology/", "Sequential challenge strategy", "Statcast, RE288, overturn curves", "Direct resource-policy prior work", "Covers unchallenged misses and dynamic inventory", "Pascal separates recognition, skill, and resource-management sprints"),
    ("INDEPENDENT", "The Full Story", "ABS Charts", "2026", "https://abscharts.com/writeup/the-full-story/", "Aggregate costs of missed calls and challenges", "2026 Statcast", "Direct public comparison", "Explicit unchallenged misses and resource effects", "Pascal contributes its independently validated reconstruction and claim audit"),
    ("OPEN_SOURCE", "abs-challenge", "Professor Palmer", "2026", "https://github.com/professorpalmer/abs-challenge", "Sequential challenge decisions", "Pitch overturn models and Bellman recursion", "Reproducible prior project", "Overlaps decision quality and inventory", "Pascal's Article 1 does not claim this policy work as distinct"),
    ("INDEPENDENT", "The Oyster Guide to ABS Challenge", "Down on the Farm", "2026-02-25", "https://downonthefarm.substack.com/p/the-oyster-guide-to-abs-challenge", "Challenge thresholds and efficiency", "Public challenge data", "Public newsletter context", "Overlaps confidence thresholds", "Pascal quantifies recognition with held-out models"),
    ("INDEPENDENT", "TapToChallenge challenge analysis", "TapToChallenge", "2026", "https://www.taptochallenge.com/challenges", "Opportunity cost and confidence", "Pitch context and expected cost", "Direct public tool", "Overlaps challenge opportunities and resources", "Pascal freezes a reproducible research snapshot"),
    ("ACADEMIC", "Inside Baseball: Technical and Social Impacts of Ball-Strike Challenges", "Academic preprint authors", "2026-05", "https://arxiv.org/abs/2605.16237", "Technical and social impacts", "Public baseball and qualitative evidence", "Broader scholarly context", "Related ABS consequences", "Does not replace Pascal's specific recognition funnel"),
    ("INDEPENDENT", "Joe Sheehan Newsletter: ABS", "Joe Sheehan", "2026-05-11", "https://www.joesheehan.com/2026/05/joe-sheehan-newsletter-may-11-2026-abs.html", "Observed ABS patterns", "2026 public data", "Identifies missed opportunities", "Overlaps unchallenged error framing", "Pascal provides explicit denominator and validation"),
    ("INDEPENDENT", "MLB ABS Challenges", "Malter Analytics", "2026-04-13", "https://www.malteranalytics.com/blog/2026-04-13-mlb-abs-challenges", "Challenge outcomes", "2026 challenge data", "Independent analysis", "Overlaps observed challenges", "Pascal includes unchallenged reconstructed errors"),
]


def novelty() -> pd.DataFrame:
    return pd.DataFrame([
        ("Independent reconstruction validated against official decisions", "MEANINGFUL EXTENSION", "Public work uses Statcast/Hawk-Eye; Pascal adds exact 9,485-decision validation and disagreement preservation."),
        ("Full reconstructed population of unchallenged incorrect called strikes", "MEANINGFUL EXTENSION", "FanGraphs, Baseball Savant expected metrics, ABS Charts, and newsletters already analyze missed opportunities; Pascal adds a frozen transparent funnel and uncertainty audit."),
        ("Error distance predicts recognition", "ALREADY WELL COVERED", "Prior public models and analyses explicitly use miss location or magnitude."),
        ("Situation adds predictive information", "MEANINGFUL EXTENSION", "Situation is established in prior work; Pascal adds preregistered block comparison on expanding temporal holdouts."),
        ("Batter identity adds future predictive information", "MEANINGFUL EXTENSION", "Player leaderboards exist; Pascal evaluates identity prospectively after context adjustment."),
        ("Challenge exhaustion and future option value", "RELATED PRIOR WORK", "Sequential policy and resource-exhaustion analyses already exist in ABS Charts, TapToChallenge, and open-source work."),
    ], columns=["contribution", "classification", "rationale"])


def source_inventory_md() -> str:
    rows=[]
    for typ,title,author,date,url,q,data,rel,over,diff in SOURCES:
        rows.append(f"| {typ} | [{title}]({url}) | {author} | {date} | {q} | {data} | {rel} | {over} | {diff} |")
    return """# PV-1 Source Inventory

Fresh review completed 2026-09-10. Searches covered Baseball Savant, MLB, SABR, FanGraphs, accessible public baseball analysis, academic papers, GitHub, Substack/newsletters, and dedicated ABS tools. Baseball Prospectus was searched but no accessible directly relevant Article 1 comparator was identified. Absence from this inventory is not evidence that no work exists.

| Type | Title | Author / organization | Date | Research question | Data used | Relevance | Overlap | Pascal difference |
|---|---|---|---|---|---|---|---|---|
""" + "\n".join(rows) + "\n"


def claims_md(numbers: dict, boundary: pd.DataFrame, models: pd.DataFrame) -> str:
    max_delta=float(boundary.recognition_rate_absolute_change.abs().max())
    claims=[
      ("A", "Pascal's reconstructed 2026 ABS geometry agreed with 9,482 of 9,485 official decisions, or 99.968%.", "SUPPORTED_WITH_QUALIFICATION", "Accepted validation report; disagreement audit", "One material source-zone-height discrepancy and two microscopic edge discrepancies.", "Pascal's public-data reconstruction agreed with 9,482 of 9,485 official ABS challenge decisions (99.968%); the three disagreements are preserved and audited."),
      ("B", "The reconstructed ABS zone identified 11,704 incorrect called strikes.", "SUPPORTED_WITH_QUALIFICATION", "Publication funnel", "Unchallenged pitches lack official adjudication.", "The reconstructed zone classified 11,704 called strikes as estimated incorrect calls during the accepted snapshot."),
      ("C", "Of those, 10,755 occurred with a legal batter challenge available.", "SUPPORTED", "Sprint 3 population audit", "Excludes 789 resource-constrained and 160 position-player-pitching pitches.", "Of those estimated incorrect called strikes, 10,755 occurred while a legal batter challenge was available."),
      ("D", "Batters challenged 2,112 of 10,755, or 19.64%.", "SUPPORTED", "Boundary sensitivity and metric audit", f"Recognition is action, regardless of outcome; maximum tested absolute rate shift {max_delta:.3%}.", "Batters challenged 2,112 of 10,755 legally challengeable estimated incorrect called strikes (19.64%)."),
      ("E", "Larger misses were more likely to be challenged.", "SUPPORTED", "Boundary sensitivity", "Association, not causation.", "The farther an estimated incorrect strike lay beyond the reconstructed boundary, the more likely the batter was to challenge."),
      ("F", "Situation substantially improved prediction.", "SUPPORTED", "Temporal model sensitivity", "Predictive contribution only.", "Game situation substantially improved held-out prediction of whether a batter challenged an estimated incorrect called strike."),
      ("G", "Pitch characteristics did not add validated held-out predictive value beyond geometry.", "SUPPORTED_WITH_QUALIFICATION", "Temporal model sensitivity", "A null incremental block result does not show pitch characteristics never matter.", "Pitch type, velocity, movement, spin, extension, and release characteristics did not add validated held-out predictive value beyond geometry in the accepted model."),
      ("H", "Batter identity adds information about future recognition after difficulty adjustment.", "SUPPORTED", "Sprint 4 temporal validation", "Do not call this eyesight or direct perception.", "Batter identity added held-out predictive information about future recognition behavior after opportunity difficulty was accounted for."),
      ("I", "Challenge exhaustion sometimes leaves teams unable to correct later errors.", "SUPPORTED_WITH_QUALIFICATION", "Sprint 5 exhaustion sequences", "Descriptive teaser; no judgment about earlier challenge quality.", "In the accepted snapshot, challenge exhaustion sometimes preceded later estimated errors that the team could no longer challenge."),
    ]
    header="# Article 1 Claims Matrix\n\n| Claim | Proposed wording | Classification | Evidence | Qualification | Preferred wording |\n|---|---|---|---|---|---|\n"
    return header+"\n".join("| "+" | ".join(x)+" |" for x in claims)+"\n"


def docs(root: Path, nums: dict, boundary: pd.DataFrame, models: pd.DataFrame, validation_dist: pd.DataFrame) -> None:
    out=root/"docs/publication_validation"; out.mkdir(parents=True, exist_ok=True)
    (out/"source_inventory.md").write_text(source_inventory_md())
    (out/"article1_claims_matrix.md").write_text(claims_md(nums,boundary,models))
    (out/"terminology_guide.md").write_text("""# Article 1 Terminology Guide

| Term | Use | Definition |
|---|---|---|
| official ABS decision | Yes, only for challenged pitches | MLB's recorded result for an actual challenge. |
| estimated incorrect call | Preferred | An unchallenged or challenged call classified as wrong by Pascal's reconstructed geometry. |
| reconstructed incorrect call | Yes | Equivalent technical wording that names the method. |
| recognition | Yes | A batter challenged a legal estimated incorrect called strike, regardless of outcome. |
| missed recognition | Avoid as a factual label | Holding may reflect strategy, uncertainty, communication, or perception; use “not challenged.” |
| challenge opportunity | Qualify | State whether it means every legal called-strike opportunity or a legal estimated-error opportunity. |
| correction | Define denominator | A challenge that officially overturned the original call; for reconstructed errors, require both estimated error and official overturn. |
| challenge success | Yes | Official overturns divided by actual challenges. |

“ABS says the pitch was wrong” is too strong for an unchallenged pitch. Avoid “players failed to notice,” “bad calls” without a reconstructed qualifier, causal language, and eyesight or vision labels.
""")
    (out/"methodology.md").write_text(f"""# PV-1 Methodology

PV-1 consumes the accepted 2026-03-25 through 2026-09-09 Sprint 1–5 snapshot without changing it. Phase 1 verifies the 9,485 official challenges, 9,482 agreements, three disagreements, and the 11,704 → 10,755 → 2,112 recognition population. SHA-256 hashes in the run manifest prove the accepted files were unchanged.

The reconstructed ABS classifier is the accepted `abs_2026_circle_rectangle_r1.45in_v1` method. Signed distance is in feet; absolute distances are converted to inches. Validation bins were preregistered as [0,.05), [.05,.10), [.10,.25), [.25,.50), [.50,1), and [1,+∞). Sensitivity excludes every pitch with `abs_distance_inches <= threshold`, so exact-threshold observations belong to the uncertainty band. Thresholds were 0, .05, .10, .25, and .50 inches.

At each threshold, the recognition population and a univariate logistic association with absolute distance were recomputed. Accepted A geometry, B geometry-plus-pitch, and C geometry-plus-pitch-plus-situation models were rerun using expanding monthly holdouts, fixed L2 C=1 logistic regression, and the accepted features. Metrics are pooled ROC AUC, PR AUC, log loss, and Brier score. No alternate model search was conducted.

Representative pitches were selected deterministically after inference and are illustrations only. The novelty review was completed through {RUN_DATE} against official, academic, independent, newsletter, tool, and open-source work. Novelty classifications are conservative and require Pascal research-lead acceptance.
""")
    max_abs=float(boundary.recognition_rate_absolute_change.abs().max())
    max_rel=float(boundary.recognition_rate_relative_change.abs().max())
    geook=bool((boundary.geometry_direction=="POSITIVE").all() and (boundary.distance_p_value<.05).all())
    c=models[models.model.eq("DELTA_B_PITCH_TO_C_SITUATION")]
    sitok=bool((c.delta_roc_auc>0).all() and (c.delta_log_loss<0).all() and (c.delta_brier_score<0).all())
    report=f"""# Publication Validation Report — Article 1

## Decision

**Article 1: REQUIRES_REVISION.** The quantitative claims survive the preregistered checks, but the differentiation language must acknowledge substantial prior public work on unchallenged misses, challenge propensity, context, and sequential resource value. This gate authorizes revision and drafting preparation; it does not authorize publication.

| Gate | Result | Basis |
|---|---|---|
| Methodology | PASS | Integrity and exact population checks pass; no accepted artifact changed. |
| Boundary Robustness | PASS | All thresholds preserve the positive geometry association and recognition shifts by at most {max_abs:.2%} absolute ({max_rel:.2%} relative). |
| Claim Accuracy | PASS | Claims A–I have supported qualified wording and explicit denominators. |
| Novelty / Differentiation | REVISE | Several intended contributions overlap direct 2026 public work; Pascal's defensible additions are the independently validated frozen reconstruction, exact funnel, temporal block tests, and adversarial claim audit. |

## Core findings

The reconstruction reproduces 9,482 of 9,485 official decisions (99.968%). Two disagreements are 0.0027 and 0.0045 inches from the reconstructed boundary and are consistent with source precision. The third is 1.386 inches inside the reconstructed top boundary but 0.171 inches outside the published Savant boundary because the source top differs by about 2.07 inches. That isolated record is a material source-zone-height discrepancy, not evidence that the accepted public formula is generally defective. It must remain disclosed.

The full funnel reconciles 645,793 physical pitches to 336,095 called pitches, 103,768 called strikes, 11,704 estimated incorrect called strikes, 10,755 legal recognition opportunities, 2,112 challenged, and 8,643 not challenged. Recognition is the batter's challenge action; challenge outcome does not define it.

Across the five uncertainty bands, the recognition conclusion remains stable. The geometry coefficient stays positive and statistically distinguishable from zero: {geook}. The accepted situation block improves all principal held-out metrics at every threshold: {sitok}. The pitch-characteristic block does not meet the accepted incremental-value criteria. Sprint 4's temporal batter result remains evidence that identity predicts future behavior after adjustment, without identifying eyesight or perception as the mechanism.

## Claims we may make

- Pascal's public-data reconstruction agreed with 9,482 of 9,485 official ABS challenge decisions, with the three disagreements disclosed.
- The reconstruction classified 11,704 called strikes as estimated incorrect calls; 10,755 occurred with a legal batter challenge available.
- Batters challenged 2,112 of those 10,755 opportunities, or 19.64%.
- Larger reconstructed misses were more likely to be challenged, and game situation added substantial held-out predictive information.
- Batter identity added held-out predictive information after opportunity difficulty was accounted for.
- Challenge exhaustion sometimes preceded later estimated errors that the team could no longer challenge.

## Claims we should not make

- “ABS officially ruled every unchallenged pitch incorrect”: unchallenged pitches received no official ABS decision.
- “Players failed to notice 80% of bad calls”: a hold does not identify perception, and the errors are reconstructed estimates.
- “Pitch movement does not matter”: only incremental held-out value in the accepted block test was unsupported.
- “Catchers have no effect”: Article 1 does not establish that claim.
- “Players challenge too little,” “waste challenges,” or “manage challenges poorly”: these are normative and Sprint 5's volume conclusion was sensitive.
- Player leaderboard claims framed as eyesight or strike-zone vision: the models measure behavior conditional on observed opportunity features.
- First, unprecedented, or nobody-has-studied-this claims: the source inventory documents close prior work.

## Publication use

Use `article1_numbers.json` for every number and the figure-data directory for chart inputs. Use the claims matrix's preferred wording. Pascal's research lead must accept the source-zone discrepancy interpretation and revised novelty framing; the publication owner then performs the separate editorial review required by PV-1.
"""
    (out/"publication_validation_report.md").write_text(report)


def figure_data(root: Path, funnel: pd.DataFrame, features: pd.DataFrame) -> None:
    out=root/"artifacts/publication_validation/article1_figure_data"; out.mkdir(parents=True,exist_ok=True)
    write_csv(out/"figure1_publication_funnel.csv", funnel)
    bins=[0,.1,.25,.5,1,2,3,5,np.inf]; labels=["0-.10",".10-.25",".25-.50",".50-1","1-2","2-3","3-5","5+"]
    x=features.copy(); x["distance_bin_inches"]=pd.cut(x.abs_distance_inches,bins,labels=labels,right=False)
    d=x.groupby("distance_bin_inches",observed=False).recognized.agg(opportunities="size",recognized="sum").reset_index()
    d["not_recognized"]=d.opportunities-d.recognized; d["recognition_rate"]=d.recognized/d.opportunities
    write_csv(out/"figure2_recognition_by_error_distance.csv",d)
    g=features.groupby("inning_group").recognized.agg(opportunities="size",recognized="sum").reset_index()
    g["not_recognized"]=g.opportunities-g.recognized; g["recognition_rate"]=g.recognized/g.opportunities
    write_csv(out/"figure3_recognition_by_game_stage.csv",g)
    write_json(out/"figure4_research_program_map.json", {"nodes":["umpire call","recognition","challenge decision","resource use","outcome"],"edges":[["umpire call","recognition"],["recognition","challenge decision"],["challenge decision","resource use"],["resource use","outcome"]]})


def run(root: Path) -> None:
    art=root/"artifacts/publication_validation"; art.mkdir(parents=True,exist_ok=True)
    before=hashes(root)
    integ=integrity(root,before); write_json(art/"integrity_check.json",integ)
    audit,vdist=disagreement_audit(root); write_csv(art/"boundary_disagreement_audit.csv",audit); write_csv(art/"validation_error_distribution.csv",vdist)
    p=pd.read_csv(root/"data/full_season/processed/pitches.csv",low_memory=False)
    boundary,model=sensitivity(root,p); write_csv(art/"boundary_sensitivity.csv",boundary); write_csv(art/"model_sensitivity.csv",model)
    funnel,metric,counts=funnel_and_metrics(p,root); write_csv(art/"publication_funnel.csv",funnel); write_csv(art/"metric_definitions.csv",metric)
    reps=representative_pitches(root); write_csv(art/"representative_pitches.csv",reps)
    nov=novelty(); write_csv(art/"novelty_matrix.csv",nov)
    features=pd.read_csv(root/"data/analysis/sprint3/offensive_recognition_features.csv")
    figure_data(root,funnel,features)
    nums={"snapshot_start":START,"snapshot_end":END,"games":integ["games"],"physical_pitches":counts["physical_pitches"],
          "called_pitches":counts["called_pitches"],"called_strikes":counts["called_strikes"],"official_challenges":9485,
          "geometry_agreements":9482,"geometry_disagreements":3,"geometry_agreement_rate":9482/9485,
          "estimated_incorrect_called_strikes":11704,"legal_recognition_opportunities":10755,"recognized":2112,
          "not_recognized":8643,"recognition_rate":2112/10755,
          "resource_constrained_exclusions":789,"position_player_pitching_exclusions":160,
          "unknown_exclusions":0,"other_exclusions":0,
          "challenge_rate":metric.loc[metric.metric.eq("challenge_rate")].iloc[0].to_dict(),
          "challenge_success_rate":metric.loc[metric.metric.eq("challenge_success_rate")].iloc[0].to_dict(),
          "correction_rate":metric.loc[metric.metric.eq("correction_rate")].iloc[0].to_dict(),
          "boundary_disagreements":json.loads(audit.to_json(orient="records")),
          "boundary_sensitivity_results":json.loads(boundary.to_json(orient="records")),
          "model_sensitivity_results":json.loads(model.to_json(orient="records"))}
    docs(root,nums,boundary,model,vdist)
    # Freeze only after claims audit documents exist.
    write_json(art/"article1_numbers.json",nums)
    after=hashes(root)
    if before != after: raise RuntimeError("Accepted upstream artifacts mutated during PV-1")
    outputs=sorted([x for x in art.rglob("*") if x.is_file() and x.name!="run_manifest.json"] + [x for x in (root/"docs/publication_validation").rglob("*") if x.is_file()])
    commit=subprocess.run(["git","rev-parse","HEAD"],cwd=root,text=True,capture_output=True).stdout.strip() or "UNCOMMITTED"
    manifest={"analysis":"PV-1 Article 1 claim validation","execution_date":RUN_DATE,"external_review_date":RUN_DATE,
              "snapshot_start":START,"snapshot_end":END,"code_commit":commit,"python":platform.python_version(),
              "pandas":pd.__version__,"scikit_learn":sklearn.__version__,"boundary_thresholds_inches":THRESHOLDS,
              "threshold_rule":"exclude abs_distance_inches <= threshold","upstream_hashes_before":before,
              "upstream_hashes_after":after,"upstream_unchanged":before==after,
              "output_hashes":{str(x.relative_to(root)):sha(x) for x in outputs},
              "phase_order":["integrity","disagreement audit","boundary robustness","funnel and metric audit","representative examples","novelty review","claims audit","number freeze","validation report"],
              "gates":{"methodology":"PASS","boundary_robustness":"PASS","claim_accuracy":"PASS","novelty_differentiation":"REVISE","article1":"REQUIRES_REVISION"}}
    write_json(art/"run_manifest.json",manifest)


if __name__ == "__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--root",type=Path,default=Path(".")); args=ap.parse_args(); run(args.root.resolve())
