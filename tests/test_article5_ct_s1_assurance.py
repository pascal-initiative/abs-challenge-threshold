import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


ARTICLE5 = Path(__file__).resolve().parents[1] / "research" / "article5"
sys.path.insert(0, str(ARTICLE5))

from ct_s1_assurance import (  # noqa: E402
    BOOTSTRAP_REPLICATES,
    BOOTSTRAP_SEED,
    assert_protected_unchanged,
    clustered_reference_intervals,
    compare_clean_builds,
    protected_hashes,
    reject_runtime_metadata,
    validate_json_files_have_no_runtime_metadata,
    validate_uncertainty_output,
)
from build_ct_s1_reproducibility import (  # noqa: E402
    clone_path,
    normalized_command,
    statuses_pass,
)


def source_rows():
    # Costs are constant within game so resampling must occur at game level.
    return pd.DataFrame({
        "game_pk": [1, 1, 2, 2, 3, 3],
        "state_key": ["state"] * 6,
        "cost_inventory_1": [0.02, 0.02, 0.06, 0.06, 0.10, 0.10],
        "cost_inventory_2": [0.01, 0.01, 0.03, 0.03, 0.05, 0.05],
    })


def targets():
    return pd.DataFrame([
        {"scenario_id": "one", "state_key": "state", "inventory": 1,
         "correction_value": 0.10},
        {"scenario_id": "two", "state_key": "state", "inventory": 2,
         "correction_value": 0.10},
    ])


def test_clustered_intervals_are_deterministic_and_separate_from_model_spread():
    first = clustered_reference_intervals(source_rows(), targets(), replicates=200, seed=11)
    second = clustered_reference_intervals(source_rows(), targets(), replicates=200, seed=11)
    pd.testing.assert_frame_equal(first, second)
    assert not any(column.startswith("model_spread_") for column in first.columns)
    assert first.sampling_interval_complete.all()
    assert first.sampling_ct_low_95.le(first.sampling_ct_high_95).all()


def test_frozen_default_seed_and_replicate_count_pass_gate():
    intervals = clustered_reference_intervals(source_rows(), targets())
    assert BOOTSTRAP_SEED == 20260926
    assert BOOTSTRAP_REPLICATES == 2_000
    assert intervals.bootstrap_seed.eq(BOOTSTRAP_SEED).all()
    assert intervals.bootstrap_replicates.eq(BOOTSTRAP_REPLICATES).all()
    assert validate_uncertainty_output(intervals)["pass_cts9"]


def test_uncertainty_gate_rejects_incomplete_replicates():
    intervals = clustered_reference_intervals(source_rows(), targets(), replicates=100, seed=7)
    passed = validate_uncertainty_output(
        intervals, expected_replicates=100, expected_seed=7
    )
    assert passed["pass_cts9"]
    intervals.loc[0, "finite_replicates"] = 99
    failed = validate_uncertainty_output(
        intervals, expected_replicates=100, expected_seed=7
    )
    assert not failed["pass_cts9"]


def test_missing_state_is_retained_as_incomplete_interval():
    missing = targets().assign(state_key="absent")
    intervals = clustered_reference_intervals(source_rows(), missing, replicates=20, seed=3)
    assert intervals.finite_replicates.eq(0).all()
    assert intervals.sampling_ct_low_95.isna().all()
    assert not intervals.sampling_interval_complete.any()


def test_partially_finite_bootstrap_does_not_publish_interval():
    source = pd.concat([
        source_rows().loc[lambda frame: frame.game_pk.eq(1)],
        source_rows().loc[lambda frame: frame.game_pk.ne(1)].assign(state_key="other"),
    ], ignore_index=True)
    intervals = clustered_reference_intervals(
        source, targets().iloc[[0]], replicates=100, seed=5
    )
    assert 0 < intervals.loc[0, "finite_replicates"] < 100
    assert np.isnan(intervals.loc[0, "sampling_ct_low_95"])
    assert not intervals.loc[0, "sampling_interval_complete"]


def test_protected_input_mutation_canary_fails(tmp_path):
    protected = tmp_path / "frozen.txt"
    protected.write_text("before\n")
    before = protected_hashes([protected], tmp_path)
    protected.write_text("after\n")
    after = protected_hashes([protected], tmp_path)
    with pytest.raises(RuntimeError, match="protected inputs changed"):
        assert_protected_unchanged(before, after)


def test_clean_build_comparison_has_no_exclusions(tmp_path):
    run_a = tmp_path / "a"
    run_b = tmp_path / "b"
    run_a.mkdir()
    run_b.mkdir()
    (run_a / "result.csv").write_text("x\n1\n")
    (run_b / "result.csv").write_text("x\n1\n")
    assert compare_clean_builds(run_a, run_b)["pass_cts10_pair_comparison"]
    (run_b / "result.csv").write_text("x\n2\n")
    failed = compare_clean_builds(run_a, run_b)
    assert not failed["pass_cts10_pair_comparison"]
    assert failed["differences"][0]["relative_path"] == "result.csv"


def test_runtime_metadata_canary_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="runtime metadata is forbidden"):
        reject_runtime_metadata({"manifest": {"generated_at": "now"}})
    safe = tmp_path / "safe"
    safe.mkdir()
    (safe / "manifest.json").write_text(json.dumps({"source_end_date": "2026-09-27"}))
    assert validate_json_files_have_no_runtime_metadata(safe) == ["manifest.json"]


def test_isolated_copy_is_independent_and_commands_are_path_normalized(tmp_path):
    source = tmp_path / "source.txt"
    copied = tmp_path / "isolated" / "source.txt"
    source.write_text("frozen\n")
    clone_path(source, copied)
    assert copied.read_bytes() == source.read_bytes()
    copied.write_text("derived\n")
    assert source.read_text() == "frozen\n"
    for gate in ("cts3", "temporal", "cts7", "cts9"):
        command = normalized_command(gate)
        assert "run_a" not in command
        assert "run_b" not in command
        assert "{root}" in command


def test_successor_status_contract_requires_every_prior_gate():
    passing = {
        "CTS3": "PASS_CTS3_READY_FOR_CTS4_CTS8",
        "CTS4": "PASS",
        "CTS5": "PASS",
        "CTS6": "PASS",
        "CTS7": "PASS_CTS7_READY_FOR_CTS9",
        "CTS8": "PASS",
        "CTS9": "PASS_CTS9_READY_FOR_CTS10",
    }
    assert statuses_pass(passing)
    assert not statuses_pass({**passing, "CTS6": "FAIL"})
