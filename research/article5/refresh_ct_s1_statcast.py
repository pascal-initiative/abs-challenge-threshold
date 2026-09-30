"""One-source refresh for the incomplete CT-S1 final-day Statcast export."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from acquire_ct_s1 import (
    BYTE_LIMIT,
    END,
    HTTP_ATTEMPT_LIMIT,
    MAX_ATTEMPTS_PER_URL,
    SINGLE_RESPONSE_LIMIT,
    USER_AGENT,
    stable_json,
)
from validate_ct_s1_raw import REQUIRED_STATCAST_COLUMNS


class RefreshError(RuntimeError):
    pass


def final_day_url() -> str:
    query = urlencode({
        "all": "true",
        "type": "details",
        "game_date_gt": END.isoformat(),
        "game_date_lt": END.isoformat(),
        "hfGT": "R|",
        "hfSea": "2026|",
    })
    return "https://baseballsavant.mlb.com/statcast_search/csv?" + query


def csv_rows(body: bytes) -> list[dict]:
    text = body.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    missing = REQUIRED_STATCAST_COLUMNS - set(reader.fieldnames or [])
    if missing:
        raise RefreshError(f"Statcast schema missing {sorted(missing)}")
    return list(reader)


def object_bytes(raw: Path) -> int:
    return sum(path.stat().st_size for path in (raw / "objects").iterdir() if path.is_file())


def refresh(raw: Path, opener=urllib.request.urlopen) -> dict:
    index = raw / "receipts.jsonl"
    manifest_path = raw / "acquisition_manifest.json"
    if not index.is_file() or not manifest_path.is_file():
        raise RefreshError("acquisition receipt or manifest is missing")
    receipts = [json.loads(line) for line in index.read_text().splitlines() if line.strip()]
    prior_http_attempts = sum(int(row.get("attempts", 0)) for row in receipts)
    url = final_day_url()
    successful = [row for row in receipts if row.get("ok") and row.get("url") == url]
    if not successful:
        raise RefreshError("original final-day Statcast receipt is missing")
    prior = successful[-1]
    prior_body = (raw / prior["path"]).read_bytes()
    if csv_rows(prior_body):
        raise RefreshError("final-day Statcast response is already populated")

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
                rows = csv_rows(body)
                validation_error = None
            except RefreshError as error:
                rows = []
                validation_error = str(error)
            receipt = {
                "url": url,
                "kind": "statcast",
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "attempts": attempt,
                "ok": bool(rows),
                "sha256": digest,
                "path": str(path.relative_to(raw)),
                "bytes": len(body),
                "content_type": content_type,
                "final_url": final_url,
            }
            if rows:
                receipt["supersedes_sha256"] = prior["sha256"]
            else:
                receipt["error"] = (
                    validation_error or "final-day Statcast response remains empty"
                )
            with index.open("a") as handle:
                handle.write(json.dumps(receipt, sort_keys=True) + "\n")
            manifest = json.loads(manifest_path.read_text())
            manifest["stored_bytes_total"] = object_bytes(raw)
            manifest["final_day_statcast_refresh_status"] = (
                "POPULATED" if rows else "STILL_EMPTY"
            )
            manifest_path.write_text(stable_json(manifest))
            if not rows:
                raise RefreshError(receipt["error"])
            return {
                "status": "REFRESHED_PENDING_PREFLIGHT",
                "date": END.isoformat(),
                "rows": len(rows),
                "bytes": len(body),
                "sha256": digest,
                "supersedes_sha256": prior["sha256"],
                "http_attempts": attempt,
            }
        except RefreshError:
            raise
        except Exception as error:
            errors.append(str(error))
            if attempt < MAX_ATTEMPTS_PER_URL:
                time.sleep(2)
    failure = {
        "url": url,
        "kind": "statcast",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "attempts": MAX_ATTEMPTS_PER_URL,
        "ok": False,
        "errors": errors,
    }
    with index.open("a") as handle:
        handle.write(json.dumps(failure, sort_keys=True) + "\n")
    raise RefreshError(f"refresh failed after two attempts: {errors}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--owner-risk-accepted", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(stable_json({
            "status": "DRY_RUN_NO_NETWORK",
            "date": END.isoformat(),
            "maximum_http_attempts": MAX_ATTEMPTS_PER_URL,
            "single_response_byte_limit": SINGLE_RESPONSE_LIMIT,
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
