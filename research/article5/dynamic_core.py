"""Pure dynamic-programming primitives for ABS challenge inventory."""
from __future__ import annotations

import numpy as np


def grant_between(innings, index: int) -> bool:
    return bool(
        index + 1 < len(innings)
        and innings[index + 1] > innings[index]
        and innings[index + 1] >= 10
    )


def backward_values(p, value, innings, policy="dynamic", kmax=2):
    p = np.asarray(p, dtype=float)
    value = np.asarray(value, dtype=float)
    innings = np.asarray(innings, dtype=int)
    if not (len(p) == len(value) == len(innings)):
        raise ValueError("p, value, and innings must have equal length")
    n = len(p)
    W = np.zeros((kmax + 1, n + 1))
    action = np.zeros((kmax + 1, n), dtype=bool)
    cost = np.zeros((kmax + 1, n))
    threshold = np.ones((kmax + 1, n))

    def next_value(k, i):
        future_k = max(k, 1) if grant_between(innings, i) and k == 0 else k
        return W[future_k, i + 1]

    for i in range(n - 1, -1, -1):
        W[0, i] = next_value(0, i)
        for k in range(1, kmax + 1):
            retained = next_value(k, i)
            consumed = next_value(k - 1, i)
            marginal = retained - consumed
            challenge = p[i] * (value[i] + retained) + (1 - p[i]) * consumed
            if policy == "dynamic":
                use = challenge > retained
            elif policy == "never":
                use = False
            elif policy.startswith("confidence_"):
                use = p[i] >= float(policy.split("_")[1])
            elif policy.startswith("ev_"):
                use = p[i] * value[i] >= float(policy.split("_")[1])
            else:
                raise ValueError(f"unknown policy: {policy}")
            W[k, i] = challenge if use else retained
            action[k, i] = use
            cost[k, i] = marginal
            denominator = value[i] + marginal
            threshold[k, i] = marginal / denominator if denominator > 0 else 1.0
    return {"W": W, "action": action, "cost": cost, "threshold": threshold}


def simulate_policy(p, value, innings, solution, inventory, repetitions, seed):
    rng = np.random.default_rng(seed)
    outcomes = np.zeros(repetitions)
    for repetition in range(repetitions):
        held = inventory
        total = 0.0
        prior_inning = innings[0] if len(innings) else 1
        for i in range(len(p)):
            if innings[i] > prior_inning and innings[i] >= 10 and held == 0:
                held = 1
            prior_inning = innings[i]
            if held > 0 and solution["action"][held, i]:
                if rng.random() < p[i]:
                    total += value[i]
                else:
                    held -= 1
        outcomes[repetition] = total
    return outcomes
