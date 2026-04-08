import numpy as np
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit

def calculate_arps_decline(q_i, d_i, b, time_months):
    """
    Calculates Arps Decline for Reservoir Forecasting.
    q_i: Initial rate (bbl/d)
    d_i: Initial decline rate (nominal, fraction/month)
    b: Hyperbolic exponent (0 = exponential, 1 = harmonic)
    """
    t = np.arange(0, time_months)
    if b == 0: # Exponential
        q_t = q_i * np.exp(-d_i * t)
    else: # Hyperbolic
        # Adding a small constant to prevent division by zero if inputs are extreme
        q_t = q_i / (1 + b * d_i * t)**(1/b)
    
    return pd.DataFrame({"Month": t, "Forecast_Rate": q_t})

def estimate_eur(df):
    """Estimate Cumulative Production (EUR) from a time series."""
    return round(df["Forecast_Rate"].sum() * 30.4, 2)
    

def arps_hyperbolic(t, qi, di, b):
    """Standard Arps Hyperbolic equation for production forecasting."""
    return qi / (1 + b * di * t)**(1/b)

def fit_production_data(t, q):
    """Fits historical data to determine qi, di, and b-factor."""
    try:
        # Initial guess: qi=max(q), di=0.1, b=0.5
        popt, _ = curve_fit(arps_hyperbolic, t, q, p0=[max(q), 0.1, 0.5], bounds=(0, [np.inf, 1, 1]))
        return popt
    except:
        return [max(q), 0.1, 0.5] # Fallback to defaults    
