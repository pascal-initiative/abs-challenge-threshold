import sys
from pathlib import Path

import numpy as np
import pandas as pd


ARTICLE5 = Path(__file__).resolve().parents[1] / "research" / "article5"
sys.path.insert(0, str(ARTICLE5))

from build_ct_s1_prepared import (  # noqa: E402
    VARIANT_SPECS,
    evaluate_variant_rows,
)
from ct_s1_core import CORE_VARIANTS, DIAGNOSTIC_VARIANTS  # noqa: E402


def tiny_stream():
    return pd.DataFrame({
        "game_pk": [1, 1, 1],
        "team_id": [10, 10, 10],
        "inning": [1, 2, 3],
        "value_constrained": [0.02, 0.20, 0.03],
        "value_pooled": [0.02, 0.20, 0.03],
        "value_raw": [0.02, 0.20, 0.03],
        "p_public": [0.5, 0.5, 0.5],
        "p_selected": [0.6, 0.6, 0.6],
    })


def test_variant_spec_exactly_matches_frozen_grid():
    names = {row[0] for row in VARIANT_SPECS}
    assert names == set(CORE_VARIANTS) | set(DIAGNOSTIC_VARIANTS)
    assert len(names) == len(VARIANT_SPECS)


def test_reference_actions_are_fixed_and_inventory_invariant():
    result = evaluate_variant_rows(
        tiny_stream(),
        probability=0.60,
        value_column="value_constrained",
        cutoff=0.05,
        grant_extras=True,
    )
    assert np.array_equal(result["actions"][1], result["actions"][2])
    assert result["actions"][1].tolist() == [False, True, False]
    assert np.isfinite(result["costs"]).all()


def test_changing_later_value_does_not_change_current_action():
    original = tiny_stream()
    changed = original.copy()
    changed.loc[2, "value_constrained"] = 100.0
    first = evaluate_variant_rows(
        original, probability=0.60, value_column="value_constrained",
        cutoff=0.05, grant_extras=True,
    )
    second = evaluate_variant_rows(
        changed, probability=0.60, value_column="value_constrained",
        cutoff=0.05, grant_extras=True,
    )
    assert first["actions"][1, 0] == second["actions"][1, 0]
    assert first["costs"][1, 0] != second["costs"][1, 0]
