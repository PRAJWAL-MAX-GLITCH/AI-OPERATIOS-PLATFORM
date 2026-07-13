"""
Neural Network Architectures & Model Factory
=============================================
Fully Connected (MLP) architectures for tabular data.
Extensible via ModelFactory for future CNN, LSTM, Transformer plug-ins.
"""
from __future__ import annotations
import torch
import torch.nn as nn
from typing import Any
import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Base MLP Building Block
# ---------------------------------------------------------------------------

class FCBlock(nn.Module):
    """A single fully-connected block: Linear → BatchNorm → Activation → Dropout."""

    def __init__(self, in_features: int, out_features: int, dropout: float = 0.3, activation: str = "relu"):
        super().__init__()
        act_map = {
            "relu":    nn.ReLU(),
            "leaky":   nn.LeakyReLU(0.1),
            "gelu":    nn.GELU(),
            "tanh":    nn.Tanh(),
            "sigmoid": nn.Sigmoid(),
        }
        self.block = nn.Sequential(
            nn.Linear(in_features, out_features),
            nn.BatchNorm1d(out_features),
            act_map.get(activation, nn.ReLU()),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)


# ---------------------------------------------------------------------------
# Task-Specific Network Heads
# ---------------------------------------------------------------------------

class BinaryClassificationNet(nn.Module):
    """MLP for Binary Classification → Sigmoid output."""

    def __init__(self, input_dim: int, hidden_dims: list[int], dropout: float = 0.3):
        super().__init__()
        layers = []
        prev = input_dim
        for h in hidden_dims:
            layers.append(FCBlock(prev, h, dropout=dropout))
            prev = h
        layers.append(nn.Linear(prev, 1))
        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x).squeeze(-1)  # (batch,)


class MultiClassNet(nn.Module):
    """MLP for Multi-class Classification → raw logits (use CrossEntropyLoss)."""

    def __init__(self, input_dim: int, num_classes: int, hidden_dims: list[int], dropout: float = 0.3):
        super().__init__()
        layers = []
        prev = input_dim
        for h in hidden_dims:
            layers.append(FCBlock(prev, h, dropout=dropout))
            prev = h
        layers.append(nn.Linear(prev, num_classes))
        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)  # (batch, num_classes)


class RegressionNet(nn.Module):
    """MLP for Regression → single scalar output."""

    def __init__(self, input_dim: int, hidden_dims: list[int], dropout: float = 0.3):
        super().__init__()
        layers = []
        prev = input_dim
        for h in hidden_dims:
            layers.append(FCBlock(prev, h, dropout=dropout))
            prev = h
        layers.append(nn.Linear(prev, 1))
        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x).squeeze(-1)  # (batch,)


# ---------------------------------------------------------------------------
# Model Factory
# ---------------------------------------------------------------------------

class DLModelFactory:
    """
    Factory for instantiating Deep Learning models.
    Future architectures (CNN, LSTM, Transformer) register here without
    touching any existing code.
    """

    _REGISTRY: dict[str, type[nn.Module]] = {
        "binary_classification": BinaryClassificationNet,
        "multiclass_classification": MultiClassNet,
        "regression": RegressionNet,
    }

    @classmethod
    def register(cls, name: str, model_class: type[nn.Module]) -> None:
        """Register a new model architecture at runtime."""
        cls._REGISTRY[name] = model_class
        logger.info("dl_model_registered", name=name)

    @classmethod
    def create(cls, problem_type: str, input_dim: int, config: dict[str, Any]) -> nn.Module:
        """
        Instantiate the correct model for the given problem type.
        config must supply hidden_dims, dropout, [num_classes for multiclass].
        """
        if problem_type not in cls._REGISTRY:
            raise ValueError(f"Unknown problem_type '{problem_type}'. Available: {list(cls._REGISTRY)}")

        hidden_dims = config.get("hidden_dims", [256, 128, 64])
        dropout     = config.get("dropout", 0.3)

        if problem_type == "binary_classification":
            model = BinaryClassificationNet(input_dim, hidden_dims, dropout)
        elif problem_type == "multiclass_classification":
            num_classes = config.get("num_classes")
            if num_classes is None:
                raise ValueError("num_classes must be provided for multiclass_classification")
            model = MultiClassNet(input_dim, num_classes, hidden_dims, dropout)
        else:  # regression
            model = RegressionNet(input_dim, hidden_dims, dropout)

        logger.info("dl_model_created", problem_type=problem_type, input_dim=input_dim)
        return model
