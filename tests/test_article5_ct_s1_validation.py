import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


ARTICLE5 = Path(__file__).resolve().parents[1] / "research" / "article5"
sys.path.insert(0, str(ARTICLE5))

from ct_s1_core import (  # noqa: E402
    CORE_VARIANTS,
    attach_model_spread,
    audit_contrasts,
    cts7_passes,
    harmonize_scenarios,
    summarize_support_schedule,
    temporal_stability,
    validate_information_fields,
    validate_public_presentation,
    validate_team_game_order,
)
from build_ct_s1_temporal import build_candidate_states  # noqa: E402
from build_ct_s1_contrasts import (  # noqa: E402
    count_pairs,
    early_late_pairs,
    inventory_pairs,
    select_ordinary_representatives,
)
from build_ct_s1_uncertainty import (  # noqa: E402
    REPLICATES,
    bootstrap_support_costs,
)


def synthetic_rows(count, games, inning=7, score=0, cost_1=0.04, cost_2=0.025):
    return pd.DataFrame({
        "game_pk": np.arange(count) % games,
        "inning": inning,
        "half_inning": "top",
        "outs": 1,
        "team_role": "offense",
        "team_score_diff": score,
        "cost_inventory_1": cost_1,
        "cost_inventory_2": cost_2,
    })


def scenario(identifier, inning, score, value=0.10, inventory=1):
    return pd.DataFrame([{
        "scenario_id": identifier,
        "inventory": inventory,
        "correction_value": value,
        "inning": inning,
        "half_inning": "top",
        "outs": 1,
        "team_role": "offense",
        "team_score_diff": score,
    }])


def test_information_gate_rejects_hindsight_canary():
    assert validate_information_fields(["inning", "outs", "score_bucket"]) == (
        "inning", "outs", "score_bucket"
    )
    with pytest.raises(ValueError, match="decision-time information violation"):
        validate_information_fields(["inning", "challenge_result"])
    with pytest.raises(ValueError, match="decision-time information violation"):
        validate_information_fields(["inning", "decision_sequence"])


def test_team_game_order_rejects_shuffle():
    ordered = pd.DataFrame({
        "game_pk": [1, 1, 1], "team_id": [10, 10, 10], "decision_sequence": [0, 1, 2]
    })
    validate_team_game_order(ordered)
    shuffled = ordered.iloc[[1, 0, 2]].reset_index(drop=True)
    with pytest.raises(ValueError, match="non-canonical row order"):
        validate_team_game_order(shuffled)


def test_candidate_states_use_public_buckets_and_both_inventory_levels():
    rows = pd.DataFrame({
        "observed_legal_decision": [True, True],
        "original_call": ["ball", "ball"],
        "side": ["offense", "offense"],
        "balls": [2, 2],
        "strikes": [1, 1],
        "outs": [1, 1],
        "base_state": ["100", "100"],
        "inning": [11, 12],
        "half_inning": ["top", "top"],
        "team_role": ["offense", "offense"],
        "team_score_diff": [2, 5],
        "value_constrained": [0.10, 0.10],
        "value_pooled": [0.11, 0.11],
        "value_raw": [0.12, 0.12],
    })
    result = build_candidate_states(rows, period="confirmation")
    assert len(result) == 2
    assert set(result.inventory) == {1, 2}
    assert set(result.inning_exact) == {"10+"}
    assert set(result.score_bucket) == {"LEAD_2PLUS"}
    assert result.scenario_id.nunique() == 2


def contrast_state(identifier, *, inning=1, inventory=1, balls=0, strikes=0, call="BALL"):
    return {
        "scenario_id": identifier,
        "original_call": call,
        "side": "OFFENSE",
        "balls": balls,
        "strikes": strikes,
        "outs": 0,
        "base_state": 0,
        "inning_exact": str(inning),
        "half_inning": "top",
        "score_bucket": "TIED",
        "team_role": "AWAY",
        "inventory": inventory,
    }


def test_contrast_pair_generators_follow_frozen_pairing_rules():
    states = pd.DataFrame([
        contrast_state("early-one", inning=1, inventory=1),
        contrast_state("late-one", inning=7, inventory=1),
        contrast_state("early-two", inning=1, inventory=2),
        contrast_state("late-two", inning=7, inventory=2),
        contrast_state("terminal-ball", inning=1, inventory=1, balls=3),
        contrast_state("ordinary-strike", inning=1, inventory=1, call="STRIKE", strikes=0),
        contrast_state("terminal-strike", inning=1, inventory=1, call="STRIKE", strikes=2),
    ])
    early = early_late_pairs(states)
    inventory = inventory_pairs(states)
    count = count_pairs(states)
    assert set(zip(early.member_a_scenario_id, early.member_b_scenario_id)) == {
        ("early-one", "late-one"), ("early-two", "late-two")
    }
    assert ("early-one", "early-two") in set(
        zip(inventory.member_a_scenario_id, inventory.member_b_scenario_id)
    )
    assert ("early-one", "terminal-ball") in set(
        zip(count.member_a_scenario_id, count.member_b_scenario_id)
    )
    assert ("ordinary-strike", "terminal-strike") in set(
        zip(count.member_a_scenario_id, count.member_b_scenario_id)
    )


