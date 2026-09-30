"""Pure helpers for the ABS-05 Gate G8 stability audit."""
from __future__ import annotations

import numpy as np


def grant_between(innings, index: int, grant_extras: bool = True) -> bool:
    return bool(
        grant_extras
        and index + 1 < len(innings)
        and innings[index + 1] > innings[index]
        and innings[index + 1] >= 10
    )


def dynamic_values(p, value, innings, grant_extras: bool = True, kmax: int = 2):
    """Solve the exact suffix policy under one declared sensitivity."""
    p = np.asarray(p, dtype=float)
    value = np.asarray(value, dtype=float)
    innings = np.asarray(innings, dtype=int)
    if not (len(p) == len(value) == len(innings)):
        raise ValueError("p, value, and innings must have equal length")
    if not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError("probabilities must be finite and in [0, 1]")
    if not np.isfinite(value).all():
        raise ValueError("values must be finite")

    n = len(p)
    W = np.zeros((kmax + 1, n + 1))
    action = np.zeros((kmax + 1, n), dtype=bool)
    cost = np.zeros((kmax + 1, n))
    threshold = np.ones((kmax + 1, n))

    def next_value(k, i):
        future_k = max(k, 1) if grant_between(innings, i, grant_extras) and k == 0 else k
        return W[future_k, i + 1]

    for i in range(n - 1, -1, -1):
        W[0, i] = next_value(0, i)
        for k in range(1, kmax + 1):
            retained = next_value(k, i)
            consumed = next_value(k - 1, i)
            marginal = retained - consumed
            challenge = p[i] * (value[i] + retained) + (1 - p[i]) * consumed
            use = challenge > retained
            W[k, i] = challenge if use else retained
            action[k, i] = use
            cost[k, i] = marginal
            denominator = value[i] + marginal
            threshold[k, i] = marginal / denominator if denominator > 0 else 1.0
    return {"W": W, "action": action, "cost": cost, "threshold": threshold}


def threshold_band(value: float) -> str:
    if not np.isfinite(value):
        return "UNAVAILABLE"
    if value <= 0.50:
        return "LOW_REQUIRED_CONFIDENCE"
    if value <= 0.70:
        return "INTERMEDIATE_REQUIRED_CONFIDENCE"
    return "HIGH_REQUIRED_CONFIDENCE"


def flip_rate(reference, sensitivity) -> tuple[int, int, float]:
    reference = np.asarray(reference, dtype=bool)
    sensitivity = np.asarray(sensitivity, dtype=bool)
    if len(reference) != len(sensitivity):
        raise ValueError("action vectors must have equal length")
    flips = int((reference != sensitivity).sum())
    return len(reference), flips, float(flips / len(reference)) if len(reference) else np.nan
