import numpy as np
import pandas as pd

def generate_corey_relperm(swc, sorw, nw, no, krw_max, kro_max):
    """Generates an ECLIPSE-style SWOF table using Corey's model with ZeroDivision protection."""
    # Denominator check: Ensures pore space for mobile fluid exists
    denominator = (1 - swc - sorw)
    
    # If mobile window is zero or negative, return a static 'blocked' table
    if denominator <= 1e-9:
        return pd.DataFrame({
            'Sw': [swc, 1.0],
            'Krw': [0.0, 0.0],
            'Kro': [0.0, 0.0],
            'Pc': [0.0, 0.0]
        })

    sw = np.linspace(swc, 1 - sorw, 15)
    sw_norm = (sw - swc) / denominator
    
    # Power law protection: Ensure exponents are not zero
    nw = max(nw, 1e-9)
    no = max(no, 1e-9)
    
    krw = krw_max * (sw_norm ** nw)
    kro = kro_max * ((1 - sw_norm) ** no)
    
    df = pd.DataFrame({
        'Sw': sw,
        'Krw': krw,
        'Kro': kro,
        'Pc': 0.0
    })
    return df

def calculate_eur(qi, di, b, economic_limit_q):
    """Calculates EUR with protection against zero decline, zero b-factor, and zero limits."""
    
    # 1. Guard against division by zero in basic inputs
    if di <= 1e-9:
        return 0.0, 0.0 # No decline means infinite life, return 0 for safety in EUR
    
    if economic_limit_q <= 1e-9:
        economic_limit_q = 0.1 # Set a floor for economic limit
        
    if qi <= economic_limit_q:
        return 0.0, 0.0 # Well is already below economic limit

    # 2. Handle the Arps b-factor cases
    # Case A: Exponential Decline (b = 0)
    if abs(b) < 1e-9:
        t_limit = np.log(qi / economic_limit_q) / di
        np_cum = (qi - economic_limit_q) / di
        
    # Case B: Harmonic Decline (b = 1)
    elif abs(b - 1.0) < 1e-9:
        t_limit = ((qi / economic_limit_q) - 1) / di
        np_cum = (qi / di) * np.log(qi / economic_limit_q)
        
    # Case C: Hyperbolic Decline (0 < b < 1)
    else:
        # Solve for t_limit: q = qi(1 + b*di*t)^(-1/b)
        t_limit = (((qi / economic_limit_q)**b) - 1) / (b * di)
        
        # Denominator check for the integration: (di * (1 - b))
        if abs(1 - b) < 1e-9:
            # Fallback to Harmonic logic if b is extremely close to 1
            np_cum = (qi / di) * np.log(qi / economic_limit_q)
        else:
            np_cum = (qi / (di * (1 - b))) * (1 - (1 + b * di * t_limit)**(1 - 1/b))
        
    return max(np_cum, 0), max(t_limit / 12, 0) # Return MSTB and Years