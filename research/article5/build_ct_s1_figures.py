"""Build the reviewable CT-S1 publication figure package.

The builder validates the content-addressed public-claim sources, emits one
source table per figure, and renders deterministic SVG and PNG drafts. It does
not modify the article site or authorize publication.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DEFAULT_SPEC = HERE / "CT_S1_FIGURE_SPEC.json"
DEFAULT_REGISTRY = HERE / "CT_S1_PUBLIC_CLAIMS.json"
DEFAULT_OUTPUT = HERE / "figures"

NAVY = "#0F3D6E"
GOLD = "#A67C2D"
DARK_GOLD = "#6F4E0A"
CHARCOAL = "#2D3748"
SLATE = "#6B7280"
IVORY = "#FAFAF8"
WHITE = "#FFFFFF"
LINE = "#D8DCE2"
SOFT_BLUE = "#EEF4FA"
SOFT_GOLD = "#F8F2E7"

FIGURE_SIZE = (12, 7.5)
PNG_DPI = 160


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def claim(registry: dict[str, Any], claim_id: str) -> dict[str, Any]:
    matches = [item for item in registry["claims"] if item["claim_id"] == claim_id]
    if len(matches) != 1:
        raise ValueError(f"expected one claim {claim_id}, found {len(matches)}")
    return matches[0]


def validate_claim_sources(registry: dict[str, Any], claim_ids: set[str]) -> None:
    for claim_id in sorted(claim_ids):
        item = claim(registry, claim_id)
        for source in item["sources"]:
            path = ROOT / source["artifact"]
            if not path.is_file():
                raise FileNotFoundError(path)
            actual = sha256(path)
            if actual != source["sha256"]:
                raise ValueError(
                    f"source hash mismatch for {source['artifact']}: "
                    f"{actual} != {source['sha256']}"
                )


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def one_row(rows: list[dict[str, str]], **filters: str) -> dict[str, str]:
    matches = [
        row for row in rows if all(row.get(key) == value for key, value in filters.items())
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one row for {filters}, found {len(matches)}")
    return matches[0]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def count_label(scenario_id: str) -> str:
    parts = scenario_id.split("|")
    return f"{parts[2]}-{parts[3]}"


def source_tables(registry: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    c05 = claim(registry, "CTS11-C05")
    audit_source = c05["sources"][0]["artifact"]
    cells_source = c05["sources"][1]["artifact"]
    audit = csv_rows(ROOT / audit_source)
    eligible = one_row(audit, contrast_class="ordinary", article_eligible="True")
    cells = csv_rows(ROOT / cells_source)
    scenarios = [eligible["member_a_scenario_id"], eligible["member_b_scenario_id"]]

    figure2: list[dict[str, Any]] = []
    for scenario_id in scenarios:
        for period in ("development", "confirmation"):
            row = one_row(
                cells,
                contrast_class="ordinary",
                scenario_id=scenario_id,
                variant="reference_fixed_0.60",
                period=period,
            )
            figure2.append(
                {
                    "period": period,
                    "count": count_label(scenario_id),
                    "ct": row["ct"],
                    "scenario_id": scenario_id,
                    "claim_id": "CTS11-C05",
                    "content_class": "MODELED",
                }
            )

    c06 = claim(registry, "CTS11-C06")
    interval_path = ROOT / c06["sources"][0]["artifact"]
    intervals = csv_rows(interval_path)
    figure3: list[dict[str, Any]] = []
    for scenario_id in scenarios:
        row = one_row(
            intervals,
            period="confirmation",
            scenario_id=scenario_id,
            inventory="2",
        )
        figure3.append(
            {
                "count": count_label(scenario_id),
                "reference_ct": row["reference_ct"],
                "sampling_lower": row["sampling_ct_lower"],
                "sampling_upper": row["sampling_ct_upper"],
                "model_spread_lower": row["model_spread_low"],
                "model_spread_upper": row["model_spread_high"],
                "sampling_replicates": row["sampling_finite_replicates"],
                "claim_ids": "CTS11-C05|CTS11-C06",
                "content_class": "MODELED",
            }
        )

    c03 = claim(registry, "CTS11-C03")
    temporal_path = ROOT / c03["sources"][0]["artifact"]
    temporal = read_json(temporal_path)["temporal_stability"]["joint"]
    c04 = claim(registry, "CTS11-C04")
    disclosure_path = ROOT / c04["sources"][0]["artifact"]
    disclosure = csv_rows(disclosure_path)
    figure4: list[dict[str, Any]] = [
        {
            "metric": "median_absolute_drift",
            "period": "development_to_confirmation",
            "numerator": "",
            "denominator": str(temporal["finite_matched_rows"]),
            "value": f"{temporal['median_absolute_drift']:.15g}",
            "unit": "threshold_proportion",
            "claim_id": "CTS11-C03",
            "content_class": "MODELED",
        },
        {
            "metric": "p90_absolute_drift",
            "period": "development_to_confirmation",
            "numerator": "",
            "denominator": str(temporal["finite_matched_rows"]),
            "value": f"{temporal['p90_absolute_drift']:.15g}",
            "unit": "threshold_proportion",
            "claim_id": "CTS11-C03",
            "content_class": "MODELED",
        },
        {
            "metric": "spearman_average_rank",
            "period": "development_to_confirmation",
            "numerator": "",
            "denominator": str(temporal["finite_matched_rows"]),
            "value": f"{temporal['spearman_average_rank']:.15g}",
            "unit": "correlation",
            "claim_id": "CTS11-C03",
            "content_class": "MODELED",
        },
    ]
    for period in ("development", "confirmation"):
        complete = sum(
            row["period"] == period
            and row["supported"] == "True"
            and row["model_spread_complete"] == "True"
            for row in disclosure
        )
        material = sum(
            row["period"] == period
            and row["supported"] == "True"
            and row["model_spread_complete"] == "True"
            and row["model_spread_label"] == "MATERIAL_MODEL_DISAGREEMENT"
            for row in disclosure
        )
        figure4.append(
            {
                "metric": "material_model_disagreement",
                "period": period,
                "numerator": str(material),
                "denominator": str(complete),
                "value": f"{material / complete:.15g}",
                "unit": "share_of_complete_rows",
                "claim_id": "CTS11-C04",
                "content_class": "MODELED",
            }
        )

    figure1 = [
        {
            "outcome": "correct_challenge",
            "call_effect": "corrected",
            "immediate_value": "+V",
            "inventory_effect": "retained",
            "future_value": "0",
            "claim_id": "CTS11-C01",
            "content_class": "MODELED_CONCEPTUAL",
        },
        {
            "outcome": "failed_challenge",
            "call_effect": "unchanged",
            "immediate_value": "0",
            "inventory_effect": "one_unit_lost",
            "future_value": "-C",
            "claim_id": "CTS11-C01",
            "content_class": "MODELED_CONCEPTUAL",
        },
        {
            "outcome": "pass_incorrect_call",
            "call_effect": "unchanged",
            "immediate_value": "-V",
            "inventory_effect": "retained",
            "future_value": "0",
            "claim_id": "CTS11-C01",
            "content_class": "MODELED_CONCEPTUAL",
        },
    ]
    return {
        "figure1_three_prices": figure1,
        "figure2_one_state_two_counts": figure2,
        "figure3_two_uncertainties": figure3,
        "figure4_stability_and_disagreement": figure4,
    }


def configure() -> None:
    matplotlib.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 12,
            "text.color": CHARCOAL,
            "axes.labelcolor": CHARCOAL,
            "axes.edgecolor": LINE,
            "xtick.color": SLATE,
            "ytick.color": CHARCOAL,
            "figure.facecolor": IVORY,
            "axes.facecolor": IVORY,
            "savefig.facecolor": IVORY,
            "svg.hashsalt": "ct-s1.0-figures",
        }
    )


def heading(fig: plt.Figure, title: str, subtitle: str, label: str) -> None:
    fig.text(0.06, 0.945, label.upper(), color=DARK_GOLD, fontsize=10, fontweight="bold")
    fig.text(0.06, 0.89, title, color=NAVY, fontsize=25, fontweight="bold")
    fig.text(0.06, 0.845, subtitle, color=SLATE, fontsize=12)


def save_figure(fig: plt.Figure, output_dir: Path, stem: str) -> list[Path]:
    rendered = output_dir / "rendered"
    rendered.mkdir(parents=True, exist_ok=True)
    svg = rendered / f"{stem}.svg"
    png = rendered / f"{stem}.png"
    fig.savefig(
        svg,
        bbox_inches="tight",
        metadata={"Creator": "Pascal Institute CT-S1 figure builder", "Date": None},
    )
    svg.write_text(
        "\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines())
        + "\n",
        encoding="utf-8",
    )
    fig.savefig(
        png,
        dpi=PNG_DPI,
        bbox_inches="tight",
        metadata={"Software": "Pascal Institute CT-S1 figure builder"},
    )
    plt.close(fig)
    return [svg, png]


def render_figure1(output_dir: Path) -> list[Path]:
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7.5)
    ax.axis("off")
    heading(
        fig,
        "The Three Prices of an ABS Challenge",
        "Break-even compares challenge with pass; the third card restates V as the pass cost",
        "Conceptual • modeled values, not player confidence",
    )
    cards = [
        (0.5, SOFT_BLUE, NAVY, "CORRECT CHALLENGE", "Call corrected", "+V immediate value", "Challenge retained"),
        (4.25, SOFT_GOLD, GOLD, "FAILED CHALLENGE", "Call unchanged", "−C future value", "One unit consumed"),
        (8.0, WHITE, SLATE, "PASS, CALL WAS WRONG", "Call unchanged", "V opportunity cost", "Same V; not an added payoff"),
    ]
    for x, face, edge, title, line1, line2, line3 in cards:
        patch = FancyBboxPatch(
            (x, 2.55), 3.35, 2.65,
            boxstyle="round,pad=0.035,rounding_size=0.12",
            linewidth=1.8, edgecolor=edge, facecolor=face,
        )
        ax.add_patch(patch)
        ax.text(x + 0.25, 4.75, title, color=edge, fontsize=10, fontweight="bold")
        ax.text(x + 0.25, 4.15, line1, fontsize=13, fontweight="bold", color=CHARCOAL)
        ax.text(x + 0.25, 3.58, line2, fontsize=12, color=CHARCOAL)
        ax.text(x + 0.25, 3.05, line3, fontsize=11, color=SLATE)
    ax.text(6, 1.72, "PASS IS THE ZERO BASELINE", ha="center", color=SLATE, fontsize=10, fontweight="bold")
    ax.text(6, 1.08, "CT-S1 Challenge Threshold =  C  /  (V + C)", ha="center", color=NAVY, fontsize=19, fontweight="bold")
    ax.text(6, 0.45, "V = correction value  •  C = future inventory value  •  fixed-path reference evaluator", ha="center", color=SLATE, fontsize=10)
    return save_figure(fig, output_dir, "figure1_three_prices")


def render_figure2(rows: list[dict[str, Any]], output_dir: Path) -> list[Path]:
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    fig.subplots_adjust(left=0.15, right=0.94, bottom=0.17, top=0.76)
    heading(
        fig,
        "Same Situation. One Count Changes.",
        "One prespecified count comparison met the published display rule; two did not",
        "Modeled • reference evaluator, not player confidence or a player rule",
    )
    periods = {"development": (NAVY, "Development"), "confirmation": (GOLD, "Confirmation")}
    counts = ["1-1", "1-2"]
    y_base = {"1-1": 1, "1-2": 0}
    offsets = {"development": 0.10, "confirmation": -0.10}
    for count in counts:
        points = []
        for period, (color, label) in periods.items():
            row = one_row(rows, period=period, count=count)
            value = float(row["ct"]) * 100
            y = y_base[count] + offsets[period]
            ax.scatter(value, y, s=115, color=color, edgecolor=WHITE, linewidth=1.2, zorder=3, label=label if count == "1-1" else None)
            text_color = NAVY if period == "development" else DARK_GOLD
            ax.text(value + 0.35, y, f"{label}: {value:.1f}%", va="center", color=text_color, fontsize=10.5, fontweight="bold")
            points.append(value)
    ax.set_xlim(56, 70.5)
    ax.set_ylim(-0.55, 1.55)
    ax.set_yticks([0, 1], labels=["1–2\ncalled strike three", "1–1\ncall moves count to 1–2"])
    ax.set_xlabel("CT-S1 threshold under declared model assumptions (not player confidence)")
    ax.xaxis.set_major_formatter(lambda value, _: f"{value:.0f}%")
    ax.grid(axis="x", color=LINE, linewidth=0.8)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.text(0.06, 0.045, "Bottom 5th • offense • trailing 2+ • 0 out • bases empty • 2 units. Direction survived all eight conventions; magnitude did not.", color=SLATE, fontsize=9.5)
    return save_figure(fig, output_dir, "figure2_one_state_two_counts")


def render_figure3(rows: list[dict[str, Any]], output_dir: Path) -> list[Path]:
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    fig.subplots_adjust(left=0.14, right=0.94, bottom=0.18, top=0.75)
    heading(
        fig,
        "One Reference. Two Kinds of Uncertainty.",
        "Confirmation-period states from the displayed count comparison",
        "Modeled • reference evaluator, not player confidence or a player rule",
    )
    y_map = {"1-1": 1, "1-2": 0}
    for row in rows:
        y = y_map[row["count"]]
        spread_low = float(row["model_spread_lower"]) * 100
        spread_high = float(row["model_spread_upper"]) * 100
        sample_low = float(row["sampling_lower"]) * 100
        sample_high = float(row["sampling_upper"]) * 100
        reference = float(row["reference_ct"]) * 100
        spread_y = y - 0.10
        sample_y = y + 0.10
        ax.plot([spread_low, spread_high], [spread_y, spread_y], color=GOLD, linewidth=9, solid_capstyle="butt", zorder=1)
        ax.plot([sample_low, sample_high], [sample_y, sample_y], color=NAVY, linewidth=3, solid_capstyle="butt", zorder=2)
        ax.scatter(reference, sample_y, s=95, color=WHITE, edgecolor=NAVY, linewidth=2.5, zorder=3)
        ax.text(spread_low - 0.45, spread_y - 0.14, f"{spread_low:.1f}%", ha="right", color=DARK_GOLD, fontsize=9.5)
        ax.text(spread_high + 0.45, spread_y - 0.14, f"{spread_high:.1f}%", ha="left", color=DARK_GOLD, fontsize=9.5)
        ax.text(sample_low, sample_y + 0.15, f"{sample_low:.1f}%", ha="center", color=NAVY, fontsize=9)
        ax.text(sample_high, sample_y + 0.15, f"{sample_high:.1f}%", ha="center", color=NAVY, fontsize=9)
        ax.text(reference, sample_y + 0.27, f"Reference {reference:.1f}%", ha="center", color=NAVY, fontsize=10, fontweight="bold")
    ax.set_xlim(47, 79)
    ax.set_ylim(-0.55, 1.55)
    ax.set_yticks([0, 1], labels=["1–2", "1–1"])
    ax.set_xlabel("CT-S1 threshold under declared model assumptions (not player confidence)")
    ax.xaxis.set_major_formatter(lambda value, _: f"{value:.0f}%")
    ax.grid(axis="x", color=LINE, linewidth=0.8)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    legend = [
        Line2D([0], [0], color=NAVY, lw=3, marker="o", markerfacecolor=WHITE, markeredgewidth=2, label="95% conditional sampling interval"),
        Line2D([0], [0], color=GOLD, lw=8, label="CT Model Spread: min–max across 8 conventions"),
    ]
    ax.legend(handles=legend, frameon=False, loc="upper left")
    fig.text(0.06, 0.047, "Thin line + circle: conditional sampling interval. Thick band: CT Model Spread. Interval overlap is not a paired test; Fig. 2's direction survived all 8 conventions.", color=SLATE, fontsize=9.2)
    return save_figure(fig, output_dir, "figure3_two_uncertainties")


def render_figure4(rows: list[dict[str, Any]], output_dir: Path) -> list[Path]:
    fig, (left, right) = plt.subplots(1, 2, figsize=FIGURE_SIZE, gridspec_kw={"wspace": 0.38})
    fig.subplots_adjust(left=0.10, right=0.95, bottom=0.18, top=0.72)
    heading(
        fig,
        "Stable Through Time. Sensitive to Definition.",
        "These panels answer different questions and use different denominators",
        "Modeled • time stability and definition sensitivity",
    )
    median = float(one_row(rows, metric="median_absolute_drift")["value"]) * 100
    p90 = float(one_row(rows, metric="p90_absolute_drift")["value"]) * 100
    left.barh([1, 0], [median, p90], color=NAVY, height=0.48)
    left.set_yticks([0, 1], labels=["90th percentile", "Median"])
    left.set_xlim(0, 3.1)
    left.set_xticks([0, 1, 2, 3])
    left.xaxis.set_major_formatter(lambda value, _: f"{value:.0f} pp")
    left.grid(axis="x", color=LINE, linewidth=0.8)
    left.spines[["top", "right", "left"]].set_visible(False)
    left.tick_params(axis="y", length=0)
    for y, value in zip([1, 0], [median, p90]):
        left.text(value + 0.08, y, f"{value:.2f} pp", va="center", color=NAVY, fontweight="bold")
    left.set_title("Absolute reference drift\ndevelopment → confirmation\n22,584 supported rows", color=NAVY, fontweight="bold", loc="left")

    material = [row for row in rows if row["metric"] == "material_model_disagreement"]
    labels = ["Development", "Confirmation"]
    values = [float(one_row(material, period=period.lower())["value"]) * 100 for period in labels]
    right.barh([1, 0], values, color=GOLD, height=0.48)
    right.set_yticks([0, 1], labels=["Confirmation", "Development"])
    right.set_xlim(0, 100)
    right.xaxis.set_major_formatter(lambda value, _: f"{value:.0f}%")
    right.grid(axis="x", color=LINE, linewidth=0.8)
    right.spines[["top", "right", "left"]].set_visible(False)
    right.tick_params(axis="y", length=0)
    for y, value in zip([1, 0], values):
        right.text(value - 2, y, "ABOUT 98%", va="center", ha="right", color=CHARCOAL, fontsize=10, fontweight="bold")
    right.set_title("Material CT Model Spread (>10 pp)\n22,428 complete rows per period", color=NAVY, fontweight="bold", loc="left")
    fig.add_artist(Line2D([0.505, 0.505], [0.18, 0.70], transform=fig.transFigure, color=LINE, linewidth=1.4))
    fig.text(0.50, 0.090, "Do not net these results out: stability of one definition is not agreement across definitions.", ha="center", color=CHARCOAL, fontsize=10.5, fontweight="bold")
    return save_figure(fig, output_dir, "figure4_stability_and_disagreement")


def build(spec_path: Path, registry_path: Path, output_dir: Path) -> dict[str, Any]:
    configure()
    spec = read_json(spec_path)
    registry = read_json(registry_path)
    claim_ids = {
        claim_id
        for figure in spec["figures"]
        for claim_id in figure["claim_ids"]
        if claim_id != "CTS11-C08"
    }
    validate_claim_sources(registry, claim_ids)
    tables = source_tables(registry)
    source_dir = output_dir / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    output_files: list[Path] = []
    for name, rows in tables.items():
        path = source_dir / f"{name}.csv"
        write_csv(path, rows)
        output_files.append(path)

    output_files.extend(render_figure1(output_dir))
    output_files.extend(render_figure2(tables["figure2_one_state_two_counts"], output_dir))
    output_files.extend(render_figure3(tables["figure3_two_uncertainties"], output_dir))
    output_files.extend(render_figure4(tables["figure4_stability_and_disagreement"], output_dir))

    review = output_dir / "FIGURE_REVIEW.md"
    review_lines = [
        "# CT-S1 Figure Review Package",
        "",
        "These are reviewable publication drafts, not deployed site assets.",
        "",
    ]
    for figure in spec["figures"]:
        review_lines.extend(
            [
                f"## {figure['title']}",
                "",
                f"- Content class: {', '.join(figure['content_class'])}",
                f"- Claims: {', '.join(figure['claim_ids'])}",
                f"- Alt text: {figure['alt_text']}",
                f"- Caption: {figure['caption']}",
                f"- Prohibitions: {'; '.join(figure['prohibitions'])}",
                "",
            ]
        )
    review.write_text("\n".join(review_lines), encoding="utf-8")
    output_files.append(review)

    manifest = {
        "research_identity": "CT-S1",
        "metric_version": spec["metric_version"],
        "status": "PASS_FIGURES_READY_FOR_EDITORIAL_REVIEW",
        "inputs": {
            str(spec_path.relative_to(ROOT)): sha256(spec_path),
            str(registry_path.relative_to(ROOT)): sha256(registry_path),
        },
        "environment": {
            "python": platform.python_version(),
            "matplotlib": matplotlib.__version__,
        },
        "outputs": {
            str(path.relative_to(output_dir)): sha256(path)
            for path in sorted(output_files)
        },
        "restrictions": {
            "site_deployment_authorized": False,
            "playbook_authorized": False,
            "player_grading_authorized": False,
        },
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = build(args.spec.resolve(), args.registry.resolve(), args.output_dir.resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
