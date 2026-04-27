"""
reservoir_math_fit.py
─────────────────────────────────────────────────────────────────────────────
fit_production_data() — Arps DCA curve fitting with automatic model selection.

Fits three Arps decline models (exponential, hyperbolic, harmonic) to a
production rate history and returns the best-fit (qi, Di, b) parameters
selected by R².

Dependencies: numpy, scipy

Usage:
    from reservoir_math_fit import fit_production_data

    qi, di, b = fit_production_data(monthly_rates)
    qi, di, b = fit_production_data(quarterly_rates, time_step_months=3.0)
"""

import warnings
from typing import Tuple

import numpy as np
from scipy.optimize import curve_fit


# ─────────────────────────────────────────────────────────────────────────────
# Arps decline models
# ─────────────────────────────────────────────────────────────────────────────

def _arps_exponential(t: np.ndarray, qi: float, di: float) -> np.ndarray:
    """q(t) = qi · exp(−Di · t)"""
    return qi * np.exp(-di * t)


def _arps_hyperbolic(t: np.ndarray, qi: float, di: float, b: float) -> np.ndarray:
    """q(t) = qi / (1 + b·Di·t)^(1/b)"""
    b = np.clip(b, 1e-6, 2.0)
    return qi / (1.0 + b * di * t) ** (1.0 / b)


def _arps_harmonic(t: np.ndarray, qi: float, di: float) -> np.ndarray:
    """q(t) = qi / (1 + Di·t)    [Arps special case: b = 1]"""
    return qi / (1.0 + di * t)


# ─────────────────────────────────────────────────────────────────────────────
# Goodness-of-fit
# ─────────────────────────────────────────────────────────────────────────────

def _r2(observed: np.ndarray, predicted: np.ndarray) -> float:
    ss_res = np.sum((observed - predicted) ** 2)
    ss_tot = np.sum((observed - np.mean(observed)) ** 2)
    return float(1.0 - ss_res / ss_tot) if ss_tot > 0 else 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def fit_production_data(
    rates: "list | np.ndarray",
    time_step_months: float = 1.0,
) -> Tuple[float, float, float]:
    """
    Fit Arps decline curve parameters to a production rate history.

    Tries three Arps models (exponential, hyperbolic, harmonic), selects the
    best fit by R², and returns the unified (qi, Di, b) parameter set.

    Args:
        rates:
            Chronological sequence of production rates (STB/D, Mscf/D, etc.),
            one value per time step. Zeros, negatives, and NaNs are dropped
            before fitting; the surviving points are remapped to a consecutive
            time axis so gaps do not distort the Di estimate.

        time_step_months:
            Duration of each time step in months (default 1.0 = monthly).
            Pass 3.0 for quarterly data, 12.0 for annual data.
            Di is returned per time step in the original unit; convert with:
                Di_annual  = 1 − exp(−Di_monthly × 12)
                Di_monthly = −ln(1 − Di_annual) / 12

    Returns:
        Tuple (qi, Di, b):
            qi  — Initial rate at t = 0, same units as input [STB/D etc.]
            Di  — Nominal decline rate per time step [fraction, not percent]
            b   — Arps b-factor [dimensionless]
                  b ≈ 0.0  → exponential (constant fractional decline)
                  0 < b < 1 → hyperbolic (most common in practice)
                  b = 1.0  → harmonic
                  b > 1.0  → signals transient flow, fractures, or layering;
                              values above 1.2 warrant engineering review.

    Raises:
        ValueError: If fewer than 3 valid (positive, finite) data points remain
                    after cleaning.

    Notes:
        - b is clamped to [0.0, 2.0]. Values > 2.0 are unphysical under Arps
          theory and typically indicate data quality problems or transient flow
          that the model cannot capture.
        - If all three scipy fits fail (e.g. degenerate data), a log-linear
          regression fallback is applied and b is set to 0.0.
        - The returned Di is NOT annualised. Multiply by (12 / time_step_months)
          only if you need a per-year figure.
    """
    # ── 1. Clean input ────────────────────────────────────────────────────────
    rates_arr = np.asarray(rates, dtype=float)
    valid_mask = np.isfinite(rates_arr) & (rates_arr > 0)
    rates_clean = rates_arr[valid_mask]

    if len(rates_clean) < 3:
        raise ValueError(
            f"fit_production_data requires at least 3 valid (positive, finite) "
            f"data points; {len(rates_clean)} remain after removing zeros, "
            f"negatives, and NaNs."
        )

    # Remap to a consecutive time axis.
    # This ensures that gaps created by dropped points do not inflate Di.
    t = np.arange(len(rates_clean), dtype=float)

    # ── 2. Initial parameter guesses ─────────────────────────────────────────
    # qi: maximum of first 3 valid points (avoids assuming the well was at
    #     peak on its very first recorded time step)
    qi_guess = float(np.max(rates_clean[:3]))
    qi_guess = max(qi_guess, 1.0)

    # Di: log-linear slope between first and last valid point
    if rates_clean[-1] < rates_clean[0] and t[-1] > 0:
        di_guess = float(-np.log(rates_clean[-1] / rates_clean[0]) / t[-1])
    else:
        di_guess = 0.05  # Flat or briefly increasing — conservative starting point
    di_guess = max(di_guess, 1e-4)

    qi_upper = qi_guess * 2.0   # Upper bound: allow fitter some room above guess

    # ── 3. Fit all three Arps models ─────────────────────────────────────────
    candidates = [
        # (model_fn,          p0,                        bounds,                           fixed_b)
        (_arps_exponential,   [qi_guess, di_guess],       ([0, 1e-6], [qi_upper, 5.0]),    0.0),
        (_arps_hyperbolic,    [qi_guess, di_guess, 0.5],  ([0, 1e-6, 1e-6], [qi_upper, 5.0, 2.0]), None),
        (_arps_harmonic,      [qi_guess, di_guess],       ([0, 1e-6], [qi_upper, 5.0]),    1.0),
    ]

    best: dict = {"model": None, "qi": qi_guess, "di": di_guess, "b": 0.0, "r2": -np.inf}

    for model_fn, p0, bounds, fixed_b in candidates:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                popt, _ = curve_fit(
                    model_fn, t, rates_clean,
                    p0=p0, bounds=bounds,
                    maxfev=8000,
                )
            r2 = _r2(rates_clean, model_fn(t, *popt))
            if r2 > best["r2"]:
                best = {
                    "model": model_fn.__name__,
                    "qi":    float(popt[0]),
                    "di":    float(popt[1]),
                    "b":     float(popt[2]) if fixed_b is None else fixed_b,
                    "r2":    r2,
                }
        except Exception:
            # curve_fit can raise RuntimeError (max iterations) or ValueError
            # (bad initial guess). Continue to the next model.
            continue

    # ── 4. Log-linear fallback (always succeeds) ──────────────────────────────
    if best["model"] is None or best["r2"] < 0:
        log_rates = np.log(np.maximum(rates_clean, 1.0))
        slope, intercept = np.polyfit(t, log_rates, 1)
        qi_fb = float(np.exp(intercept))
        di_fb = max(float(-slope), 1e-4)
        pred_fb = _arps_exponential(t, qi_fb, di_fb)
        best = {
            "model": "log_linear_fallback",
            "qi":    qi_fb,
            "di":    di_fb,
            "b":     0.0,
            "r2":    _r2(rates_clean, pred_fb),
        }

    # ── 5. Clamp and return ───────────────────────────────────────────────────
    qi = max(float(best["qi"]), 0.0)
    di = max(float(best["di"]), 0.0)
    b  = float(np.clip(best["b"], 0.0, 2.0))

    return qi, di, b


