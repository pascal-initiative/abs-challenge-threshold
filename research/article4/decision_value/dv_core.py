"""Pure, testable pieces of the Article 4 decision-value analysis."""
from __future__ import annotations

import numpy as np

HALF_PLATE_FT = 17 / 2 / 12


def edge_class(plate_x, plate_z, top, bot, bat_side):
    """Nearest ABS-zone edge, symmetric across the boundary.

    The class is the same whether the pitch is just inside or just outside that
    edge, so together with the UNSIGNED boundary distance it does not reveal
    whether the call was correct.  Horizontal edges are named INSIDE/OUTSIDE
    relative to the batter (right-handed batter stands at negative x from the
    catcher's view, so x > 0 is outside for RHB).
    """
    x = np.asarray(plate_x, float); z = np.asarray(plate_z, float)
    h = np.abs(x) - HALF_PLATE_FT
    t = z - np.asarray(top, float)
    b = np.asarray(bot, float) - z
    stack = np.vstack([h, t, b])
    k = np.nanargmax(np.where(np.isnan(stack), -np.inf, stack), axis=0)
    side = np.asarray(bat_side).astype(str)
    outside = np.where(side == "R", x > 0, x < 0)
    horiz = np.where(outside, "OUTSIDE", "INSIDE")
    out = np.where(k == 0, horiz, np.where(k == 1, "TOP", "BOTTOM")).astype(object)
    out[np.isnan(x) | np.isnan(z)] = None
    return out


def suffix_option_values(p, v, use_prob, kmax=2):
    """Expected run value recovered from a future opportunity stream.

    Opportunities are processed in time order.  At opportunity i the holder of
    k > 0 challenges uses one with probability use_prob[i]; the challenge
    succeeds with probability p[i], recovering v[i] runs and retaining the
    challenge (2026 rule), or fails and loses one.  Backward recursion gives,
    for every start index s, V[k][s] = expected value from s onward holding k.
    Returns an array of shape (kmax + 1, n + 1); column n is the empty stream.
    """
    p = np.asarray(p, float); v = np.asarray(v, float); q = np.asarray(use_prob, float)
    n = len(p)
    V = np.zeros((kmax + 1, n + 1))
    for i in range(n - 1, -1, -1):
        for k in range(1, kmax + 1):
            use = p[i] * (v[i] + V[k, i + 1]) + (1 - p[i]) * V[k - 1, i + 1]
            V[k, i] = q[i] * use + (1 - q[i]) * V[k, i + 1]
    return V


def suffix_prophet(ev):
    """Upper-bound benchmarks: max and top-two sum of future EV from each start index."""
    ev = np.asarray(ev, float); n = len(ev)
    top1 = np.zeros(n + 1); top2 = np.zeros(n + 1)
    best = []
    for i in range(n - 1, -1, -1):
        best = sorted(best + [ev[i]], reverse=True)[:2]
        top1[i] = best[0]; top2[i] = sum(best)
    return top1, top2


def flip_value(pre_balls, pre_strikes, pre_outs, bases: str, call: str, lookup: dict):
    """Value to the entitled team of reversing a called ball/strike (no runner action)."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from counterfactual import apply_call  # noqa: E402
    occ = {b for b, f in zip(("1B", "2B", "3B"), bases) if f == "1"}
    other = "STRIKE" if call == "BALL" else "BALL"
    def val(s):
        return float(s.runs) if s.inning_ended else s.runs + lookup[(s.balls, s.strikes, s.outs, s.base_state)]
    a = apply_call(pre_balls, pre_strikes, pre_outs, occ, call)
    c = apply_call(pre_balls, pre_strikes, pre_outs, occ, other)
    delta_batting = val(a) - val(c)  # observed minus corrected, batting perspective
    return -delta_batting if call == "STRIKE" else delta_batting


def classify_spend(ev, cost_low, cost_high):
    """SPEND_CLEARLY if EV exceeds every preservation-cost benchmark; PRESERVE_CLEARLY if below all."""
    ev = np.asarray(ev, float)
    return np.where(ev > cost_high, "IMMEDIATE_EXCEEDS_PRESERVATION",
                    np.where(ev < cost_low, "PRESERVATION_EXCEEDS_IMMEDIATE", "OVERLAPPING"))
