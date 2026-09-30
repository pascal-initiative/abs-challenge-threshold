"""Pure primitives for the non-clairvoyant CT-2026 reference evaluator."""
from __future__ import annotations

import hashlib

import numpy as np


TOLERANCE = 1e-12


def fixed_ev_actions(p, value, cutoff=0.05, kmax=2, tolerance=TOLERANCE):
    """Return the frozen future-use policy: challenge when p * V >= cutoff.

    The action rule deliberately ignores inventory, inning, and the realized
    future sequence. Inventory zero can never challenge; every positive
    inventory level follows the same predeclared rule. Ties challenge.
    """
    p = np.asarray(p, dtype=float)
    value = np.asarray(value, dtype=float)
    p, value = np.broadcast_arrays(p, value)
    if p.ndim != 1:
        raise ValueError("p and value must be one-dimensional")
    if np.any(~np.isfinite(p)) or np.any(~np.isfinite(value)):
        raise ValueError("p and value must be finite")
    if np.any((p < 0) | (p > 1)):
        raise ValueError("probabilities must lie in [0, 1]")
    if not np.isfinite(cutoff) or cutoff < 0:
        raise ValueError("cutoff must be finite and nonnegative")
    # A noisy sensitivity estimator can assign a negative value to correction.
    # Such an opportunity never satisfies a nonnegative EV cutoff. The
    # publication threshold for that variant is separately reported undefined.
    use = p * value >= cutoff - tolerance
    actions = np.zeros((kmax + 1, len(p)), dtype=bool)
    actions[1:] = use
    return actions


def challenge_threshold(value, cost):
    """Return C/(V+C), with the frozen CT-2026 boundary conventions."""
    value = np.asarray(value, dtype=float)
    cost = np.asarray(cost, dtype=float)
    value, cost = np.broadcast_arrays(value, cost)
    if np.any(~np.isfinite(value)) or np.any(~np.isfinite(cost)):
        raise ValueError("value and cost must be finite")
    if np.any(value < -TOLERANCE) or np.any(cost < -TOLERANCE):
        raise ValueError("value and cost must be nonnegative")
    value = np.maximum(value, 0.0)
    cost = np.maximum(cost, 0.0)
    denominator = value + cost
    result = np.full(denominator.shape, np.nan, dtype=float)
    valid = denominator > 0
    result[valid] = cost[valid] / denominator[valid]
    return result


def grant_between(innings, index: int, grant_extras: bool = True) -> bool:
    """Whether zero inventory is restored before the next observed opportunity."""
    if not grant_extras:
        return False
    return bool(
        index + 1 < len(innings)
        and innings[index + 1] > innings[index]
        and innings[index + 1] >= 10
    )


def evaluate_fixed_actions(p, value, innings, actions, grant_extras=True, kmax=2):
    """Evaluate actions that were selected without access to the future path."""
    p = np.asarray(p, dtype=float)
    value = np.asarray(value, dtype=float)
    innings = np.asarray(innings, dtype=int)
    actions = np.asarray(actions, dtype=bool)
    if not (len(p) == len(value) == len(innings)):
        raise ValueError("p, value, and innings must have equal length")
    if actions.shape != (kmax + 1, len(p)):
        raise ValueError("actions must have shape (kmax + 1, opportunities)")
    if np.any((p < 0) | (p > 1)):
        raise ValueError("probabilities must lie in [0, 1]")

    n = len(p)
    W = np.zeros((kmax + 1, n + 1), dtype=float)
    cost = np.zeros((kmax + 1, n), dtype=float)

    def next_value(k, i):
        future_k = max(k, 1) if grant_between(innings, i, grant_extras) and k == 0 else k
        return W[future_k, i + 1]

    for i in range(n - 1, -1, -1):
        W[0, i] = next_value(0, i)
        for k in range(1, kmax + 1):
            retained = next_value(k, i)
            consumed = next_value(k - 1, i)
            cost[k, i] = retained - consumed
            challenge = p[i] * (value[i] + retained) + (1 - p[i]) * consumed
            W[k, i] = challenge if actions[k, i] else retained
    return {"W": W, "cost": cost}


def select_actions(p, value, state_codes, schedule, tolerance=TOLERANCE):
    """Select actions from current information and a prior state-cost schedule."""
    p = np.asarray(p, dtype=float)
    value = np.asarray(value, dtype=float)
    state_codes = np.asarray(state_codes, dtype=int)
    schedule = np.asarray(schedule, dtype=float)
    if not (len(p) == len(value) == len(state_codes)):
        raise ValueError("p, value, and state_codes must have equal length")
    if schedule.ndim != 2 or schedule.shape[0] < 2:
        raise ValueError("schedule must have inventory rows")
    if np.any(state_codes < 0) or np.any(state_codes >= schedule.shape[1]):
        raise ValueError("state code outside schedule")

    actions = np.zeros((schedule.shape[0], len(p)), dtype=bool)
    for inventory in range(1, schedule.shape[0]):
        cost = schedule[inventory, state_codes]
        delta = p * value - (1 - p) * cost
        actions[inventory] = delta > tolerance
    return actions


