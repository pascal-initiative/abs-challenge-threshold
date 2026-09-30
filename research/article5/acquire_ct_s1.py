"""Bounded, resumable acquisition for the CT-S1 confirmation window.

Network access is impossible without both explicit command-line switches. The
script also refuses to run before the frozen regular-season window is complete.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode


START = date(2026, 9, 11)
END = date(2026, 9, 27)
EARLIEST_EXECUTION = date(2026, 9, 28)
UNIQUE_REQUEST_LIMIT = 326
HTTP_ATTEMPT_LIMIT = 652
GAME_FEED_LIMIT = 275
BYTE_LIMIT = 450 * 1024 * 1024
SINGLE_RESPONSE_LIMIT = 10 * 1024 * 1024
MAX_ATTEMPTS_PER_URL = 2
REQUEST_DELAY_SECONDS = 0.25
USER_AGENT = "Pascal-ABS-Research/CT-S1 (owner-directed public research)"


class AcquisitionError(RuntimeError):
    pass


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def stable_json(value) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def schedule_url() -> str:
    return "https://statsapi.mlb.com/api/v1/schedule?" + urlencode({
        "sportId": 1,
        "startDate": START.isoformat(),
        "endDate": END.isoformat(),
        "gameType": "R",
    })


def fixed_jobs(games: list[dict]) -> list[tuple[str, str]]:
    if len(games) > GAME_FEED_LIMIT:
        raise AcquisitionError(
            f"schedule contains {len(games)} final games; cap is {GAME_FEED_LIMIT}"
        )
    jobs = [("https://statsapi.mlb.com" + game["link"], "feed") for game in games]
    teams = sorted({
        int(game["teams"][side]["team"]["id"])
        for game in games
        for side in ("home", "away")
    })
    if len(teams) != 30:
        raise AcquisitionError(f"expected 30 MLB teams, found {len(teams)}")
    for team in teams:
        query = urlencode({
            "year": "2026",
            "challengeType": "team-summary",
            "gameType": "regular",
            "level": "mlb",
            "id": team,
            "groupBy": "",
        })
        jobs.append((
            f"https://baseballsavant.mlb.com/leaderboard/services/abs/{team}?{query}",
            "abs",
        ))
    current = START
    while current <= END:
        query = urlencode({
            "all": "true",
            "type": "details",
            "game_date_gt": current.isoformat(),
            "game_date_lt": current.isoformat(),
            "hfGT": "R|",
            "hfSea": "2026|",
        })
        jobs.append((
            "https://baseballsavant.mlb.com/statcast_search/csv?" + query,
            "statcast",
        ))
        current += timedelta(days=1)
    jobs.append(("https://baseballsavant.mlb.com/abs", "abs_dashboard"))
    if 1 + len(jobs) > UNIQUE_REQUEST_LIMIT:
        raise AcquisitionError("planned unique requests exceed the frozen cap")
    return jobs


def final_games(schedule: dict) -> list[dict]:
    candidates = []
    for day in schedule.get("dates", []):
        for game in day.get("games", []):
            official = date.fromisoformat(game["officialDate"])
            if not START <= official <= END or game.get("gameType") != "R":
                continue
            if game.get("status", {}).get("abstractGameState") != "Final":
                raise AcquisitionError(
                    f"game {game.get('gamePk')} is not final; acquisition is premature"
                )
            candidates.append(game)
    if not candidates:
        raise AcquisitionError("schedule contains no final regular-season games")

    # MLB can list a postponed game under both its original schedule date and
    # its completed date while retaining one gamePk, officialDate, and feed.
    # Collapse only that evidenced representation. Any identity conflict or
    # ambiguity about the completed representation remains a hard stop.
    by_game = {}
    for game in candidates:
        by_game.setdefault(int(game["gamePk"]), []).append(game)
    games = []
    for game_pk, listings in sorted(by_game.items()):
        if len(listings) == 1:
            games.append(listings[0])
            continue
        identities = {
            (
                game["officialDate"],
                game.get("gameType"),
                game.get("link"),
                int(game["teams"]["home"]["team"]["id"]),
                int(game["teams"]["away"]["team"]["id"]),
            )
            for game in listings
        }
        if len(identities) != 1:
            raise AcquisitionError(f"conflicting duplicate listings for game {game_pk}")
        completed = [
            game for game in listings
            if game.get("status", {}).get("detailedState") == "Final"
        ]
        if len(completed) != 1:
            raise AcquisitionError(f"ambiguous duplicate listings for game {game_pk}")
        games.append(completed[0])
    return sorted(games, key=lambda game: (game["officialDate"], int(game["gamePk"])))


class BoundedDownloader:
    def __init__(self, raw: Path, opener=urllib.request.urlopen):
        self.raw = raw
        self.objects = raw / "objects"
        self.index = raw / "receipts.jsonl"
        self.opener = opener
        self.raw.mkdir(parents=True, exist_ok=True)
        self.objects.mkdir(exist_ok=True)
        prior = []
        if self.index.exists():
            prior = [json.loads(line) for line in self.index.read_text().splitlines()]
        self.cache = {row["url"]: row for row in prior if row.get("ok")}
        self.unique_requests = 0
        self.http_attempts = 0
        self.downloaded_bytes = 0
        self.stored_bytes = sum(int(row["bytes"]) for row in self.cache.values())
        if self.stored_bytes > BYTE_LIMIT:
            raise AcquisitionError("existing isolated cache exceeds 450 MiB cap")

    def _append(self, receipt: dict) -> None:
        with self.index.open("a") as handle:
            handle.write(json.dumps(receipt, sort_keys=True) + "\n")

    def _cached(self, row: dict) -> bytes:
        body = (self.raw / row["path"]).read_bytes()
        if sha256_bytes(body) != row["sha256"]:
            raise AcquisitionError(f"cached checksum mismatch for {row['url']}")
        return body

    def fetch(self, url: str, kind: str) -> bytes:
        if url in self.cache:
            return self._cached(self.cache[url])
        if self.unique_requests >= UNIQUE_REQUEST_LIMIT:
            raise AcquisitionError("unique-request cap exhausted")
        self.unique_requests += 1
        errors = []
        for attempt in range(1, MAX_ATTEMPTS_PER_URL + 1):
            if self.http_attempts >= HTTP_ATTEMPT_LIMIT:
                raise AcquisitionError("HTTP-attempt cap exhausted")
            self.http_attempts += 1
            try:
                request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with self.opener(request, timeout=90) as response:
                    declared = response.headers.get("Content-Length")
                    if declared and int(declared) > SINGLE_RESPONSE_LIMIT:
                        raise AcquisitionError("declared response exceeds 10 MiB quarantine cap")
                    chunks = []
                    size = 0
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        size += len(chunk)
                        if size > SINGLE_RESPONSE_LIMIT:
                            raise AcquisitionError("response exceeds 10 MiB quarantine cap")
                        if self.stored_bytes + size > BYTE_LIMIT:
                            raise AcquisitionError("450 MiB acquisition byte cap exceeded")
                        chunks.append(chunk)
                    body = b"".join(chunks)
                    final_url = response.url
                    content_type = response.headers.get("Content-Type")
                digest = sha256_bytes(body)
                path = self.objects / digest
                if not path.exists():
                    with path.open("xb") as handle:
                        handle.write(body)
                receipt = {
                    "url": url,
                    "kind": kind,
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                    "attempts": attempt,
                    "ok": True,
                    "sha256": digest,
                    "path": str(path.relative_to(self.raw)),
                    "bytes": len(body),
                    "content_type": content_type,
                    "final_url": final_url,
                }
                self._append(receipt)
                self.cache[url] = receipt
                self.downloaded_bytes += len(body)
                self.stored_bytes += len(body)
                time.sleep(REQUEST_DELAY_SECONDS)
                return body
            except AcquisitionError as error:
                self._append({
                    "url": url,
                    "kind": kind,
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                    "attempts": attempt,
                    "ok": False,
                    "blocked": True,
                    "error": str(error),
                })
                raise
            except Exception as error:  # network errors are preserved in receipt
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
        self._append(receipt)
        raise AcquisitionError(f"download failed after two attempts: {url}")


def acquire(root: Path, raw: Path, today: date) -> dict:
    if today < EARLIEST_EXECUTION:
        raise AcquisitionError(
            f"holdout is incomplete; earliest execution is {EARLIEST_EXECUTION}"
        )
    downloader = BoundedDownloader(raw)
    schedule_body = downloader.fetch(schedule_url(), "schedule")
    try:
        schedule = json.loads(schedule_body)
    except json.JSONDecodeError as error:
        raise AcquisitionError("schedule response is not valid JSON") from error
    games = final_games(schedule)
    jobs = fixed_jobs(games)
    for url, kind in jobs:
        downloader.fetch(url, kind)
    manifest = {
        "research_identity": "CT-S1",
        "status": "ACQUIRED_PENDING_RECONCILIATION",
        "window": {"start": START.isoformat(), "end": END.isoformat()},
        "final_games": len(games),
        "unique_network_requests_this_run": downloader.unique_requests,
        "http_attempts_this_run": downloader.http_attempts,
        "downloaded_bytes_this_run": downloader.downloaded_bytes,
        "stored_bytes_total": downloader.stored_bytes,
        "limits": {
            "unique_requests": UNIQUE_REQUEST_LIMIT,
            "http_attempts": HTTP_ATTEMPT_LIMIT,
            "game_feeds": GAME_FEED_LIMIT,
            "bytes": BYTE_LIMIT,
            "single_response_bytes": SINGLE_RESPONSE_LIMIT,
        },
        "next_gate": "CTS2_RULES_AND_POPULATION",
    }
    (raw / "acquisition_manifest.json").write_text(stable_json(manifest))
    return manifest


def dry_plan() -> dict:
    return {
        "research_identity": "CT-S1",
        "status": "DRY_RUN_NO_NETWORK",
        "window": {"start": START.isoformat(), "end": END.isoformat()},
        "earliest_execution": EARLIEST_EXECUTION.isoformat(),
        "owner_risk_acceptance_recorded": True,
        "limits": {
            "unique_requests": UNIQUE_REQUEST_LIMIT,
            "http_attempts": HTTP_ATTEMPT_LIMIT,
            "game_feeds": GAME_FEED_LIMIT,
            "downloaded_bytes": BYTE_LIMIT,
            "single_response_bytes": SINGLE_RESPONSE_LIMIT,
            "concurrency": 1,
        },
        "external_service_calls": {
            "github_actions": 0,
            "vercel": 0,
            "supabase": 0,
            "odds_api": 0,
            "hosted_databases": 0,
            "claude": 0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--owner-risk-accepted", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(stable_json(dry_plan()), end="")
        return 0
    if not args.owner_risk_accepted:
        raise SystemExit("--owner-risk-accepted is required with --execute")
    root = args.root.resolve()
    raw = root / "data/ct_s1/raw"
    try:
        result = acquire(root, raw, datetime.now(timezone.utc).date())
    except AcquisitionError as error:
        print(stable_json({"status": "STOPPED", "error": str(error)}), end="")
        return 2
    print(stable_json(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
