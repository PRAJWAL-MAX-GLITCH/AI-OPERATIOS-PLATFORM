"""
Model Factory
=============
Factory pattern for creating scikit-learn models based on algorithm string.
Supports classification, regression, clustering.
"""
from __future__ import annotations
from typing import Any

# Classification
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier

# Regression
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.tree import DecisionTreeRegressor

# Clustering
from sklearn.cluster import KMeans, DBSCAN


class ModelFactory:
    _classification_models = {
        "logistic_regression": LogisticRegression,
        "random_forest": RandomForestClassifier,
        "extra_trees": ExtraTreesClassifier,
        "gradient_boosting": GradientBoostingClassifier,
        "decision_tree": DecisionTreeClassifier,
    }

    _regression_models = {
        "linear_regression": LinearRegression,
        "ridge": Ridge,
        "lasso": Lasso,
        "random_forest": RandomForestRegressor,
        "extra_trees": ExtraTreesRegressor,
        "gradient_boosting": GradientBoostingRegressor,
        "decision_tree": DecisionTreeRegressor,
    }
    
    _clustering_models = {
        "kmeans": KMeans,
        "dbscan": DBSCAN,
    }

    @classmethod
    def create_model(cls, problem_type: str, algorithm: str, parameters: dict[str, Any]) -> Any:
        algorithm = algorithm.lower().strip()
        
        if problem_type == "classification":
            registry = cls._classification_models
        elif problem_type == "regression":
            registry = cls._regression_models
        elif problem_type == "clustering":
            registry = cls._clustering_models
        else:
            raise ValueError(f"Unsupported problem type: {problem_type}")

        if algorithm not in registry:
            raise ValueError(f"Algorithm '{algorithm}' not supported for {problem_type}. Available: {list(registry.keys())}")

        model_class = registry[algorithm]
        
        # Scikit-learn doesn't accept unknown parameters easily, so we just unpack
        try:
            return model_class(**parameters)
        except TypeError as e:
            raise ValueError(f"Invalid parameters for {algorithm}: {str(e)}")
