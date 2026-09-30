"""Replay immutable MLB game feeds into per-pitch states for Article 4.

The feed is the only source used for runner movements, concurrent actions and
runs to the end of the half-inning.  Every attached event is linked to its pitch
by a source field (``actionPlayId`` equal to the pitch ``playId``; catcher pickoff
throws by ``fromCatcher`` on the event immediately following the pitch; runner
movements by ``playIndex``).  No event is attached by timing heuristics.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from counterfactual import BASES, Movement, apply_movements

CALL_CODES = {"B": "BALL", "*B": "BALL", "C": "STRIKE", "P": "BALL", "I": "BALL"}
BASERUNNING_PREFIXES = ("stolen_base", "caught_stealing", "wild_pitch", "passed_ball",
                        "defensive_indiff", "pickoff", "other_out", "error", "balk",
                        "runner", "other_advance")


def _count(event):
    c = event.get("count") or {}
    return c.get("balls"), c.get("strikes"), c.get("outs")


def _movement(r, batter_id) -> Movement:
    m, d = r.get("movement", {}), r.get("details", {})
    rid = (d.get("runner") or {}).get("id")
    return Movement(rid, m.get("start"), m.get("end"), bool(m.get("isOut")), d.get("event"),
                    d.get("movementReason"), int(d.get("playIndex", -1)), rid == batter_id)


def _move_json(m: Movement) -> dict:
    return {"runner_id": m.runner_id, "start": m.start, "end": m.end, "is_out": m.is_out,
            "event": m.event, "reason": m.reason, "play_index": m.play_index, "is_batter": m.is_batter}


def parse_feed(feed: dict, feed_sha: str):
    """Return (pitch_rows, half_rows) for one final game feed."""
    pk = int(feed["gamePk"])
    plays = feed["liveData"]["plays"]["allPlays"]
    linescore = {(i["num"], side): (i.get(side) or {}).get("runs")
                 for i in feed["liveData"]["linescore"].get("innings", []) for side in ("away", "home")}
    actions = defaultdict(list)  # pitch playId -> [(play_pos, event)]
    for pos, play in enumerate(plays):
        for e in play["playEvents"]:
            if e.get("type") == "action" and e.get("actionPlayId"):
                actions[e["actionPlayId"]].append((pos, e))
    rows, halves = [], []
    last_pitch = None  # most recent pitch row; receives state-changing events until the next pitch
    half_key, bases, outs, runs_half = None, set(), 0, 0
    half_pitches = []
    score = {"home": 0, "away": 0}

    def close_half():
        if half_key is None:
            return
        inning, half = half_key
        side = "away" if half == "top" else "home"
        halves.append({"game_pk": pk, "inning": inning, "half_inning": half,
                       "feed_movement_runs": runs_half, "linescore_runs": linescore.get((inning, side)),
                       "end_outs": outs, "pitches": len(half_pitches)})
        for r in half_pitches:
            r["future_runs_half"] = runs_half - r["_runs_before"]
            r["half_end_outs"] = outs
            del r["_runs_before"]

    for pos, play in enumerate(plays):
        about, matchup = play["about"], play["matchup"]
        key = (int(about["inning"]), about["halfInning"])
        if key != half_key:
            close_half()
            half_key, bases, outs, runs_half, half_pitches = key, set(), 0, 0, []
        batter_id = matchup["batter"]["id"]
        batting = "away" if key[1] == "top" else "home"
        moves = [_movement(r, batter_id) for r in play.get("runners", [])]
        by_index = defaultdict(list)
        for m in moves:
            by_index[m.play_index].append(m)
        events = sorted(play["playEvents"], key=lambda e: e["index"])
        prev_count = (0, 0)
        for n, e in enumerate(events):
            idx = e["index"]
            if e.get("isPitch"):
                detail = e.get("details", {})
                code = (detail.get("call") or {}).get("code")
                row = {"pitch_key": f"{pk}:{about['atBatIndex']}:{idx}", "game_pk": pk,
                       "at_bat_index": about["atBatIndex"], "play_event_index": idx,
                       "play_id": e.get("playId"), "inning": key[0], "half_inning": key[1],
                       "feed_batter_id": batter_id, "feed_pitcher_id": matchup["pitcher"]["id"],
                       "feed_call_code": code, "feed_call": CALL_CODES.get(code),
                       "feed_description": detail.get("description"),
                       "feed_pre_balls": prev_count[0], "feed_pre_strikes": prev_count[1],
                       "feed_pre_outs": outs, "feed_pre_on_1b": int("1B" in bases),
                       "feed_pre_on_2b": int("2B" in bases), "feed_pre_on_3b": int("3B" in bases),
                       "feed_pre_bat_score": score[batting],
                       "feed_pre_fld_score": score["home" if batting == "away" else "away"],
                       "feed_source_sha256": feed_sha, "_runs_before": runs_half}
                if CALL_CODES.get(code):
                    row.update(_window(play, pos, n, events, e, actions, by_index, plays, batter_id))
                    row["feed_pa_result_event"] = play["result"].get("event")
                    row["feed_pa_result_description"] = play["result"].get("description")
                    row["feed_pa_is_complete"] = about.get("isComplete")
                row["state_changing_events_before_next_pitch"] = []
                half_pitches.append(row)
                rows.append(row)
                last_pitch = row
            group = by_index.get(idx, [])
            b_now, s_now, _ = _count(e)
            if not e.get("isPitch") and last_pitch is not None and (
                    group or (b_now is not None and (b_now, s_now) != tuple(prev_count))
                    or (e.get("details") or {}).get("eventType") == "runner_placed"):
                last_pitch["state_changing_events_before_next_pitch"].append(
                    (e.get("details") or {}).get("eventType") or e.get("type"))
            if (e.get("details") or {}).get("eventType") == "runner_placed" and not group:
                # Extra-inning automatic runner: the feed records the base on the
                # event itself rather than as a runner movement.
                placed = {1: "1B", 2: "2B", 3: "3B"}.get(e.get("base"))
                if placed is None:
                    raise RuntimeError(f"runner_placed without base in game {pk}")
                bases = set(bases) | {placed}
            if group:
                bases, add_outs, add_runs, _ = apply_movements(bases, group)
                outs += add_outs
                runs_half += add_runs
                score[batting] += add_runs
            b, s, _ = _count(e)
            if b is not None and s is not None:
                prev_count = (b, s)
        if last_pitch is not None and not any(e.get("isPitch") for e in events):
            last_pitch["state_changing_events_before_next_pitch"].append("PA_WITHOUT_PITCH:" + str(play["result"].get("eventType")))
        # Scores are replayed from movements; the feed's own post-play score audits them.
        res = play.get("result", {})
        if res.get("awayScore") is not None:
            score["away"], score["home"] = res["awayScore"], res["homeScore"]
    close_half()
    for r in rows:
        r["state_changing_events_before_next_pitch"] = json.dumps(r["state_changing_events_before_next_pitch"])
    return rows, halves


def _window(play, pos, n, events, pitch, actions, by_index, plays, batter_id) -> dict:
    """Source-linked events attached to one pitch."""
    attached = []  # (play_pos, event)
    for apos, a in actions.get(pitch.get("playId"), []):
        attached.append((apos, a))
    nxt = events[n + 1] if n + 1 < len(events) else None
    catcher_pickoff = bool(nxt is not None and nxt.get("type") == "pickoff"
                           and (nxt.get("details") or {}).get("fromCatcher"))
    if catcher_pickoff:
        attached.append((pos, nxt))
    move_objs = list(by_index.get(pitch["index"], []))
    for apos, a in attached:
        if apos == pos:
            move_objs.extend(by_index.get(a["index"], []))
        else:
            other = plays[apos]
            for r in other.get("runners", []):
                if int(r.get("details", {}).get("playIndex", -1)) == a["index"]:
                    move_objs.append(_movement(r, batter_id))
    credits = []
    for r in play.get("runners", []):
        # Fielding credits on runner (not batter) movements: a catcher assist or
        # throwing error is the only source evidence of a recorded catcher throw.
        if ((r.get("details", {}).get("runner") or {}).get("id") != batter_id and
                int(r.get("details", {}).get("playIndex", -1)) in {pitch["index"]} | {a["index"] for p, a in attached if p == pos}):
            for c in r.get("credits", []) or []:
                credits.append(f"{c.get('credit')}:{(c.get('position') or {}).get('abbreviation')}")
    reviews = [a.get("reviewDetails") for _, a in attached if a.get("reviewDetails")]
    unattached = []
    for e in events[n + 1:]:
        if e.get("isPitch"):
            break
        if e.get("type") == "action" and e.get("isBaseRunningPlay") and e.get("actionPlayId") != pitch.get("playId"):
            unattached.append((e.get("details") or {}).get("eventType"))
    pitch_review = pitch.get("reviewDetails") or {}
    return {
        "feed_pitch_start_time": pitch.get("startTime"), "feed_pitch_end_time": pitch.get("endTime"),
        "feed_pitch_review_type": pitch_review.get("reviewType"),
        "feed_pitch_review_overturned": pitch_review.get("isOverturned"),
        "attached_event_indices": json.dumps([[p, a["index"]] for p, a in attached]),
        "attached_event_types": json.dumps([(a.get("details") or {}).get("eventType") or a.get("type") for _, a in attached]),
        "attached_event_descriptions": json.dumps([(a.get("details") or {}).get("description") for _, a in attached]),
        "attached_event_is_baserunning": json.dumps([bool(a.get("isBaseRunningPlay")) for _, a in attached]),
        "catcher_pickoff_throw_after_pitch": catcher_pickoff,
        "attached_movements": json.dumps([_move_json(m) for m in move_objs]),
        "attached_credits": json.dumps(credits),
        "secondary_review_json": json.dumps(reviews) if reviews else None,
        "next_event_type": None if nxt is None else ((nxt.get("details") or {}).get("eventType") or nxt.get("type")),
        "next_event_from_catcher": None if nxt is None else (nxt.get("details") or {}).get("fromCatcher"),
        "unlinked_baserunning_before_next_pitch": json.dumps(unattached),
    }


def load_feeds(root: Path, shas: dict[int, str]):
    """Parse the exact feed object referenced by the processed pitch table."""
    raw = root / "data/full_season/raw"
    receipts = {}
    for line in (raw / "receipts.jsonl").read_text().splitlines():
        r = json.loads(line)
        if r.get("kind") == "feed" and r.get("ok"):
            receipts[r["sha256"]] = r
    rows, halves = [], []
    for pk, sha in sorted(shas.items()):
        receipt = receipts.get(sha)
        if receipt is None:
            raise RuntimeError(f"feed receipt missing for game {pk}: {sha}")
        feed = json.loads((raw / receipt["path"]).read_text())
        if int(feed["gamePk"]) != pk:
            raise RuntimeError(f"feed object {sha} is not game {pk}")
        r, h = parse_feed(feed, sha)
        rows.extend(r)
        halves.extend(h)
    return rows, halves
