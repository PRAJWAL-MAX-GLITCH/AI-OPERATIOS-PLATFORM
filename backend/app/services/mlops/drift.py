"""
Data Drift Engine
=================
Calculates statistical drift between training baselines and production data.
"""
import numpy as np
from scipy import stats
import pandas as pd
from typing import Dict, Any, List

class DriftDetector:
    """Core logic for calculating statistical drift in features and predictions."""

    @staticmethod
    def calculate_psi(expected: np.ndarray, actual: np.ndarray, buckets: int = 10) -> float:
        """Calculate Population Stability Index (PSI) between two distributions."""
        def get_percentages(data: np.ndarray, breaks: np.ndarray) -> np.ndarray:
            counts = np.histogram(data, breaks)[0]
            # Replace 0 counts with small value to avoid division by zero
            counts = np.where(counts == 0, 0.0001, counts)
            return counts / sum(counts)

        # Create buckets based on expected (baseline) data
        breaks = np.linspace(expected.min(), expected.max(), buckets + 1)
        expected_perc = get_percentages(expected, breaks)
        actual_perc = get_percentages(actual, breaks)

        psi_value = np.sum((actual_perc - expected_perc) * np.log(actual_perc / expected_perc))
        return float(psi_value)

    @staticmethod
    def ks_test(expected: np.ndarray, actual: np.ndarray) -> Dict[str, float]:
        """Kolmogorov-Smirnov test for numerical drift."""
        statistic, p_value = stats.ks_2samp(expected, actual)
        return {
            "statistic": float(statistic),
            "p_value": float(p_value),
            "drift_detected": bool(p_value < 0.05)
        }

    @staticmethod
    def chi_square_test(expected: pd.Series, actual: pd.Series) -> Dict[str, float]:
        """Chi-Square test for categorical drift."""
        expected_counts = expected.value_counts(normalize=True)
        actual_counts = actual.value_counts(normalize=True)
        
        # Align indexes
        all_categories = set(expected_counts.index).union(set(actual_counts.index))
        exp_freq = np.array([expected_counts.get(cat, 0.0001) for cat in all_categories])
        act_freq = np.array([actual_counts.get(cat, 0.0001) for cat in all_categories])
        
        # Scale to frequencies assuming same sample size for valid chi-square
        sample_size = len(actual)
        exp_freq *= sample_size
        act_freq *= sample_size
        
        statistic, p_value = stats.chisquare(f_obs=act_freq, f_exp=exp_freq)
        return {
            "statistic": float(statistic),
            "p_value": float(p_value),
            "drift_detected": bool(p_value < 0.05)
        }

    @staticmethod
    def js_divergence(expected: np.ndarray, actual: np.ndarray, buckets: int = 10) -> float:
        """Jensen-Shannon divergence."""
        from scipy.spatial import distance
        breaks = np.linspace(expected.min(), expected.max(), buckets + 1)
        exp_hist = np.histogram(expected, breaks)[0]
        act_hist = np.histogram(actual, breaks)[0]
        
        exp_dist = exp_hist / np.sum(exp_hist)
        act_dist = act_hist / np.sum(act_hist)
        
        return float(distance.jensenshannon(exp_dist, act_dist))

    @staticmethod
    def evaluate_numerical_feature(expected: np.ndarray, actual: np.ndarray) -> Dict[str, Any]:
        """Runs a battery of tests for numerical features."""
        psi_score = DriftDetector.calculate_psi(expected, actual)
        ks_result = DriftDetector.ks_test(expected, actual)
        js_score = DriftDetector.js_divergence(expected, actual)
        
        # PSI > 0.2 indicates significant drift
        has_drift = bool(psi_score > 0.2 or ks_result["drift_detected"])
        
        return {
            "type": "numerical",
            "has_drift": has_drift,
            "metrics": {
                "psi": psi_score,
                "ks_statistic": ks_result["statistic"],
                "ks_p_value": ks_result["p_value"],
                "js_divergence": js_score
            }
        }
        
    @staticmethod
    def evaluate_categorical_feature(expected: pd.Series, actual: pd.Series) -> Dict[str, Any]:
        """Runs a battery of tests for categorical features."""
        chi2_result = DriftDetector.chi_square_test(expected, actual)
        
        return {
            "type": "categorical",
            "has_drift": chi2_result["drift_detected"],
            "metrics": {
                "chi2_statistic": chi2_result["statistic"],
                "chi2_p_value": chi2_result["p_value"]
            }
        }
