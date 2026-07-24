"""
Model Monitoring & Drift Detection Tests
========================================
"""
import pytest
import numpy as np
import pandas as pd
from app.services.mlops.drift import DriftDetector

class TestDriftDetector:
    def test_psi_identical_distributions(self):
        np.random.seed(42)
        expected = np.random.normal(50, 10, 1000)
        actual = expected.copy()
        
        psi = DriftDetector.calculate_psi(expected, actual)
        # Should be very close to 0
        assert psi < 0.05
        
    def test_psi_shifted_distributions(self):
        np.random.seed(42)
        expected = np.random.normal(50, 10, 1000)
        actual = np.random.normal(60, 10, 1000) # Shifted mean
        
        psi = DriftDetector.calculate_psi(expected, actual)
        # Should indicate significant drift (typically > 0.2)
        assert psi > 0.2

    def test_ks_test(self):
        np.random.seed(42)
        expected = np.random.normal(0, 1, 1000)
        actual = np.random.normal(1, 1, 1000)
        
        result = DriftDetector.ks_test(expected, actual)
        assert result["drift_detected"] is True
        assert result["p_value"] < 0.05

    def test_chi_square_test(self):
        expected = pd.Series(["A"] * 500 + ["B"] * 500)
        # Distribution changed to mostly A
        actual = pd.Series(["A"] * 800 + ["B"] * 200)
        
        result = DriftDetector.chi_square_test(expected, actual)
        assert result["drift_detected"] is True
        assert result["p_value"] < 0.05

    def test_evaluate_numerical_feature(self):
        np.random.seed(42)
        expected = np.random.normal(100, 15, 1000)
        actual = np.random.normal(120, 15, 1000)
        
        result = DriftDetector.evaluate_numerical_feature(expected, actual)
        assert result["type"] == "numerical"
        assert result["has_drift"] is True
        assert result["metrics"]["psi"] > 0.2
        assert result["metrics"]["ks_p_value"] < 0.05