# ─────────────────────────────────────────────────────────────────────────────
# Self-tests  (run with: python reservoir_math_fit.py)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    np.random.seed(42)
    t24 = np.arange(24, dtype=float)
    PASS = FAIL = 0

    def check(name, rates, qi_true, di_true, b_true,
              tol_qi=0.10, tol_di=0.30, tol_b=0.20):
        global PASS, FAIL
        try:
            qi, di, b = fit_production_data(rates)
            ok = (
                abs(qi - qi_true) / max(qi_true, 1)           < tol_qi and
                abs(di - di_true) / max(di_true, 1e-6)        < tol_di and
                (abs(b - b_true)  / max(b_true, 0.1) < tol_b  or
                 abs(b - b_true)                      < 0.15)
            )
            icon = "✅ PASS" if ok else "⚠️  WARN"
            PASS += ok; FAIL += not ok
            print(f"{icon} | {name}")
            print(f"       True : qi={qi_true:>7.1f}  Di={di_true:.4f}  b={b_true:.2f}")
            print(f"       Fit  : qi={qi:>7.1f}  Di={di:.4f}  b={b:.2f}")
        except Exception as e:
            FAIL += 1
            print(f"❌ FAIL | {name}: {e}")
        print()

    print("=" * 62)
    print("  fit_production_data() — Test Suite")
    print("=" * 62)
    print()

    check("Clean exponential (b=0)",
          _arps_exponential(t24, 4500, 0.12),              4500, 0.12, 0.0)

    check("Clean hyperbolic (b=0.8)",
          _arps_hyperbolic(t24, 3200, 0.15, 0.8),          3200, 0.15, 0.8)

    check("Clean harmonic (b=1.0)",
          _arps_harmonic(t24, 2800, 0.10),                 2800, 0.10, 1.0)

    check("Noisy hyperbolic (b=0.6, σ=80)",
          _arps_hyperbolic(t24, 4000, 0.18, 0.6) + np.random.normal(0, 80, 24),
          4000, 0.18, 0.6, tol_di=0.40, tol_b=0.40)

    check("Shallow decline (Di=0.03, b=0.3)",
          _arps_hyperbolic(t24, 2000, 0.03, 0.3),          2000, 0.03, 0.3, tol_di=0.40)

    check("Steep exponential (Di=0.30)",
          _arps_exponential(t24, 6000, 0.30),              6000, 0.30, 0.0)

    check("Short series — 5 points",
          _arps_exponential(np.arange(5, dtype=float), 3000, 0.10),
          3000, 0.10, 0.0, tol_di=0.40)

    check("Minimum data — 3 points",
          [5000, 4400, 3872],                              5000, 0.12, 0.0, tol_di=0.50)

    check("Series with zeros/negatives dropped",
          [4000, 3600, -50, 0, 2920, 2630, 2367],
          # After dropping: [4000, 3600, 2920, 2630, 2367]
          # True Di ≈ 0.136 per step on the surviving 5 points
          4000, 0.136, 0.0, tol_qi=0.12, tol_di=0.35, tol_b=0.50)

    # ValueError: too few valid points
    print("Expected ValueError | Only 2 valid points")
    try:
        fit_production_data([5000, 0])
        print("❌ FAIL — should have raised ValueError\n")
        FAIL += 1
    except ValueError as e:
        print(f"✅ PASS — raised ValueError: {e}\n")
        PASS += 1

    print("=" * 62)
    print(f"  Results: {PASS} passed, {FAIL} failed / warned")
    print("=" * 62)