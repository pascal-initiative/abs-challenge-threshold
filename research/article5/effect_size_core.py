"""Pure helpers for the ABS-05 Gate G9 effect-size audit."""
from __future__ import annotations

import numpy as np


def grant_between(innings, index: int) -> bool:
    return bool(
        index + 1 < len(innings)
        and innings[index + 1] > innings[index]
        and innings[index + 1] >= 10
    )


def evaluate_inventory_policy(p, value, innings, actions, kmax: int = 2):
    """Evaluate a fixed inventory-dependent action matrix by backward recursion."""
    p = np.asarray(p, dtype=float)
    value = np.asarray(value, dtype=float)
    innings = np.asarray(innings, dtype=int)
    actions = np.asarray(actions, dtype=bool)
    if not (len(p) == len(value) == len(innings)):
        raise ValueError("p, value, and innings must align")
    if actions.shape != (kmax + 1, len(p)):
        raise ValueError("actions must have shape (kmax + 1, opportunities)")
    W = np.zeros((kmax + 1, len(p) + 1))

    def next_value(k, i):
        future_k = max(k, 1) if grant_between(innings, i) and k == 0 else k
        return W[future_k, i + 1]

    for i in range(len(p) - 1, -1, -1):
        W[0, i] = next_value(0, i)
        for k in range(1, kmax + 1):
            retained = next_value(k, i)
            consumed = next_value(k - 1, i)
            challenged = p[i] * (value[i] + retained) + (1 - p[i]) * consumed
            W[k, i] = challenged if actions[k, i] else retained
    return W


def static_cost_actions(p, value, cost_one, cost_two):
    p = np.asarray(p, dtype=float)
    value = np.asarray(value, dtype=float)
    costs = [None, np.asarray(cost_one, dtype=float), np.asarray(cost_two, dtype=float)]
    if not all(len(costs[k]) == len(p) for k in (1, 2)):
        raise ValueError("static cost arrays must align")
    actions = np.zeros((3, len(p)), dtype=bool)
    for inventory in (1, 2):
        actions[inventory] = p * value > (1 - p) * costs[inventory]
    return actions


def cluster_bootstrap_effect(
    dynamic_by_game,
    simple_by_game,
    repetitions: int,
    seed: int,
    batch_size: int = 250,
):
    dynamic = np.asarray(dynamic_by_game, dtype=float)
    simple = np.asarray(simple_by_game, dtype=float)
    if simple.ndim != 2 or len(dynamic) != len(simple):
        raise ValueError("game arrays must align")
    rng = np.random.default_rng(seed)
    effects = np.empty(repetitions)
    n_games = len(dynamic)
    cursor = 0
    while cursor < repetitions:
        size = min(batch_size, repetitions - cursor)
        indices = rng.integers(0, n_games, size=(size, n_games))
        dynamic_mean = dynamic[indices].mean(axis=1)
        simple_means = simple[indices].mean(axis=1)
        effects[cursor:cursor + size] = dynamic_mean - simple_means.max(axis=1)
        cursor += size
    point = float(dynamic.mean() - simple.mean(axis=0).max())
    return {
        "point": point,
        "lower_95": float(np.quantile(effects, 0.025)),
        "upper_95": float(np.quantile(effects, 0.975)),
        "repetitions": repetitions,
    }
