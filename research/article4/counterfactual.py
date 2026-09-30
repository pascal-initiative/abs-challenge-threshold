"""Deterministic post-pitch state reconstruction for Article 4.

Every function here is pure: it receives a pre-pitch state, the call that the
source feed actually recorded, the alternative call, and the runner movements
that the feed attaches to the pitch.  It returns the actual post-pitch state and
the counterfactual post-pitch state, together with the rule that produced it.

Rule vocabulary (documented in METHODOLOGY.md):

R1_NO_RUNNER_ACTION           No live-ball runner movement is attached to the
                              pitch.  The alternative call is applied to the
                              pre-pitch state exactly (count, walk force chain,
                              strikeout out, third-out inning end).  EXACT.
R2_RUNNER_OUTCOME_STANDS      Runner action occurred, and neither call ends the
                              plate appearance.  Published 2026 ABS guidance says
                              the outcome of a stolen-base attempt stands except
                              on an overturned ball four or strike three, so the
                              live-ball runner result is kept and only the
                              count changes.  RULE_BASED.
R3_TERMINAL_CALL_RUNNER_ACTION Runner action occurred, and at least one of the
                              two calls ends the plate appearance.  Runner
                              placement is then at umpire discretion under the
                              2026 guidance, so the counterfactual is AMBIGUOUS.
                              Two bounding alternatives are enumerated (runner
                              result stands / runners returned to the base held
                              at the time of pitch) and no primary state is
                              selected.
R4_UNCAUGHT_THIRD_STRIKE      The counterfactual call is strike three and the
                              pitch was not caught cleanly (wild pitch, passed
                              ball, or blocked ball).  Whether the batter could
                              have reached first is unobservable.  AMBIGUOUS.
R5_UNSUPPORTED_MOVEMENT       A movement type the engine does not model
                              (catcher interference, "other advance", missing
                              bases), or the movements do not reconcile with the
                              pre-pitch base state.  AMBIGUOUS, no alternatives.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

BASES = ("1B", "2B", "3B")
WALK_EVENTS = {"Walk", "Intent Walk"}
STRIKEOUT_EVENTS = {"Strikeout", "Strikeout Double Play", "Strikeout Triple Play"}
UNSUPPORTED_EVENTS = {"Catcher Interference", "Other Advance", "Batter Interference",
                      "Runner Interference", "Fan Interference"}
UNCAUGHT_EVENTS = {"Wild Pitch", "Passed Ball"}


@dataclass(frozen=True)
class State:
    balls: int
    strikes: int
    outs: int
    on_1b: bool
    on_2b: bool
    on_3b: bool
    runs: int = 0              # runs scored by the batting team on this pitch
    pa_status: str = "CONTINUES"  # CONTINUES / WALK / STRIKEOUT
    inning_ended: bool = False

    @property
    def base_state(self) -> str:
        return f"{int(self.on_1b)}{int(self.on_2b)}{int(self.on_3b)}"

    def valid(self) -> bool:
        if self.inning_ended:
            return self.outs == 3
        return (0 <= self.balls <= 3 and 0 <= self.strikes <= 2 and 0 <= self.outs <= 2
                and self.runs >= 0)


@dataclass
class Movement:
    runner_id: int | None
    start: str | None
    end: str | None
    is_out: bool
    event: str | None
    reason: str | None
    play_index: int
    is_batter: bool


@dataclass
class Result:
    actual: State | None
    counterfactual: State | None
    rule: str
    confidence: str             # EXACT / RULE_BASED / AMBIGUOUS
    ambiguity_reason: str | None = None
    alternatives: dict = field(default_factory=dict)  # label -> State
    actual_consistency: str = "CONSISTENT"


def result_type(balls: int, strikes: int, call: str) -> str:
    if call == "BALL":
        return "WALK" if balls == 3 else "CONTINUES"
    if call == "STRIKE":
        return "STRIKEOUT" if strikes == 2 else "CONTINUES"
    raise ValueError(call)


def _finish(balls, strikes, outs, bases, runs, pa_status) -> State:
    if outs >= 3:
        # A strikeout is complete when the pitch is caught; runners cannot
        # score on a play on which the third out is made this way, and runner
        # outs on the same play also end the half-inning.  Runs are void.
        return State(0, 0, 3, False, False, False, 0, pa_status, True)
    if pa_status != "CONTINUES":
        balls = strikes = 0
    return State(balls, strikes, outs, "1B" in bases, "2B" in bases, "3B" in bases,
                 runs, pa_status, False)


def apply_call(balls, strikes, outs, bases: set, call: str) -> State:
    """Apply a called ball/strike with no other runner action."""
    kind = result_type(balls, strikes, call)
    bases = set(bases)
    runs = 0
    if kind == "CONTINUES":
        return _finish(balls + (call == "BALL"), strikes + (call == "STRIKE"), outs, bases, 0, kind)
    if kind == "WALK":
        runs = _force_walk(bases)
        return _finish(0, 0, outs, bases, runs, kind)
    return _finish(0, 0, outs + 1, bases, 0, kind)


def _force_walk(bases: set) -> int:
    """Mutate an occupancy set for a batter awarded first; return forced runs."""
    runs = 0
    if "1B" in bases:
        if "2B" in bases:
            if "3B" in bases:
                runs = 1
            bases.add("3B")
        bases.add("2B")
    bases.add("1B")
    return runs


def _collapse(moves: list[Movement]) -> list[Movement]:
    """One net movement per runner per play index, preserving source order."""
    out: dict = {}
    order = []
    for m in moves:
        key = (m.play_index, m.runner_id)
        if key not in out:
            out[key] = replace(m)
            order.append(key)
        else:
            prev = out[key]
            out[key] = replace(prev, end=m.end, is_out=prev.is_out or m.is_out,
                               event=m.event, reason=m.reason)
    return [out[k] for k in order]


def apply_movements(bases: set, moves: list[Movement]):
    """Replay feed movements on an occupancy set.

    Returns (bases, outs_added, runs, consistent).  Removal is keyed by the
    movement's start base, so pinch-runner identity changes cannot desynchronize
    occupancy.  Groups are applied in play-index order.
    """
    bases = set(bases)
    outs = runs = 0
    consistent = True
    for idx in sorted({m.play_index for m in moves}):
        group = _collapse([m for m in moves if m.play_index == idx])
        for m in group:
            if m.start in BASES:
                if m.start not in bases:
                    consistent = False
                bases.discard(m.start)
        for m in group:
            if m.is_out:
                outs += 1
            elif m.end == "score":
                runs += 1
            elif m.end in BASES:
                if m.end in bases:
                    consistent = False
                bases.add(m.end)
            elif m.end is None and m.start is None and not m.is_out:
                consistent = False
    return bases, outs, runs, consistent


def classify_movements(moves: list[Movement]):
    batter, forced, live, unsupported = [], [], [], []
    for m in moves:
        if m.event in UNSUPPORTED_EVENTS or (m.start is None and m.end is None and not m.is_out):
            unsupported.append(m)
        elif m.is_batter:
            batter.append(m)
        elif m.event in WALK_EVENTS and m.reason in (None, "r_adv_force"):
            forced.append(m)
        elif m.event in STRIKEOUT_EVENTS and not m.is_out and m.start == m.end:
            continue
        else:
            live.append(m)
    return batter, forced, live, unsupported


def _alternative(pre_balls, pre_strikes, pre_outs, bases, call, extra_outs=0, extra_runs=0) -> State:
    kind = result_type(pre_balls, pre_strikes, call)
    bases = set(bases)
    outs = pre_outs + extra_outs
    runs = extra_runs
    if kind == "WALK":
        runs += _force_walk(bases)
    elif kind == "STRIKEOUT":
        outs += 1
    balls = pre_balls + (call == "BALL" and kind == "CONTINUES")
    strikes = pre_strikes + (call == "STRIKE" and kind == "CONTINUES")
    return _finish(balls, strikes, outs, bases, runs, kind)


def reconstruct(pre_balls: int, pre_strikes: int, pre_outs: int, pre_bases: set,
                actual_call: str, cf_call: str, moves: list[Movement],
                uncaught_pitch: bool = False) -> Result:
    """Return actual and counterfactual post-pitch states for one called pitch."""
    pre_bases = set(pre_bases)
    act_bases, act_outs, act_runs, consistent = apply_movements(pre_bases, moves)
    act_kind = result_type(pre_balls, pre_strikes, actual_call)
    cf_kind = result_type(pre_balls, pre_strikes, cf_call)
    act_b = pre_balls + (actual_call == "BALL" and act_kind == "CONTINUES")
    act_s = pre_strikes + (actual_call == "STRIKE" and act_kind == "CONTINUES")
    actual = _finish(act_b, act_s, pre_outs + act_outs, act_bases, act_runs, act_kind)
    batter, forced, live, unsupported = classify_movements(moves)
    uncaught = uncaught_pitch or any(m.event in UNCAUGHT_EVENTS for m in live)

    if not consistent or unsupported:
        return Result(actual if consistent else None, None, "R5_UNSUPPORTED_MOVEMENT", "AMBIGUOUS",
                      "movements do not reconcile with pre-pitch bases" if not consistent
                      else "unsupported movement: " + ",".join(sorted({str(m.event) for m in unsupported})),
                      actual_consistency="CONSISTENT" if consistent else "INCONSISTENT")

    # Validate that the actual call's mechanical consequences are present.
    if not live:
        expected = apply_call(pre_balls, pre_strikes, pre_outs, pre_bases, actual_call)
        if expected != actual:
            consistency = "ACTUAL_DIFFERS_FROM_MECHANICAL_TRANSITION"
        else:
            consistency = "CONSISTENT"
    else:
        consistency = "CONSISTENT"

    if cf_kind == "STRIKEOUT" and uncaught:
        alts = _uncaught_alternatives(pre_balls, pre_strikes, pre_outs, pre_bases, cf_call, live)
        return Result(actual, None, "R4_UNCAUGHT_THIRD_STRIKE", "AMBIGUOUS",
                      "counterfactual strike three on an uncaught pitch; batter could have attempted first base",
                      alts, consistency)

    if not live:
        cf = apply_call(pre_balls, pre_strikes, pre_outs, pre_bases, cf_call)
        return Result(actual, cf, "R1_NO_RUNNER_ACTION", "EXACT", None, {}, consistency)

    live_bases, live_outs, live_runs, _ = apply_movements(pre_bases, live)
    if act_kind == "CONTINUES" and cf_kind == "CONTINUES":
        cf = _finish(pre_balls + (cf_call == "BALL"), pre_strikes + (cf_call == "STRIKE"),
                     pre_outs + live_outs, live_bases, live_runs, "CONTINUES")
        return Result(actual, cf, "R2_RUNNER_OUTCOME_STANDS", "RULE_BASED", None, {}, consistency)

    stands = _alternative(pre_balls, pre_strikes, pre_outs, live_bases, cf_call, live_outs, live_runs)
    returned = _alternative(pre_balls, pre_strikes, pre_outs, pre_bases, cf_call)
    alts = {"RUNNER_RESULT_STANDS": stands, "RUNNERS_RETURNED_TO_TIME_OF_PITCH_BASES": returned}
    return Result(actual, None, "R3_TERMINAL_CALL_RUNNER_ACTION", "AMBIGUOUS",
                  f"{act_kind}->{cf_kind} with live-ball runner action; placement at umpire discretion",
                  alts, consistency)


def _uncaught_alternatives(pre_balls, pre_strikes, pre_outs, pre_bases, cf_call, live):
    bases_sets = {"RUNNERS_RETURNED_TO_TIME_OF_PITCH_BASES": (set(pre_bases), 0, 0)}
    if live:
        lb, lo, lr, _ = apply_movements(pre_bases, live)
        bases_sets["RUNNER_RESULT_STANDS"] = (lb, lo, lr)
    alts = {}
    for label, (bases, add_outs, add_runs) in bases_sets.items():
        alts[f"{label}|BATTER_OUT"] = _alternative(pre_balls, pre_strikes, pre_outs, bases, cf_call, add_outs, add_runs)
        outs_now = pre_outs + add_outs
        # Uncaught third strike: batter may run if first is open or there are two outs.
        if ("1B" not in bases or outs_now == 2) and outs_now < 3:
            b = set(bases)
            runs = add_runs
            if "1B" in b:  # two outs, first occupied: runners forced
                runs += _force_walk(b)
            else:
                b.add("1B")
            alts[f"{label}|BATTER_REACHES_FIRST"] = _finish(0, 0, outs_now, b, runs, "STRIKEOUT")
    return alts
