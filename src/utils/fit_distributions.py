import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.special import xlogy
import warnings
warnings.filterwarnings('ignore')
 

def fit_truncated_distributions(data_series, title=""):    
    """
    Fit truncated distributions to count data where zero values are missing.

    Parameters:
    - data_series : pd.Series
        Index = number of repetitive tasks, Values = count of objects/assets
    - title : str
        Title for the distribution (e.g., 'Objects' or 'Assets')

    Returns:
    - dict : Fitting results and metrics
    """
    # Extract x (counts) and y (frequencies)
    x_data = data_series.index.values.astype(float)
    y_data = data_series.values.astype(float)
    
    # Normalize to probability mass function for fitting
    y_normalized = y_data / y_data.sum()
    
    results = {'title': title, 'fits': {}}
    
    # --------------------
    # | TRUNCATED POISSON |
    # --------------------
    try:
        def truncated_poisson(x, lambda_param):
            """PMF of Poisson truncated at zero"""
            # P(X=k | X>0) = P(X=k) / P(X>0) = (lambda^k / k!) / (e^lambda - 1)
            return (lambda_param ** x / np.math.factorial(x)) / (np.exp(lambda_param) - 1)
        
        # Initial guess
        lambda_init = np.average(x_data, weights=y_data)
        
        popt, pcov = curve_fit(truncated_poisson, x_data, y_normalized, 
                               p0=[lambda_init], maxfev=10000)
        lambda_fit = popt[0]
        
        # Calculate R² and AIC
        y_pred = truncated_poisson(x_data, lambda_fit)
        ss_res = np.sum((y_normalized - y_pred) ** 2)
        ss_tot = np.sum((y_normalized - np.mean(y_normalized)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)
        
        k = 1  # number of parameters
        aic = 2 * k - 2 * np.sum(xlogy(y_data, y_pred))
        
        results['fits']['Truncated Poisson'] = {
            'params': {'lambda': lambda_fit},
            'r_squared': r_squared,
            'aic': aic,
            'y_pred': y_pred,
            'formula': f'λ = {lambda_fit:.4f}'
        }
        print(f"{title} - Truncated Poisson: λ={lambda_fit:.4f}, R²={r_squared:.4f}, AIC={aic:.2f}")
    except Exception as e:
        print(f"{title} - Truncated Poisson fitting failed: {e}")
    
    # -------------------------------
    # | TRUNCATED NEGATIVE BINOMIAL |
    # -------------------------------
    try:
        def truncated_negative_binomial(x, n, p):
            """PMF of Negative Binomial truncated at zero"""
            from scipy.special import binom
            # P(X=k | X>0) = C(n+k-1, k) * p^n * (1-p)^k / (1 - p^n)
            numerator = binom(n + x - 1, x) * (p ** n) * ((1 - p) ** x)
            denominator = 1 - (p ** n)
            return numerator / denominator
        
        # Initial guesses (method of moments)
        mean_x = np.average(x_data, weights=y_data)
        variance_x = np.average((x_data - mean_x) ** 2, weights=y_data)
        
        # For negative binomial: mean = r(1-p)/p, var = r(1-p)/p²
        # Estimate: p = mean / variance, r = mean² / (variance - mean)
        if variance_x > mean_x:
            p_init = mean_x / variance_x
            n_init = (mean_x ** 2) / (variance_x - mean_x)
        else:
            p_init = 0.5
            n_init = mean_x
        
        popt, pcov = curve_fit(truncated_negative_binomial, x_data, y_normalized,
                               p0=[n_init, p_init], maxfev=10000,
                               bounds=([0.1, 0.01], [100, 0.99]))
        n_fit, p_fit = popt
        
        y_pred = truncated_negative_binomial(x_data, n_fit, p_fit)
        ss_res = np.sum((y_normalized - y_pred) ** 2)
        ss_tot = np.sum((y_normalized - np.mean(y_normalized)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)
        
        k = 2  # number of parameters
        aic = 2 * k - 2 * np.sum(xlogy(y_data, y_pred))
        
        results['fits']['Truncated Negative Binomial'] = {
            'params': {'n': n_fit, 'p': p_fit},
            'r_squared': r_squared,
            'aic': aic,
            'y_pred': y_pred,
            'formula': f'n = {n_fit:.4f}, p = {p_fit:.4f}'
        }
        print(f"{title} - Truncated Negative Binomial: n={n_fit:.4f}, p={p_fit:.4f}, R²={r_squared:.4f}, AIC={aic:.2f}")
    except Exception as e:
        print(f"{title} - Truncated Negative Binomial fitting failed: {e}")
    
    # --------------------------------------------------------------------
    # | TRUNCATED GEOMETRIC (special case of Negative Binomial with n=1) |
    # --------------------------------------------------------------------
    try:
        def truncated_geometric(x, p):
            """PMF of Geometric truncated at zero"""
            # P(X=k | X>0) = (1-p)^(k-1) * p / (1 - p)
            # But for count of failures: (1-p)^k * p / (1 - p^inf) ≈ (1-p)^k * p
            return ((1 - p) ** x) * p / (1 - p)
        
        # Initial guess: p = 1 / (1 + mean)
        mean_x = np.average(x_data, weights=y_data)
        p_init = 1 / (1 + mean_x)
        
        popt, pcov = curve_fit(truncated_geometric, x_data, y_normalized,
                               p0=[p_init], maxfev=10000, bounds=([0.01], [0.99]))
        p_fit = popt[0]
        
        y_pred = truncated_geometric(x_data, p_fit)
        ss_res = np.sum((y_normalized - y_pred) ** 2)
        ss_tot = np.sum((y_normalized - np.mean(y_normalized)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)
        
        k = 1
        aic = 2 * k - 2 * np.sum(xlogy(y_data, y_pred))
        
        results['fits']['Truncated Geometric'] = {
            'params': {'p': p_fit},
            'r_squared': r_squared,
            'aic': aic,
            'y_pred': y_pred,
            'formula': f'p = {p_fit:.4f}'
        }
        print(f"{title} - Truncated Geometric: p={p_fit:.4f}, R²={r_squared:.4f}, AIC={aic:.2f}")
    except Exception as e:
        print(f"{title} - Truncated Geometric fitting failed: {e}")
    
    # ----------------------------------------------
    # | POWER LAW (Zipf-like where α is close to 1)|
    # ----------------------------------------------
    try:
        def power_law(x, alpha):
            """Power law: P(X=k) ∝ k^(-alpha)"""
            return x ** (-alpha) / np.sum(x_data ** (-alpha))
        
        # Initial guess
        alpha_init = 2.0
        
        popt, pcov = curve_fit(power_law, x_data, y_normalized,
                               p0=[alpha_init], maxfev=10000, bounds=([0.5], [5]))
        alpha_fit = popt[0]
        
        y_pred = power_law(x_data, alpha_fit)
        ss_res = np.sum((y_normalized - y_pred) ** 2)
        ss_tot = np.sum((y_normalized - np.mean(y_normalized)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)
        
        k = 1
        aic = 2 * k - 2 * np.sum(xlogy(y_data, y_pred))
        
        results['fits']['Power Law'] = {
            'params': {'alpha': alpha_fit},
            'r_squared': r_squared,
            'aic': aic,
            'y_pred': y_pred,
            'formula': f'α = {alpha_fit:.4f}'
        }
        print(f"{title} - Power Law: α={alpha_fit:.4f}, R²={r_squared:.4f}, AIC={aic:.2f}")
    except Exception as e:
        print(f"{title} - Power Law fitting failed: {e}")
    
    return results, x_data, y_data, y_normalized