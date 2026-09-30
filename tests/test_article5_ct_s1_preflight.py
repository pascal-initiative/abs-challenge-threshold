import importlib.util
import csv
import hashlib
import io
import json
import sys
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "research/article5/validate_ct_s1_raw.py"
SPEC = importlib.util.spec_from_file_location("article5_ct_s1_preflight", MODULE_PATH)
preflight = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = preflight
SPEC.loader.exec_module(preflight)


def build_valid_snapshot(raw: Path):
    (raw / "objects").mkdir()
    receipts = []

    def add(url, kind, body):
        body = body.encode() if isinstance(body, str) else body
        digest = hashlib.sha256(body).hexdigest()
        (raw / "objects" / digest).write_bytes(body)
        receipts.append({
            "url": url,
            "kind": kind,
            "retrieved_at": "2026-09-28T00:00:00+00:00",
            "attempts": 1,
            "ok": True,
            "sha256": digest,
            "path": f"objects/{digest}",
            "bytes": len(body),
            "content_type": "application/json",
            "final_url": url,
        })

    games = []
    current = preflight.START
    for index in range(17):
        games.append({
            "gamePk": 1000 + index,
            "officialDate": current.isoformat(),
            "gameType": "R",
            "season": "2026",
            "link": f"/api/v1.1/game/{1000 + index}/feed/live",
            "status": {"abstractGameState": "Final"},
            "teams": {
                "home": {"team": {"id": (2 * index) % 30 + 1}},
                "away": {"team": {"id": (2 * index + 1) % 30 + 1}},
            },
        })
        current += timedelta(days=1)
    schedule = {
        "dates": [{"date": game["officialDate"], "games": [game]} for game in games]
    }
    add(preflight.schedule_url(), "schedule", json.dumps(schedule))
    date_to_game = {game["officialDate"]: game for game in games}
    columns = sorted(preflight.REQUIRED_STATCAST_COLUMNS)
    abs_index = 0
    for url, kind in preflight.fixed_jobs(games):
        if kind == "feed":
            game_pk = int(url.split("/")[-3])
            add(url, kind, json.dumps({
                "gamePk": game_pk,
                "gameData": {"status": {"abstractGameState": "Final"}},
            }))
        elif kind == "abs":
            records = []
            if abs_index < len(games):
                challenge_game = games[abs_index]
                records.append({
                    "game_pk": challenge_game["gamePk"],
                    "game_date": challenge_game["officialDate"],
                    "play_id": f"challenge-{abs_index}",
                })
            abs_index += 1
            add(url, kind, json.dumps({"data": records}))
        elif kind == "statcast":
            day = url.split("game_date_gt=")[1][:10]
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=columns)
            writer.writeheader()
            row = {column: "" for column in columns}
            row.update({
                "game_date": day,
                "game_pk": date_to_game[day]["gamePk"],
                "at_bat_number": 1,
                "pitch_number": 1,
                "description": "ball",
            })
            writer.writerow(row)
            add(url, kind, output.getvalue())
        else:
            daily = [
                {"game_date": game["officialDate"], "challenges": 1}
                for game in games
            ]
            add(url, kind, "<script>const absSummaryData = " + json.dumps(daily) + ";</script>")
    (raw / "receipts.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in receipts)
    )
    stored_bytes = sum(path.stat().st_size for path in (raw / "objects").iterdir())
    (raw / "acquisition_manifest.json").write_text(json.dumps({
        "research_identity": "CT-S1",
        "status": "ACQUIRED_PENDING_RECONCILIATION",
        "window": {"start": "2026-09-11", "end": "2026-09-27"},
        "final_games": 17,
        "stored_bytes_total": stored_bytes,
        "limits": {
            "unique_requests": preflight.UNIQUE_REQUEST_LIMIT,
            "http_attempts": preflight.HTTP_ATTEMPT_LIMIT,
            "game_feeds": preflight.GAME_FEED_LIMIT,
            "bytes": preflight.BYTE_LIMIT,
            "single_response_bytes": preflight.SINGLE_RESPONSE_LIMIT,
        },
    }))


