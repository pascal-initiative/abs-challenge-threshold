"""Archive post-snapshot Braves feeds for the Article 4 case-study search only.

The accepted research snapshot ends 2026-09-09.  The Braves case study is a
search for a specific remembered game, so this script archives, content-addressed
and with receipts, the 2026 Braves regular-season schedule plus final feeds for
Braves games after the snapshot cutoff.  These bytes are used ONLY by the case
study search; they never enter any Article 4 population, RE table or summary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

TEAM_ID = 144
UA = {"User-Agent": "Pascal-ABS-Research/0.1 (public research)"}


def fetch(url: str, raw: Path) -> tuple[dict, bytes]:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
        body = r.read()
        ctype = r.headers.get("Content-Type")
    sha = hashlib.sha256(body).hexdigest()
    (raw / "objects").mkdir(parents=True, exist_ok=True)
    (raw / "objects" / sha).write_bytes(body)
    return {"url": url, "retrieved_at": datetime.now(timezone.utc).isoformat(), "bytes": len(body),
            "content_type": ctype, "sha256": sha, "path": f"objects/{sha}", "ok": True}, body


def main(out: Path, start: str, end: str, snapshot_end: str) -> None:
    raw = out / "case_study_raw"
    receipts = []
    url = "https://statsapi.mlb.com/api/v1/schedule?" + urlencode(
        dict(sportId=1, teamId=TEAM_ID, startDate=start, endDate=end, gameType="R"))
    rec, body = fetch(url, raw)
    rec["kind"] = "schedule"
    receipts.append(rec)
    games = [g for d in json.loads(body)["dates"] for g in d["games"]]
    for g in games:
        if g["officialDate"] > snapshot_end and g["status"]["abstractGameState"] == "Final":
            rec, _ = fetch("https://statsapi.mlb.com" + g["link"], raw)
            rec.update(kind="feed", game_pk=g["gamePk"], official_date=g["officialDate"])
            receipts.append(rec)
    (raw / "receipts.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in receipts))
    print(f"archived {len(receipts)} objects to {raw}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "output")
    ap.add_argument("--start", default="2026-03-25")
    ap.add_argument("--end", default="2026-09-23")
    ap.add_argument("--snapshot-end", default="2026-09-09")
    a = ap.parse_args()
    main(a.output, a.start, a.end, a.snapshot_end)
