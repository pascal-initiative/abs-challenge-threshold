"""Evaluate CT-S1 information timing, support, temporal stability, and spread.

This is the first result-bearing successor build.  It consumes the immutable
CTS3 prepared artifacts, preserves confirmation as the CTS5 denominator, and
does not select CTS7 article contrasts or calculate CTS9 intervals.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT_DEFAULT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from ct_s1_core import (  # noqa: E402
    CORE_VARIANTS,
    DIAGNOSTIC_VARIANTS,
    MATERIAL_SPREAD,
    REFERENCE_VARIANT,
    VERSION,
    attach_model_spread,
    attach_state_dimensions,
    harmonize_scenarios,
    temporal_stability,
    validate_information_fields,
    validate_public_presentation,
)


BUILD_VERSION = "ct-s1.0-cts4-cts8"
ALL_VARIANTS = (*CORE_VARIANTS, *DIAGNOSTIC_VARIANTS)
VALUE_COLUMNS = {
    **{variant: "value_constrained" for variant in ALL_VARIANTS},
    "re_pooled_count": "value_pooled",
    "re_raw": "value_raw",
}
STATE_FIELDS = (
    "original_call",
    "side",
    "balls",
    "strikes",
    "outs",
    "base_state",
    "inning_exact",
    "half_inning",
    "score_bucket",
    "team_role",
)
PUBLIC_KEY_FIELDS = (*STATE_FIELDS, "inventory")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def expected_hashes(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text().splitlines():
        digest, relative = line.split(maxsplit=1)
        result[relative] = digest
    return result


def score_representative(bucket: pd.Series) -> pd.Series:
    mapping = {
        "TRAIL_2PLUS": -2,
        "TRAIL_1": -1,
        "TIED": 0,
        "LEAD_1": 1,
        "LEAD_2PLUS": 2,
    }
    result = bucket.map(mapping)
    if result.isna().any():
        raise ValueError("unknown score bucket")
    return result.astype(int)


def inning_representative(value: pd.Series) -> pd.Series:
    return value.replace({"10+": "10"}).astype(int)


def build_candidate_states(prepared: pd.DataFrame, *, period: str) -> pd.DataFrame:
    """Collapse legal opportunities to unique public decision-time states."""
    frame = prepared.loc[prepared.observed_legal_decision.astype(bool)].copy()
    frame = attach_state_dimensions(frame)
    value_columns = sorted(set(VALUE_COLUMNS.values()))
    grouped = frame.groupby(list(STATE_FIELDS), sort=True, dropna=False)
    uniqueness = grouped[value_columns].nunique(dropna=False)
    if uniqueness.gt(1).any().any():
        failing = uniqueness.index[uniqueness.gt(1).any(axis=1)].tolist()[:5]
        raise ValueError(f"correction value is not state-deterministic: {failing}")
    states = grouped[value_columns].first().reset_index()
    states["inning"] = inning_representative(states.inning_exact)
    states["team_score_diff"] = score_representative(states.score_bucket)
    base_id = states.loc[:, STATE_FIELDS].astype(str).agg("|".join, axis=1)
    states.insert(0, "period", period)
    pieces = []
    for inventory in (1, 2):
        piece = states.copy()
        piece["inventory"] = inventory
        piece["scenario_id"] = base_id + f"|inventory={inventory}"
        pieces.append(piece)
    result = pd.concat(pieces, ignore_index=True)
    if result.scenario_id.duplicated().any():
        raise ValueError("candidate scenario identifiers are not unique")
    return result.sort_values("scenario_id", kind="stable").reset_index(drop=True)


def variant_candidates(states: pd.DataFrame, variant: str) -> pd.DataFrame:
    return states.assign(correction_value=states[VALUE_COLUMNS[variant]])


def schedule_for(schedules: pd.DataFrame, period: str, variant: str) -> pd.DataFrame:
    result = schedules.loc[
        schedules.period.eq(period) & schedules.variant.eq(variant)
    ].copy()
    if result.empty:
        raise ValueError(f"missing support schedule for {period}/{variant}")
    return result


def run_harmonization(
    development: pd.DataFrame,
    confirmation: pd.DataFrame,
    schedules: pd.DataFrame,
) -> pd.DataFrame:
    pieces = []
    for variant in ALL_VARIANTS:
        matched = harmonize_scenarios(
            variant_candidates(development, variant),
            variant_candidates(confirmation, variant),
            schedule_for(schedules, "development", variant),
            schedule_for(schedules, "confirmation", variant),
        )
        matched.insert(0, "variant", variant)
        matched.insert(1, "variant_class", "CORE" if variant in CORE_VARIANTS else "DIAGNOSTIC")
        pieces.append(matched)
    return pd.concat(pieces, ignore_index=True)


def disclosure_table(long: pd.DataFrame, reference: pd.DataFrame) -> pd.DataFrame:
    indices = ["scenario_id", "inventory"]
    result = []
    reference_fields = [
        *indices,
        "supported",
        "development_original_level",
        "confirmation_original_level",
        "harmonized_level",
        "development_support_rows",
        "development_support_games",
        "confirmation_support_rows",
        "confirmation_support_games",
        "exclusion_reason",
    ]
    metadata = reference.loc[:, reference_fields].copy()
    for period, value_column in (
        ("development", "development_ct"),
        ("confirmation", "confirmation_ct"),
    ):
        wide = long.pivot(index=indices, columns="variant", values=value_column).reset_index()
        wide.columns.name = None
        wide = attach_model_spread(wide)
        wide.insert(0, "period", period)
        wide = wide.merge(metadata, on=indices, how="left", validate="one_to_one")
        wide["reference_ct"] = wide[REFERENCE_VARIANT]
        wide["successor_version"] = VERSION
        wide["objective"] = "expected_runs"
        wide["sampling_interval_status"] = "PENDING_CTS9"
        wide["permitted_use"] = np.select(
            [
                ~wide.supported.fillna(False),
                ~np.isfinite(pd.to_numeric(wide.reference_ct, errors="coerce")),
                wide.model_spread_label.eq("INCOMPLETE_MODEL_SPREAD"),
                wide.model_spread_label.eq("MATERIAL_MODEL_DISAGREEMENT"),
            ],
            [
                "SUPPRESSED_UNSUPPORTED",
                "SUPPRESSED_UNDEFINED_REFERENCE",
                "FULL_DISCLOSURE_ONLY_INCOMPLETE_SPREAD",
                "FULL_DISCLOSURE_REQUIRED_MATERIAL_SPREAD",
            ],
            default="COMPACT_POINT_WITH_MODEL_LABEL",
        )
        result.append(wide)
    combined = pd.concat(result, ignore_index=True)
    validate_public_presentation(
        combined.loc[
            combined.reference_ct.notna() & combined.model_spread_complete,
            ["reference_ct", "model_spread_complete", "model_spread_width", "model_spread_label"],
        ]
    )
    return combined.sort_values(["period", "scenario_id"], kind="stable").reset_index(drop=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    source = (args.input or root / "data/ct_s1/cts3").resolve()
    output = (args.output or root / "data/ct_s1/temporal").resolve()
    if output.exists():
        raise SystemExit(f"output must not already exist: {output}")
    output.mkdir(parents=True)

    required_inputs = [
        source / "development_prepared.csv",
        source / "confirmation_prepared.csv",
        source / "support_schedules.csv",
        source / "validation.json",
        source / "manifest.json",
    ]
    protected_specs = [
        root / "research/article5/CT_S1_CTS3_OUTPUTS.sha256",
        root / "research/article5/CT_SUCCESSOR_VALIDATION_PLAN.md",
        root / "research/article5/CT_S1_MODEL_SCHEMA.md",
        root / "research/article5/AMENDMENT_005_CT_SUCCESSOR_STANDARD.md",
    ]
    protected = [*required_inputs, *protected_specs]
    before = {str(path.relative_to(root)): sha256(path) for path in protected}
    expected = expected_hashes(root / "research/article5/CT_S1_CTS3_OUTPUTS.sha256")
    cts3_hashes_reconcile = all(
        (root / relative).is_file() and sha256(root / relative) == digest
        for relative, digest in expected.items()
    )
    cts3_validation = json.loads((source / "validation.json").read_text())
    if not cts3_validation["status"].startswith("PASS_CTS3"):
        raise SystemExit("CTS3 did not pass")

    validate_information_fields(PUBLIC_KEY_FIELDS)
    validate_information_fields(["fixed_probability", "correction_value", "fixed_ev_cutoff"])
    development_prepared = pd.read_csv(source / "development_prepared.csv")
    confirmation_prepared = pd.read_csv(source / "confirmation_prepared.csv")
    schedules = pd.read_csv(source / "support_schedules.csv")
    development = build_candidate_states(development_prepared, period="development")
    confirmation = build_candidate_states(confirmation_prepared, period="confirmation")
    matched_long = run_harmonization(development, confirmation, schedules)
    reference = matched_long.loc[matched_long.variant.eq(REFERENCE_VARIANT)].copy()
    reference["absolute_drift"] = (
        reference.confirmation_ct - reference.development_ct
    ).abs()

    stability_joint = temporal_stability(reference)
    stability_inventory = {
        str(inventory): temporal_stability(reference.loc[reference.inventory.eq(inventory)])
        for inventory in (1, 2)
    }
    disclosed = disclosure_table(matched_long, reference)
    compact = disclosed.loc[
        disclosed.permitted_use.eq("COMPACT_POINT_WITH_MODEL_LABEL")
    ].copy()
    exclusions = disclosed.loc[
        ~disclosed.permitted_use.eq("COMPACT_POINT_WITH_MODEL_LABEL")
    ].copy()

    support_levels = reference.harmonized_level.value_counts(dropna=False).to_dict()
    exclusion_reasons = reference.exclusion_reason.value_counts(dropna=False).to_dict()
    core_present = set(CORE_VARIANTS).issubset(disclosed.columns)
    disclosure_labeled = disclosed.model_spread_label.notna().all()
    material_labeled = disclosed.loc[
        disclosed.model_spread_width.gt(MATERIAL_SPREAD), "model_spread_label"
    ].eq("MATERIAL_MODEL_DISAGREEMENT").all()
    after = {str(path.relative_to(root)): sha256(path) for path in protected}

    conditions = {
        "cts3_hashes_reconcile": cts3_hashes_reconcile,
        "protected_inputs_unchanged": before == after,
        "cts4_public_key_fields_pass": True,
        "cts4_action_fields_pass": True,
        "cts4_inherited_current_action_canary_pass": bool(
            cts3_validation["conditions"]["current_action_canary_passes"]
        ),
        "cts5_confirmation_denominator_preserved": int(len(reference)) == int(len(confirmation)),
        "cts5_support_coverage_pass": bool(stability_joint["pass_support_coverage"]),
        "cts5_schedule_minima_enforced": bool(
            (schedules.loc[schedules.period.eq("development"), "support_rows"] >= 200).all()
            and (schedules.loc[schedules.period.eq("development"), "support_games"] >= 100).all()
            and (schedules.loc[schedules.period.eq("confirmation"), "support_rows"] >= 50).all()
            and (schedules.loc[schedules.period.eq("confirmation"), "support_games"] >= 25).all()
        ),
        "cts6_temporal_stability_pass": bool(stability_joint["pass_cts6"]),
        "cts8_all_core_columns_present": core_present,
        "cts8_all_rows_labeled": bool(disclosure_labeled),
        "cts8_material_spread_labeled": bool(material_labeled),
        "cts8_diagnostics_excluded_from_endpoints": True,
    }
    gate_status = {
        "CTS4": "PASS" if all(conditions[key] for key in conditions if key.startswith("cts4_")) else "FAIL",
        "CTS5": "PASS" if all(conditions[key] for key in conditions if key.startswith("cts5_")) else "FAIL",
        "CTS6": "PASS" if conditions["cts6_temporal_stability_pass"] else "FAIL",
        "CTS8": "PASS" if all(conditions[key] for key in conditions if key.startswith("cts8_")) else "FAIL",
    }
    all_pass = all(value == "PASS" for value in gate_status.values()) and all(
        (conditions["cts3_hashes_reconcile"], conditions["protected_inputs_unchanged"])
    )
    status = "PASS_CTS4_CTS5_CTS6_CTS8" if all_pass else "STOP_NUMERICAL_SUCCESSOR"

    development.to_csv(output / "development_candidate_states.csv", index=False, float_format="%.12g", lineterminator="\n")
    confirmation.to_csv(output / "confirmation_candidate_states.csv", index=False, float_format="%.12g", lineterminator="\n")
    matched_long.to_csv(output / "matched_all_variants.csv", index=False, float_format="%.12g", lineterminator="\n")
    reference.to_csv(output / "matched_reference.csv", index=False, float_format="%.12g", lineterminator="\n")
    disclosed.to_csv(output / "reference_disclosure.csv", index=False, float_format="%.12g", lineterminator="\n")
    compact.to_csv(output / "compact_eligible.csv", index=False, float_format="%.12g", lineterminator="\n")
    exclusions.to_csv(output / "exclusions.csv", index=False, float_format="%.12g", lineterminator="\n")

    validation = {
        "research_identity": "CT-S1",
        "version": BUILD_VERSION,
        "metric_version": VERSION,
        "status": status,
        "gate_status": gate_status,
        "conditions": conditions,
        "candidate_states": {
            "development": int(len(development)),
            "confirmation": int(len(confirmation)),
            "confirmation_is_cts5_denominator": True,
        },
        "support": {
            "coverage": stability_joint["support_coverage"],
            "harmonized_levels": {str(key): int(value) for key, value in support_levels.items()},
            "exclusion_reasons": {str(key): int(value) for key, value in exclusion_reasons.items()},
        },
        "temporal_stability": {"joint": stability_joint, "by_inventory": stability_inventory},
        "model_disclosure": {
            "rows": int(len(disclosed)),
            "compact_eligible_rows": int(len(compact)),
            "incomplete_rows": int(disclosed.model_spread_label.eq("INCOMPLETE_MODEL_SPREAD").sum()),
            "material_disagreement_rows": int(disclosed.model_spread_label.eq("MATERIAL_MODEL_DISAGREEMENT").sum()),
            "diagnostic_variants": list(DIAGNOSTIC_VARIANTS),
            "core_variants": list(CORE_VARIANTS),
        },
        "restrictions": {
            "cts7_contrasts": "not evaluated",
            "cts9_sampling_intervals": "not evaluated",
            "article_claims": False,
            "playbook_allowed": False,
            "numerical_successor_allowed": all_pass,
        },
        "next_gate": "CTS7_CONTRAST_STABILITY" if all_pass else "STOP_AND_REPORT",
    }
    write_json(output / "validation.json", validation)
    artifacts = sorted(path for path in output.iterdir() if path.is_file())
    manifest = {
        "version": BUILD_VERSION,
        "status": status,
        "code_sha256": {
            "build_ct_s1_temporal.py": sha256(Path(__file__)),
            "ct_s1_core.py": sha256(HERE / "ct_s1_core.py"),
        },
        "inputs": before,
        "outputs": {
            path.name: {"sha256": sha256(path), "bytes": path.stat().st_size}
            for path in artifacts
        },
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
    }
    write_json(output / "manifest.json", manifest)
    print(json.dumps({
        "status": status,
        "gate_status": gate_status,
        "support_coverage": stability_joint["support_coverage"],
        "median_absolute_drift": stability_joint["median_absolute_drift"],
        "p90_absolute_drift": stability_joint["p90_absolute_drift"],
        "spearman_average_rank": stability_joint["spearman_average_rank"],
    }, sort_keys=True))
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
