import importlib.util
import hashlib
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "research/article5/refresh_ct_s1_abs.py"
SPEC = importlib.util.spec_from_file_location("article5_ct_s1_abs_refresh", MODULE_PATH)
refresh = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = refresh
SPEC.loader.exec_module(refresh)


def dashboard(days):
    rows = [{"game_date": day, "challenges": 1} for day in days]
    return ("<script>const absSummaryData = " + json.dumps(rows) + ";</script>").encode()


def test_dashboard_final_day_gate():
    assert not refresh.dashboard_has_final_day(dashboard(["2026-09-26"]))
    assert refresh.dashboard_has_final_day(dashboard(["2026-09-26", "2026-09-27"]))


def test_malformed_dashboard_fails_closed():
    with pytest.raises(refresh.RefreshError, match="not parseable"):
        refresh.dashboard_has_final_day(b"not a dashboard")


def test_team_abs_requires_json_data_list():
    assert refresh.team_abs_is_valid(b'{"data": []}')
    with pytest.raises(refresh.RefreshError, match="no data list"):
        refresh.team_abs_is_valid(b'{"wrong": []}')


class FakeResponse:
    def __init__(self, url, body, content_type):
        self.url = url
        self.body = body
        self.headers = {"Content-Length": str(len(body)), "Content-Type": content_type}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, _size):
        return self.body


def test_dashboard_is_refreshed_before_thirty_team_sources(tmp_path):
    raw = tmp_path
    objects = raw / "objects"
    objects.mkdir()
    receipts = []

    def add(url, kind, body):
        digest = hashlib.sha256(body).hexdigest()
        (objects / digest).write_bytes(body)
        receipts.append({
            "url": url,
            "kind": kind,
            "retrieved_at": "2026-09-28T07:00:00+00:00",
            "attempts": 1,
            "ok": True,
            "sha256": digest,
            "path": f"objects/{digest}",
            "bytes": len(body),
            "content_type": "application/json",
            "final_url": url,
        })

    add(refresh.DASHBOARD_URL, "abs_dashboard", dashboard(["2026-09-26"]))
    team_urls = [f"https://example.test/team/{team}" for team in range(30)]
    for url in team_urls:
        add(url, "abs", b'{"data": []}')
    (raw / "receipts.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in receipts)
    )
    (raw / "acquisition_manifest.json").write_text(json.dumps({
        "stored_bytes_total": refresh.object_bytes(raw),
    }))

    calls = []

    def opener(request, timeout):
        calls.append(request.full_url)
        if request.full_url == refresh.DASHBOARD_URL:
            return FakeResponse(
                request.full_url,
                dashboard(["2026-09-26", "2026-09-27"]),
                "text/html",
            )
        return FakeResponse(request.full_url, b'{"data": []}', "application/json")

    result = refresh.refresh(raw, opener=opener)
    assert result["network_calls_this_run"] == 31
    assert calls[0] == refresh.DASHBOARD_URL
    assert set(calls[1:]) == set(team_urls)
    updated = [json.loads(line) for line in (raw / "receipts.jsonl").read_text().splitlines()]
    assert len([row for row in updated if row.get("supersedes_sha256")]) == 31