def aggregate_schedule(costs, state_codes, state_count, kmax=2):
    """Average evaluated marginal continuation cost within each state."""
    costs = np.asarray(costs, dtype=float)
    state_codes = np.asarray(state_codes, dtype=int)
    if costs.shape[0] != kmax + 1 or costs.shape[1] != len(state_codes):
        raise ValueError("cost matrix shape mismatch")
    counts = np.bincount(state_codes, minlength=state_count).astype(float)
    if np.any(counts == 0):
        raise ValueError("every state code must have observations")
    schedule = np.zeros((kmax + 1, state_count), dtype=float)
    for inventory in range(1, kmax + 1):
        totals = np.bincount(
            state_codes, weights=costs[inventory], minlength=state_count
        )
        schedule[inventory] = totals / counts
    return schedule


def stable_hash(*arrays) -> str:
    digest = hashlib.sha256()
    for array in arrays:
        value = np.ascontiguousarray(array)
        digest.update(str(value.dtype).encode("ascii"))
        digest.update(str(value.shape).encode("ascii"))
        digest.update(value.tobytes())
    return digest.hexdigest()


def fit_state_policy(
    p,
    value,
    innings,
    state_codes,
    groups,
    state_count,
    grant_extras=True,
    kmax=2,
    tolerance=1e-10,
    max_iterations=200,
):
    """Fit CT's state-only policy and return its converged schedule and audit."""
    p = np.asarray(p, dtype=float)
    value = np.asarray(value, dtype=float)
    innings = np.asarray(innings, dtype=int)
    state_codes = np.asarray(state_codes, dtype=int)
    if not (len(p) == len(value) == len(innings) == len(state_codes)):
        raise ValueError("row arrays must have equal length")

    schedule = np.zeros((kmax + 1, state_count), dtype=float)
    prior_actions = None
    prior_policy_hash = None
    seen_policy_hashes = {}
    history = []
    converged = False
    final_actions = None
    final_costs = None
    final_game_values = None

    for iteration in range(1, max_iterations + 1):
        actions = select_actions(p, value, state_codes, schedule)
        policy_hash = stable_hash(actions)
        if policy_hash in seen_policy_hashes and policy_hash != prior_policy_hash:
            return {
                "converged": False,
                "cycle_detected": True,
                "iterations": iteration,
                "history": history,
                "repeated_policy_hash": policy_hash,
                "first_seen_iteration": seen_policy_hashes[policy_hash],
            }

        costs = np.zeros((kmax + 1, len(p)), dtype=float)
        game_values = []
        for group_id, positions in groups:
            positions = np.asarray(positions, dtype=int)
            evaluated = evaluate_fixed_actions(
                p[positions],
                value[positions],
                innings[positions],
                actions[:, positions],
                grant_extras=grant_extras,
                kmax=kmax,
            )
            costs[:, positions] = evaluated["cost"]
            game_values.append(
                (group_id, *[float(evaluated["W"][k, 0]) for k in range(kmax + 1)])
            )

        new_schedule = aggregate_schedule(costs, state_codes, state_count, kmax)
        maximum_change = float(np.max(np.abs(new_schedule - schedule)))
        policy_stable = prior_actions is not None and np.array_equal(actions, prior_actions)
        history.append({
            "iteration": iteration,
            "policy_hash": policy_hash,
            "schedule_hash": stable_hash(new_schedule),
            "maximum_schedule_change": maximum_change,
            "policy_stable": bool(policy_stable),
            "challenge_count_inventory_1": int(actions[1].sum()),
            "challenge_count_inventory_2": int(actions[2].sum()),
        })

        final_actions = actions
        final_costs = costs
        final_game_values = game_values
        if policy_stable and maximum_change <= tolerance:
            schedule = new_schedule
            converged = True
            break

        seen_policy_hashes[policy_hash] = iteration
        prior_policy_hash = policy_hash
        prior_actions = actions
        schedule = new_schedule

    return {
        "converged": converged,
        "cycle_detected": False,
        "iterations": len(history),
        "history": history,
        "schedule": schedule,
        "actions": final_actions,
        "row_costs": final_costs,
        "game_values": final_game_values,
    }