def test_ordinary_selection_uses_development_midpoint_and_stable_tie_break():
    candidates = pd.DataFrame([
        {
            "contrast_id": "inventory|z", "contrast_class": "inventory",
            "source_contrast_class": "inventory", "member_a_scenario_id": "a",
            "member_b_scenario_id": "b", "outs": 0, "base_state": 0,
            "selection_rule": "test",
        },
        {
            "contrast_id": "inventory|a", "contrast_class": "inventory",
            "source_contrast_class": "inventory", "member_a_scenario_id": "c",
            "member_b_scenario_id": "d", "outs": 0, "base_state": 0,
            "selection_rule": "test",
        },
    ])
    development = pd.Series({"a": 0.2, "b": 0.4, "c": 0.2, "d": 0.4, "extra": 0.3})
    selected = select_ordinary_representatives(candidates, development)
    assert len(selected) == 1
    assert selected.loc[0, "member_a_scenario_id"] == "c"
    assert selected.loc[0, "contrast_class"] == "ordinary"


def test_cluster_bootstrap_draws_whole_games_and_reconciles_point_cost():
    prepared = pd.DataFrame({
        "game_pk": [1, 1, 2, 2],
        "inning": [7, 7, 7, 7],
        "half_inning": ["top"] * 4,
        "outs": [1] * 4,
        "team_role": ["offense"] * 4,
        "team_score_diff": [0] * 4,
        "cost_inventory_1__reference_fixed_0.60": [0.02, 0.04, 0.06, 0.08],
        "cost_inventory_2__reference_fixed_0.60": [0.01, 0.03, 0.05, 0.07],
    })
    key = "L0_EXACT|7|top|1|offense|TIED"
    result = bootstrap_support_costs(
        prepared,
        period="development",
        required_keys={"L0_EXACT": {key}},
    )
    assert len(result) == 2
    assert result.sampling_complete.all()
    assert set(result.sampling_finite_replicates) == {REPLICATES}
    assert result.loc[result.inventory.eq(1), "sampling_cost_point_recomputed"].iloc[0] == pytest.approx(0.05)
    assert result.loc[result.inventory.eq(2), "sampling_cost_point_recomputed"].iloc[0] == pytest.approx(0.04)


def test_harmonization_uses_finest_common_supported_level():
    development_rows = synthetic_rows(200, 100, inning=7, score=0, cost_1=0.04)
    # Confirmation splits exact score support: 30 tied and 30 leading.  L0 is
    # unsupported, while L1 (which drops score) is supported.
    confirmation_rows = pd.concat([
        synthetic_rows(30, 25, inning=7, score=0, cost_1=0.05),
        synthetic_rows(30, 25, inning=7, score=1, cost_1=0.05).assign(
            game_pk=lambda frame: frame.game_pk + 100
        ),
    ], ignore_index=True)
    development_schedule = summarize_support_schedule(
        development_rows, period="development", min_rows=200, min_games=100
    )
    confirmation_schedule = summarize_support_schedule(
        confirmation_rows, period="confirmation", min_rows=50, min_games=25
    )
    matched = harmonize_scenarios(
        scenario("ordinary", 7, 0),
        scenario("ordinary", 7, 0),
        development_schedule,
        confirmation_schedule,
    )
    assert matched.loc[0, "supported"]
    assert matched.loc[0, "development_original_level"] == "L0_EXACT"
    assert matched.loc[0, "confirmation_original_level"] == "L1_NO_SCORE"
    assert matched.loc[0, "harmonized_level"] == "L1_NO_SCORE"
    assert matched.loc[0, "development_support_rows"] == 200
    assert matched.loc[0, "confirmation_support_rows"] == 60


def test_confirmation_rows_without_development_match_remain_in_coverage_denominator():
    rows = synthetic_rows(200, 100)
    development_schedule = summarize_support_schedule(
        rows, period="development", min_rows=200, min_games=100
    )
    confirmation_schedule = summarize_support_schedule(
        rows.iloc[:100], period="confirmation", min_rows=50, min_games=25
    )
    confirmation = pd.concat([
        scenario("matched", 7, 0),
        scenario("confirmation-only", 7, 0),
    ], ignore_index=True)
    matched = harmonize_scenarios(
        scenario("matched", 7, 0),
        confirmation,
        development_schedule,
        confirmation_schedule,
    )
    assert len(matched) == 2
    excluded = matched.loc[matched.scenario_id.eq("confirmation-only")].iloc[0]
    assert not excluded.supported
    assert excluded.exclusion_reason == "NO_DEVELOPMENT_MATCH"


