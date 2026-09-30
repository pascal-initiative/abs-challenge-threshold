"""Create Article 3's descriptive recognized-count table from accepted Sprint 4."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


COMPLETE_RESULTS_SHA256 = "8ef844441d9302e3603e942c558e545cb9506ac9815396061039a68d2fb4640d"
ADJUSTED_LEADERBOARD_SHA256 = "b2dc3e5e19c1323f0bc398fa1f5f677aa0c88f324b324b49566e3f4359855359"
SPRINT4_MANIFEST_SHA256 = "a7d68a88c60ac3b9247f23b77e7bb66283578560b9ef6a2d0c8547bdc45fde3a"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def pp(value: float) -> str:
    return f"{100 * value:+.1f} pp"


def run(root: Path) -> None:
    results_path = root / "data/analysis/sprint4/complete_batter_results.csv"
    leaderboard_path = root / "data/analysis/sprint4/ranking_eligible_leaderboard.csv"
    manifest_path = root / "artifacts/sprint4/run_manifest.json"
    expected = {
        results_path: COMPLETE_RESULTS_SHA256,
        leaderboard_path: ADJUSTED_LEADERBOARD_SHA256,
        manifest_path: SPRINT4_MANIFEST_SHA256,
    }
    for path, digest in expected.items():
        if sha256(path) != digest:
            raise RuntimeError(f"Accepted Sprint 4 input hash mismatch: {path}")

    results = read_csv(results_path)
    leaderboard = read_csv(leaderboard_path)
    adjusted_rank = {row["batter_id"]: int(row["adjusted_rank"]) for row in leaderboard}

    # This is a descriptive count sort only. Batter ID resolves count ties so the
    # requested output has exactly ten rows without introducing another metric.
    ordered = sorted(results, key=lambda row: (-int(row["recognized"]), int(row["batter_id"])))
    selected = ordered[:10]
    cutoff_count = int(selected[-1]["recognized"])
    tied_but_excluded = [
        row for row in ordered[10:] if int(row["recognized"]) == cutoff_count
    ]

    table = []
    for position, row in enumerate(selected, 1):
        rank = adjusted_rank.get(row["batter_id"])
        table.append({
            "recognized_count_sort_position": position,
            "batter_id": int(row["batter_id"]),
            "batter": row["batter_name"],
            "opportunities": int(row["opportunities"]),
            "recognized": int(row["recognized"]),
            "raw_recognition_rate": float(row["raw_recognition_rate"]),
            "expected_recognized": float(row["expected_recognized"]),
            "expected_recognition_rate": float(row["expected_recognition_rate"]),
            "adjusted_effect": float(row["adjusted_effect"]),
            "adjusted_leaderboard_rank": rank,
        })

    comparison = sorted([
        {
            "accepted_adjusted_leaderboard_rank": row["adjusted_leaderboard_rank"],
            "batter_id": row["batter_id"],
            "batter": row["batter"],
            "recognized_count_sort_position": row["recognized_count_sort_position"],
            "recognized": row["recognized"],
            "opportunities": row["opportunities"],
            "adjusted_effect": row["adjusted_effect"],
        }
        for row in table
    ], key=lambda row: row["accepted_adjusted_leaderboard_rank"])

    artifact_dir = root / "artifacts/publication_validation/article3"
    doc_path = root / "docs/publication_validation/article3/recognized_count_top10.md"
    table_csv = artifact_dir / "recognized_count_top10.csv"
    table_json = artifact_dir / "recognized_count_top10.json"
    comparison_csv = artifact_dir / "recognized_count_top10_vs_adjusted_leaderboard.csv"
    comparison_json = artifact_dir / "recognized_count_top10_vs_adjusted_leaderboard.json"
    output_manifest = artifact_dir / "recognized_count_top10_manifest.json"
    hash_path = artifact_dir / "recognized_count_top10_hashes.sha256"

    write_csv(table_csv, table)
    table_json.write_text(json.dumps(table, indent=2, ensure_ascii=False) + "\n")
    write_csv(comparison_csv, comparison)
    comparison_json.write_text(json.dumps(comparison, indent=2, ensure_ascii=False) + "\n")

    md = [
        "# Article 3 — Most Recognized Eligible Incorrect Called Strikes",
        "",
        "Descriptive sort of the immutable accepted Sprint 4 `complete_batter_results` artifact. Players are ordered by recognized count descending; batter ID ascending is used only to resolve ties and return exactly 10 rows.",
        "",
        "| Batter | Opportunities | Recognized | Raw recognition rate | Expected recognized | Expected recognition rate | Adjusted effect | Adjusted leaderboard rank |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in table:
        md.append(
            f"| {row['batter']} | {row['opportunities']} | {row['recognized']} | "
            f"{pct(row['raw_recognition_rate'])} | {row['expected_recognized']:.2f} | "
            f"{pct(row['expected_recognition_rate'])} | {pp(row['adjusted_effect'])} | "
            f"{row['adjusted_leaderboard_rank'] if row['adjusted_leaderboard_rank'] is not None else '—'} |"
        )
    md.extend([
        "",
        "## Comparison with the accepted adjusted leaderboard",
        "",
        "| Adjusted leaderboard rank | Batter | Recognized-count sort position | Recognized | Opportunities | Adjusted effect |",
        "|---:|---|---:|---:|---:|---:|",
    ])
    for row in comparison:
        md.append(
            f"| {row['accepted_adjusted_leaderboard_rank']} | {row['batter']} | "
            f"{row['recognized_count_sort_position']} | {row['recognized']} | "
            f"{row['opportunities']} | {pp(row['adjusted_effect'])} |"
        )
    md.extend([
        "",
        f"Cutoff note: {', '.join(row['batter_name'] for row in tied_but_excluded)} also recognized {cutoff_count} opportunities and was excluded only by the neutral batter-ID tie-break.",
        "",
        "The recognized-count order is descriptive volume, not a new skill ranking. Adjusted ranks are copied from the accepted Sprint 4 ranking-eligible leaderboard.",
    ])
    doc_path.write_text("\n".join(md) + "\n")

    outputs = [table_csv, table_json, comparison_csv, comparison_json, doc_path]
    output_manifest.write_text(json.dumps({
        "artifact": "Article 3 recognized-count top 10",
        "method": "recognized descending; batter_id ascending tie-break",
        "cutoff_tie": {
            "recognized": cutoff_count,
            "excluded_by_tie_break": [
                {"batter_id": int(row["batter_id"]), "batter": row["batter_name"]}
                for row in tied_but_excluded
            ],
        },
        "immutable_inputs": {
            str(path.relative_to(root)): digest for path, digest in expected.items()
        },
        "outputs": {
            str(path.relative_to(root)): sha256(path) for path in outputs
        },
    }, indent=2, ensure_ascii=False) + "\n")
    outputs.append(output_manifest)
    hash_path.write_text("".join(
        f"{sha256(path)}  {path.relative_to(root)}\n" for path in outputs
    ))

    # Re-verify accepted inputs after output creation.
    for path, digest in expected.items():
        if sha256(path) != digest:
            raise RuntimeError(f"Accepted Sprint 4 input changed: {path}")


if __name__ == "__main__":
    run(Path(__file__).resolve().parents[1])
