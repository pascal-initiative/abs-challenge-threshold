"""Pure helpers for the ABS-05 win-probability sensitivity."""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize


PHASES = [(inning, half) for inning in range(1, 11) for half in ("top", "bottom")]
PHASE_INDEX = {phase: index for index, phase in enumerate(PHASES)}


def phase_index(inning, half) -> np.ndarray:
    capped = np.minimum(np.asarray(inning, dtype=int), 10)
    halves = np.asarray(half).astype(str)
    return np.asarray([PHASE_INDEX[(int(i), str(h))] for i, h in zip(capped, halves)], dtype=int)


def design_matrix(inning, half, advantage) -> np.ndarray:
    advantage = np.asarray(advantage, dtype=float)
    phases = phase_index(inning, half)
    matrix = np.zeros((len(advantage), len(PHASES) * 2))
    rows = np.arange(len(advantage))
    matrix[rows, phases] = 1.0
    matrix[rows, len(PHASES) + phases] = advantage
    return matrix


def _sigmoid(value):
    value = np.asarray(value, dtype=float)
    positive = value >= 0
    out = np.empty_like(value)
    out[positive] = 1 / (1 + np.exp(-value[positive]))
    exponential = np.exp(value[~positive])
    out[~positive] = exponential / (1 + exponential)
    return out


def fit_bounded_logistic(matrix, target, weights, penalty: float = 1e-4):
    matrix = np.asarray(matrix, dtype=float)
    target = np.asarray(target, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if matrix.ndim != 2 or len(matrix) != len(target) or len(target) != len(weights):
        raise ValueError("matrix, target, and weights must align")
    if not np.isfinite(matrix).all() or not np.isfinite(weights).all():
        raise ValueError("model inputs must be finite")
    if ((target < 0) | (target > 1)).any() or (weights <= 0).any():
        raise ValueError("invalid target or weight")
    weights = weights * (len(weights) / weights.sum())

    def objective(beta):
        linear = matrix @ beta
        loss = np.logaddexp(0.0, linear) - target * linear
        return float(np.dot(weights, loss) + 0.5 * penalty * np.dot(beta, beta))

    def gradient(beta):
        residual = (_sigmoid(matrix @ beta) - target) * weights
        return matrix.T @ residual + penalty * beta

    bounds = [(None, None)] * len(PHASES) + [(0.0, None)] * len(PHASES)
    solved = minimize(
        objective,
        np.zeros(matrix.shape[1]),
        jac=gradient,
        method="L-BFGS-B",
        bounds=bounds,
        options={"ftol": 1e-12, "gtol": 1e-8, "maxiter": 2000},
    )
    if not solved.success:
        raise RuntimeError(f"bounded win model failed: {solved.message}")
    return {
        "coef": solved.x,
        "objective": objective(solved.x),
        "iterations": int(solved.nit),
        "minimum_advantage_slope": float(solved.x[len(PHASES):].min()),
    }


def predict(model, matrix) -> np.ndarray:
    return _sigmoid(np.asarray(matrix, dtype=float) @ np.asarray(model["coef"], dtype=float))


def fit_phase_logistic(inning, half, advantage, target, weights, penalty: float = 1e-4):
    """Memory-efficient equivalent of the bounded phase design."""
    phases = phase_index(inning, half)
    advantage = np.asarray(advantage, dtype=float)
    target = np.asarray(target, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if not (len(phases) == len(advantage) == len(target) == len(weights)):
        raise ValueError("phase model inputs must align")
    if not np.isfinite(advantage).all() or not np.isfinite(weights).all():
        raise ValueError("phase model inputs must be finite")
    if ((target < 0) | (target > 1)).any() or (weights <= 0).any():
        raise ValueError("invalid target or weight")
    weights = weights * (len(weights) / weights.sum())
    phase_count = len(PHASES)

    def linear(beta):
        return beta[phases] + beta[phase_count + phases] * advantage

    def objective(beta):
        values = linear(beta)
        loss = np.logaddexp(0.0, values) - target * values
        return float(np.dot(weights, loss) + 0.5 * penalty * np.dot(beta, beta))

    def gradient(beta):
        residual = (_sigmoid(linear(beta)) - target) * weights
        return np.concatenate([
            np.bincount(phases, weights=residual, minlength=phase_count),
            np.bincount(phases, weights=residual * advantage, minlength=phase_count),
        ]) + penalty * beta

    bounds = [(None, None)] * phase_count + [(0.0, None)] * phase_count
    solved = minimize(
        objective,
        np.zeros(phase_count * 2),
        jac=gradient,
        method="L-BFGS-B",
        bounds=bounds,
        options={"ftol": 1e-12, "gtol": 1e-8, "maxiter": 2000},
    )
    if not solved.success:
        raise RuntimeError(f"bounded phase win model failed: {solved.message}")
    return {
        "coef": solved.x,
        "objective": objective(solved.x),
        "iterations": int(solved.nit),
        "minimum_advantage_slope": float(solved.x[phase_count:].min()),
    }


def predict_phase(model, inning, half, advantage) -> np.ndarray:
    phases = phase_index(inning, half)
    advantage = np.asarray(advantage, dtype=float)
    coefficients = np.asarray(model["coef"], dtype=float)
    phase_count = len(PHASES)
    return _sigmoid(
        coefficients[phases] + coefficients[phase_count + phases] * advantage
    )


def opponent_adjusted_delta(challenge_value, hold_value, opponent_value):
    return (challenge_value - opponent_value) - (hold_value - opponent_value)