def test_negative_sensitivity_value_is_retained_as_undefined_threshold():
    rows = synthetic_rows(200, 100)
    development_schedule = summarize_support_schedule(
        rows, period="development", min_rows=200, min_games=100
    )
    confirmation_schedule = summarize_support_schedule(
        rows.iloc[:100], period="confirmation", min_rows=50, min_games=25
    )
    matched = harmonize_scenarios(
        scenario("raw-negative", 7, 0, value=-0.01),
        scenario("raw-negative", 7, 0, value=-0.02),
        development_schedule,
        confirmation_schedule,
    )
    assert matched.loc[0, "supported"]
    assert np.isnan(matched.loc[0, "development_ct"])
    assert np.isnan(matched.loc[0, "confirmation_ct"])


def test_temporal_stability_uses_average_ranks_and_all_frozen_cutoffs():
    matched = pd.DataFrame({
        "supported": [True, True, True, True],
        "development_ct": [0.20, 0.20, 0.40, 0.60],
        "confirmation_ct": [0.21, 0.21, 0.43, 0.64],
    })
    result = temporal_stability(matched)
    assert result["spearman_average_rank"] == pytest.approx(1.0)
    assert result["support_coverage"] == 1.0
    assert result["pass_cts6"]


def test_model_spread_uses_core_only_and_labels_material_rows():
    assert "cutoff_0.00" in CORE_VARIANTS
    assert "cutoff_0.10" in CORE_VARIANTS
    row = {variant: 0.20 for variant in CORE_VARIANTS}
    row[CORE_VARIANTS[-1]] = 0.34
    row["public_tracking"] = 0.99
    result = attach_model_spread(pd.DataFrame([row]))
    assert result.loc[0, "model_spread_low"] == pytest.approx(0.20)
    assert result.loc[0, "model_spread_high"] == pytest.approx(0.34)
    assert result.loc[0, "model_spread_label"] == "MATERIAL_MODEL_DISAGREEMENT"
    assert not result.loc[0, "unlabeled_point_permitted"]


def test_incomplete_model_grid_cannot_be_compact_point():
    row = {variant: 0.20 for variant in CORE_VARIANTS}
    row["re_raw"] = np.nan
    result = attach_model_spread(pd.DataFrame([row]))
    assert result.loc[0, "model_spread_label"] == "INCOMPLETE_MODEL_SPREAD"
    assert not result.loc[0, "unlabeled_point_permitted"]


def test_public_presentation_rejects_missing_material_disagreement_label():
    unsafe = pd.DataFrame([{
        "reference_ct": 0.25,
        "model_spread_complete": True,
        "model_spread_width": 0.20,
        "model_spread_label": "MODEL_SPREAD_WITHIN_0.10",
    }])
    with pytest.raises(ValueError, match="unsafe public CT presentation"):
        validate_public_presentation(unsafe)


def contrast_grid(identifier="ordinary-one", contrast_class="ordinary", flip=False):
    records = []
    for period in ("development", "confirmation"):
        for variant in CORE_VARIANTS:
            difference = -0.06 if flip and period == "confirmation" and variant == "re_raw" else 0.06
            records.extend([
                {"contrast_id": identifier, "contrast_class": contrast_class,
                 "period": period, "variant": variant, "member": "A", "ct": 0.20},
                {"contrast_id": identifier, "contrast_class": contrast_class,
                 "period": period, "variant": variant, "member": "B", "ct": 0.20 + difference},
            ])
    return pd.DataFrame(records)


def test_contrast_requires_direction_across_every_core_implementation():
    good = audit_contrasts(contrast_grid())
    assert good.loc[0, "article_eligible"]
    assert cts7_passes(good)

    bad = audit_contrasts(contrast_grid(flip=True))
    assert not bad.loc[0, "direction_stable"]
    assert not bad.loc[0, "article_eligible"]
    assert not cts7_passes(bad)


def test_contrast_duplicate_core_cell_fails_complete_grid():
    duplicated = pd.concat([contrast_grid(), contrast_grid().iloc[[0]]], ignore_index=True)
    result = audit_contrasts(duplicated)
    assert not result.loc[0, "complete_core_grid"]
    assert result.loc[0, "failure_reason"] == "INCOMPLETE_OR_DUPLICATE_CORE_GRID"
