"""Bounded refresh for final-day CT-S1 ABS sources after publication lag."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT_DEFAULT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT_DEFAULT))

from acquire_ct_s1 import (  # noqa: E402
    BYTE_LIMIT,
    END,
    HTTP_ATTEMPT_LIMIT,
    MAX_ATTEMPTS_PER_URL,
    SINGLE_RESPONSE_LIMIT,
    USER_AGENT,
    stable_json,
)
from src.common import constant  # noqa: E402


DASHBOARD_URL = "https://baseballsavant.mlb.com/abs"


class RefreshError(RuntimeError):
    pass


def object_bytes(raw: Path) -> int:
    return sum(path.stat().st_size for path in (raw / "objects").iterdir() if path.is_file())


def dashboard_has_final_day(body: bytes) -> bool:
    try:
        rows = constant(body.decode("utf-8-sig"), "absSummaryData")
    except Exception as error:
        raise RefreshError("official ABS dashboard is not parseable") from error
    return any(str(row.get("game_date", ""))[:10] == END.isoformat() for row in rows)


def team_abs_is_valid(body: bytes) -> bool:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as error:
        raise RefreshError("team ABS response is not valid JSON") from error
    if not isinstance(payload.get("data"), list):
        raise RefreshError("team ABS response has no data list")
    return True


def _append(index: Path, receipt: dict) -> None:
    with index.open("a") as handle:
        handle.write(json.dumps(receipt, sort_keys=True) + "\n")


def _update_manifest(raw: Path, status: str) -> None:
    path = raw / "acquisition_manifest.json"
    manifest = json.loads(path.read_text())
    manifest["stored_bytes_total"] = object_bytes(raw)
    manifest["final_day_abs_refresh_status"] = status
    path.write_text(stable_json(manifest))


def fetch_replacement(
    raw: Path,
    index: Path,
    url: str,
    kind: str,
    prior: dict,
    validator,
    prior_http_attempts: int,
    opener=urllib.request.urlopen,
) -> tuple[dict, int]:
    errors = []
    for attempt in range(1, MAX_ATTEMPTS_PER_URL + 1):
        if prior_http_attempts + attempt > HTTP_ATTEMPT_LIMIT:
            raise RefreshError("HTTP-attempt cap exhausted")
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with opener(request, timeout=90) as response:
                declared = response.headers.get("Content-Length")
                if declared and int(declared) > SINGLE_RESPONSE_LIMIT:
                    raise RefreshError("declared response exceeds 10 MiB cap")
                body = response.read(SINGLE_RESPONSE_LIMIT + 1)
                if len(body) > SINGLE_RESPONSE_LIMIT:
                    raise RefreshError("response exceeds 10 MiB cap")
                content_type = response.headers.get("Content-Type")
                final_url = response.url
            digest = hashlib.sha256(body).hexdigest()
            path = raw / "objects" / digest
            if not path.exists():
                if object_bytes(raw) + len(body) > BYTE_LIMIT:
                    raise RefreshError("450 MiB acquisition byte cap exceeded")
                with path.open("xb") as handle:
                    handle.write(body)
            try:
                valid = bool(validator(body))
                validation_error = None if valid else "source remains incomplete"
            except RefreshError as error:
                valid = False
                validation_error = str(error)
            receipt = {
                "url": url,
                "kind": kind,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "attempts": attempt,
                "ok": valid,
                "sha256": digest,
                "path": str(path.relative_to(raw)),
                "bytes": len(body),
                "content_type": content_type,
                "final_url": final_url,
            }
            if valid:
                receipt["supersedes_sha256"] = prior["sha256"]
            else:
                receipt["error"] = validation_error
            _append(index, receipt)
            _update_manifest(raw, "IN_PROGRESS" if valid else "STILL_INCOMPLETE")
            if not valid:
                raise RefreshError(validation_error)
            return receipt, attempt
        except RefreshError:
            raise
        except Exception as error:
            errors.append(str(error))
            if attempt < MAX_ATTEMPTS_PER_URL:
                time.sleep(2)
    receipt = {
        "url": url,
        "kind": kind,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "attempts": MAX_ATTEMPTS_PER_URL,
        "ok": False,
        "errors": errors,
    }
    _append(index, receipt)
    raise RefreshError(f"refresh failed after two attempts: {errors}")


def refresh(raw: Path, opener=urllib.request.urlopen) -> dict:
    index = raw / "receipts.jsonl"
    manifest = raw / "acquisition_manifest.json"
    if not index.is_file() or not manifest.is_file():
        raise RefreshError("acquisition receipt or manifest is missing")
    receipts = [json.loads(line) for line in index.read_text().splitlines() if line.strip()]
    prior_http_attempts = sum(int(row.get("attempts", 0)) for row in receipts)
    successes = {}
    successful_history = {}
    for row in receipts:
        if row.get("ok"):
            successes[row["url"]] = row
            successful_history.setdefault(row["url"], []).append(row)
    if DASHBOARD_URL not in successes:
        raise RefreshError("original ABS dashboard receipt is missing")
    team_urls = sorted(url for url, row in successes.items() if row.get("kind") == "abs")
    if len(team_urls) != 30:
        raise RefreshError(f"expected 30 team ABS sources, found {len(team_urls)}")

    calls = 0
    dashboard = successes[DASHBOARD_URL]
    dashboard_body = (raw / dashboard["path"]).read_bytes()
    if not dashboard_has_final_day(dashboard_body):
        dashboard, used = fetch_replacement(
            raw, index, DASHBOARD_URL, "abs_dashboard", dashboard,
            dashboard_has_final_day, prior_http_attempts, opener,
        )
        calls += 1
        prior_http_attempts += used

    refreshed_teams = 0
    for url in team_urls:
        history = successful_history[url]
        if any(row.get("supersedes_sha256") for row in history):
            refreshed_teams += 1
            continue
        replacement, used = fetch_replacement(
            raw, index, url, "abs", successes[url], team_abs_is_valid,
            prior_http_attempts, opener,
        )
        successes[url] = replacement
        prior_http_attempts += used
        calls += 1
        refreshed_teams += 1

    _update_manifest(raw, "REFRESHED_PENDING_PREFLIGHT")
    return {
        "status": "REFRESHED_PENDING_PREFLIGHT",
        "date": END.isoformat(),
        "network_calls_this_run": calls,
        "team_sources_refreshed": refreshed_teams,
        "dashboard_final_day_present": True,
        "stored_bytes_total": object_bytes(raw),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--owner-risk-accepted", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(stable_json({
            "status": "DRY_RUN_NO_NETWORK",
            "date": END.isoformat(),
            "sequence": "dashboard first; 30 team sources only after dashboard completeness",
            "maximum_unique_urls": 31,
            "maximum_http_attempts": 62,
        }), end="")
        return 0
    if not args.owner_risk_accepted:
        raise SystemExit("--owner-risk-accepted is required with --execute")
    try:
        result = refresh(args.root.resolve() / "data/ct_s1/raw")
    except RefreshError as error:
        print(stable_json({"status": "STOPPED", "error": str(error)}), end="")
        return 2
    print(stable_json(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
