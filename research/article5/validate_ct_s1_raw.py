"""Offline CTS1/CTS2 preflight for an acquired CT-S1 raw snapshot."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT_DEFAULT = HERE.parents[1]
sys.path.insert(0, str(ROOT_DEFAULT))

from research.article5.acquire_ct_s1 import (  # noqa: E402
    BYTE_LIMIT,
    END,
    GAME_FEED_LIMIT,
    HTTP_ATTEMPT_LIMIT,
    SINGLE_RESPONSE_LIMIT,
    START,
    UNIQUE_REQUEST_LIMIT,
    final_games,
    fixed_jobs,
    schedule_url,
    stable_json,
)
from src.common import constant  # noqa: E402


REQUIRED_STATCAST_COLUMNS = {
    "game_date", "game_pk", "at_bat_number", "pitch_number", "description",
    "pitch_type", "stand", "p_throws", "batter", "pitcher", "fielder_2",
    "release_speed", "release_spin_rate", "spin_axis", "pfx_x", "pfx_z",
    "release_pos_x", "release_pos_y", "release_pos_z", "release_extension",
    "plate_x", "plate_z", "sz_top", "sz_bot", "balls", "strikes",
    "outs_when_up", "on_1b", "on_2b", "on_3b", "home_score", "away_score",
}
ALLOWED_RECEIPT_KEYS = {
    "url", "kind", "retrieved_at", "attempts", "ok", "sha256", "path",
    "bytes", "content_type", "final_url", "blocked", "error", "errors",
    "supersedes_sha256",
}


class PreflightError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_object(raw: Path, relative: str) -> Path:
    path = (raw / relative).resolve()
    objects = (raw / "objects").resolve()
    try:
        path.relative_to(objects)
    except ValueError as error:
        raise PreflightError(f"receipt path escapes objects directory: {relative}") from error
    return path


def load_snapshot(raw: Path):
    index = raw / "receipts.jsonl"
    manifest_path = raw / "acquisition_manifest.json"
    if not index.is_file() or not manifest_path.is_file():
        raise PreflightError("receipt index or acquisition manifest is missing")
    receipts = [json.loads(line) for line in index.read_text().splitlines() if line.strip()]
    if not receipts:
        raise PreflightError("receipt index is empty")
    unknown = sorted({key for row in receipts for key in row if key not in ALLOWED_RECEIPT_KEYS})
    if unknown:
        raise PreflightError(f"unexpected receipt fields: {unknown}")
    successes = defaultdict(list)
    for row in receipts:
        if row.get("ok"):
            successes[row["url"]].append(row)
    for url, rows in successes.items():
        prior = None
        for row in rows:
            if prior is not None and row["sha256"] != prior["sha256"]:
                if row.get("supersedes_sha256") != prior["sha256"]:
                    raise PreflightError(f"unaudited successful URL hash conflict: {url}")
            prior = row
    latest = {url: rows[-1] for url, rows in successes.items()}
    bodies = {}
    receipt_object_paths = {}
    for row in receipts:
        if not row.get("sha256") or not row.get("path"):
            continue
        path = _safe_object(raw, row["path"])
        if not path.is_file():
            raise PreflightError(f"missing raw object for {row.get('url')}")
        if path.stat().st_size != int(row["bytes"]):
            raise PreflightError(f"byte count mismatch for {row.get('url')}")
        if path.stat().st_size > SINGLE_RESPONSE_LIMIT:
            raise PreflightError(f"single response exceeds cap for {row.get('url')}")
        if sha256(path) != row["sha256"] or path.name != row["sha256"]:
            raise PreflightError(f"SHA-256 mismatch for {row.get('url')}")
        receipt_object_paths[path] = path.stat().st_size
    actual_objects = {
        path.resolve() for path in (raw / "objects").iterdir() if path.is_file()
    }
    if actual_objects != set(receipt_object_paths):
        raise PreflightError("object directory does not match receipt inventory")
    for url, row in latest.items():
        path = _safe_object(raw, row["path"])
        bodies[url] = path.read_bytes()
    if len(latest) > UNIQUE_REQUEST_LIMIT:
        raise PreflightError("unique-request cap exceeded")
    if sum(int(row.get("attempts", 0)) for row in receipts) > HTTP_ATTEMPT_LIMIT:
        raise PreflightError("HTTP-attempt cap exceeded")
    if sum(receipt_object_paths.values()) > BYTE_LIMIT:
        raise PreflightError("stored-object byte cap exceeded")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("research_identity") != "CT-S1":
        raise PreflightError("wrong research identity in acquisition manifest")
    if manifest.get("status") != "ACQUIRED_PENDING_RECONCILIATION":
        raise PreflightError("acquisition manifest is not awaiting reconciliation")
    return receipts, latest, bodies, manifest


def validate_snapshot(raw: Path) -> dict:
    protected = {
        str(path.relative_to(raw)): sha256(path)
        for path in sorted(raw.rglob("*"))
        if path.is_file()
    }
    receipts, latest, bodies, manifest = load_snapshot(raw)
    if schedule_url() not in bodies:
        raise PreflightError("frozen schedule response is missing")
    try:
        schedule = json.loads(bodies[schedule_url()])
    except json.JSONDecodeError as error:
        raise PreflightError("schedule is not valid JSON") from error
    games = final_games(schedule)
    expected_jobs = fixed_jobs(games)
    expected = {schedule_url(): "schedule", **dict(expected_jobs)}
    if set(latest) != set(expected):
        missing = sorted(set(expected) - set(latest))
        extra = sorted(set(latest) - set(expected))
        raise PreflightError(f"source set mismatch; missing={missing}, extra={extra}")
    for url, kind in expected.items():
        if latest[url]["kind"] != kind:
            raise PreflightError(f"source kind mismatch for {url}")

    game_ids = {int(game["gamePk"]) for game in games}
    abs_records = {}
    for url, kind in expected_jobs:
        if kind == "feed":
            try:
                feed = json.loads(bodies[url])
            except json.JSONDecodeError as error:
                raise PreflightError(f"invalid feed JSON: {url}") from error
            if int(feed.get("gamePk", -1)) not in game_ids:
                raise PreflightError(f"feed game is outside schedule: {url}")
            if feed.get("gameData", {}).get("status", {}).get("abstractGameState") != "Final":
                raise PreflightError(f"feed is not final: {url}")
        elif kind == "abs":
            try:
                payload = json.loads(bodies[url])
            except json.JSONDecodeError as error:
                raise PreflightError(f"invalid ABS JSON: {url}") from error
            if not isinstance(payload.get("data"), list):
                raise PreflightError(f"ABS data list missing: {url}")
            for record in payload["data"]:
                record_date = str(record.get("game_date", ""))[:10]
                if not START.isoformat() <= record_date <= END.isoformat():
                    continue
                try:
                    key = (int(record["game_pk"]), str(record["play_id"]))
                except (KeyError, TypeError, ValueError) as error:
                    raise PreflightError(f"malformed ABS challenge record: {url}") from error
                if key[0] not in game_ids:
                    raise PreflightError(f"ABS challenge is outside schedule: {url}")
                if key in abs_records and abs_records[key] != record_date:
                    raise PreflightError(f"ABS duplicate changes game date: {url}")
                abs_records.setdefault(key, record_date)
        elif kind == "statcast":
            text = bodies[url].decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(text))
            columns = set(reader.fieldnames or [])
            missing = sorted(REQUIRED_STATCAST_COLUMNS - columns)
            if missing:
                raise PreflightError(f"Statcast schema missing {missing}: {url}")
            rows = list(reader)
            if not rows:
                raise PreflightError(f"empty Statcast response: {url}")
            if any(int(float(row["game_pk"])) not in game_ids for row in rows):
                raise PreflightError(f"Statcast contains out-of-window game: {url}")
            requested_date = url.split("game_date_gt=")[1][:10]
            if any(row["game_date"] != requested_date for row in rows):
                raise PreflightError(f"Statcast response crosses requested date: {url}")

    dashboard_url = "https://baseballsavant.mlb.com/abs"
    dashboard = bodies[dashboard_url].decode("utf-8-sig")
    try:
        daily = constant(dashboard, "absSummaryData")
    except Exception as error:
        raise PreflightError("official ABS daily summary is not parseable") from error
    game_dates = {game["officialDate"] for game in games}
    daily_rows = [
        row for row in daily
        if START.isoformat() <= row["game_date"][:10] <= END.isoformat()
    ]
    daily_dates = {row["game_date"][:10] for row in daily_rows}
    if daily_dates != game_dates:
        raise PreflightError("official ABS daily dates do not match completed game dates")
    if not daily_rows or any("challenges" not in row for row in daily_rows):
        raise PreflightError("official ABS daily challenge totals are incomplete")
    observed_counts = Counter(abs_records.values())
    expected_daily = {
        row["game_date"][:10]: int(row["challenges"])
        for row in daily_rows
    }
    observed_daily = {
        day: int(observed_counts.get(day, 0))
        for day in expected_daily
    }
    if observed_daily != expected_daily:
        raise PreflightError("team ABS records do not reconcile to official daily totals")

    after = {
        str(path.relative_to(raw)): sha256(path)
        for path in sorted(raw.rglob("*"))
        if path.is_file()
    }
    if after != protected:
        raise PreflightError("validator modified the immutable raw snapshot")
    kind_counts = Counter(row["kind"] for row in latest.values())
    result = {
        "research_identity": "CT-S1",
        "status": "PASS_CTS1_READY_FOR_CTS2_PROCESSING",
        "window": {"start": START.isoformat(), "end": END.isoformat()},
        "final_games": len(games),
        "source_counts": dict(sorted(kind_counts.items())),
        "unique_urls": len(latest),
        "receipt_rows": len(receipts),
        "source_sha256s": sorted({row["sha256"] for row in latest.values()}),
        "stored_unique_object_bytes": sum(
            path.stat().st_size for path in (raw / "objects").iterdir()
            if path.is_file()
        ),
        "official_daily_challenges": int(sum(row["challenges"] for row in daily_rows)),
        "deduplicated_team_abs_challenges": len(abs_records),
        "raw_snapshot_sha256": hashlib.sha256(
            stable_json(protected).encode("utf-8")
        ).hexdigest(),
        "acquisition_manifest_final_games": manifest.get("final_games"),
        "next_command": (
            f"python -m src.pipeline --start {START} --end {END} "
            "--raw-dir data/ct_s1/raw --output data/ct_s1/reconstructed"
        ),
    }
    if manifest.get("final_games") != len(games):
        raise PreflightError("manifest final-game count does not reconcile")
    if manifest.get("window") != result["window"]:
        raise PreflightError("manifest window does not reconcile")
    if manifest.get("stored_bytes_total") != result["stored_unique_object_bytes"]:
        raise PreflightError("manifest stored-byte total does not reconcile")
    expected_limits = {
        "unique_requests": UNIQUE_REQUEST_LIMIT,
        "http_attempts": HTTP_ATTEMPT_LIMIT,
        "game_feeds": GAME_FEED_LIMIT,
        "bytes": BYTE_LIMIT,
        "single_response_bytes": SINGLE_RESPONSE_LIMIT,
    }
    if manifest.get("limits") != expected_limits:
        raise PreflightError("manifest limits do not match frozen limits")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--raw-dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    raw = (args.raw_dir or root / "data/ct_s1/raw").resolve()
    output = (args.output or root / "data/ct_s1/preflight/validation.json").resolve()
    try:
        result = validate_snapshot(raw)
    except PreflightError as error:
        print(stable_json({"status": "FAIL", "error": str(error)}), end="")
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(stable_json(result))
    print(stable_json(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