class CTS1PreflightTests(unittest.TestCase):
    def test_complete_synthetic_snapshot_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            raw = Path(temp)
            build_valid_snapshot(raw)
            result = preflight.validate_snapshot(raw)
            self.assertEqual(result["status"], "PASS_CTS1_READY_FOR_CTS2_PROCESSING")
            self.assertEqual(result["final_games"], 17)
            self.assertEqual(result["unique_urls"], 66)
            self.assertEqual(result["deduplicated_team_abs_challenges"], 17)

    def test_missing_snapshot_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(preflight.PreflightError):
                preflight.validate_snapshot(Path(temp))

    def test_receipt_path_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            raw = Path(temp)
            (raw / "receipts.jsonl").write_text(json.dumps({
                "url": "https://example.test/data",
                "kind": "schedule",
                "retrieved_at": "2026-09-28T00:00:00+00:00",
                "attempts": 1,
                "ok": True,
                "sha256": "0" * 64,
                "path": "../escape",
                "bytes": 0,
                "content_type": "application/json",
                "final_url": "https://example.test/data",
            }) + "\n")
            (raw / "acquisition_manifest.json").write_text(json.dumps({
                "research_identity": "CT-S1",
                "status": "ACQUIRED_PENDING_RECONCILIATION",
            }))
            with self.assertRaises(preflight.PreflightError):
                preflight.load_snapshot(raw)

    def test_unknown_receipt_field_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            raw = Path(temp)
            (raw / "receipts.jsonl").write_text(json.dumps({
                "url": "https://example.test/data",
                "kind": "schedule",
                "ok": False,
                "secret_token": "must-not-be-recorded",
            }) + "\n")
            (raw / "acquisition_manifest.json").write_text(json.dumps({
                "research_identity": "CT-S1",
                "status": "ACQUIRED_PENDING_RECONCILIATION",
            }))
            with self.assertRaises(preflight.PreflightError):
                preflight.load_snapshot(raw)

    def test_audited_successful_supersession_is_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            raw = Path(temp)
            build_valid_snapshot(raw)
            receipts = [
                json.loads(line) for line in (raw / "receipts.jsonl").read_text().splitlines()
            ]
            final_url = next(
                url for url, kind in preflight.fixed_jobs(preflight.final_games(json.loads(
                    (raw / receipts[0]["path"]).read_bytes()
                )))
                if kind == "statcast" and "game_date_gt=2026-09-27" in url
            )
            prior = next(row for row in receipts if row["url"] == final_url)
            original = (raw / prior["path"]).read_text()
            replacement = (original + original.splitlines()[-1] + "\n").encode()
            digest = hashlib.sha256(replacement).hexdigest()
            (raw / "objects" / digest).write_bytes(replacement)
            successor = dict(prior)
            successor.update({
                "retrieved_at": "2026-09-28T12:00:00+00:00",
                "sha256": digest,
                "path": f"objects/{digest}",
                "bytes": len(replacement),
                "supersedes_sha256": prior["sha256"],
            })
            with (raw / "receipts.jsonl").open("a") as handle:
                handle.write(json.dumps(successor, sort_keys=True) + "\n")
            manifest = json.loads((raw / "acquisition_manifest.json").read_text())
            manifest["stored_bytes_total"] = sum(
                path.stat().st_size for path in (raw / "objects").iterdir()
            )
            (raw / "acquisition_manifest.json").write_text(json.dumps(manifest))
            result = preflight.validate_snapshot(raw)
            self.assertEqual(result["status"], "PASS_CTS1_READY_FOR_CTS2_PROCESSING")

    def test_unaudited_successful_hash_conflict_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            raw = Path(temp)
            build_valid_snapshot(raw)
            receipts = [
                json.loads(line) for line in (raw / "receipts.jsonl").read_text().splitlines()
            ]
            prior = next(row for row in receipts if row["kind"] == "statcast")
            replacement = (raw / prior["path"]).read_bytes() + b"\n"
            digest = hashlib.sha256(replacement).hexdigest()
            (raw / "objects" / digest).write_bytes(replacement)
            conflict = dict(prior)
            conflict.update({
                "sha256": digest,
                "path": f"objects/{digest}",
                "bytes": len(replacement),
            })
            with (raw / "receipts.jsonl").open("a") as handle:
                handle.write(json.dumps(conflict, sort_keys=True) + "\n")
            with self.assertRaisesRegex(preflight.PreflightError, "unaudited successful"):
                preflight.load_snapshot(raw)


if __name__ == "__main__":
    unittest.main()
