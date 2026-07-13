"""
Loss Functions & Optimizer Factory
====================================
Configurable loss functions and optimizers with LR scheduler support.
"""
from __future__ import annotations
import torch
import torch.nn as nn
from torch.optim import Adam, AdamW, SGD, RMSprop
from torch.optim.lr_scheduler import (
    CosineAnnealingLR, StepLR, ReduceLROnPlateau, LinearLR, SequentialLR
)
from typing import Any
import structlog

logger = structlog.get_logger(__name__)


def get_loss_function(problem_type: str, config: dict[str, Any]) -> nn.Module:
    """
    Returns the appropriate loss function.
    problem_type: binary_classification | multiclass_classification | regression
    """
    loss_override = config.get("loss_fn")

    if loss_override == "huber":
        return nn.HuberLoss(delta=config.get("huber_delta", 1.0))
    elif loss_override == "mae":
        return nn.L1Loss()
    elif loss_override == "mse":
        return nn.MSELoss()
    elif loss_override == "bce":
        return nn.BCEWithLogitsLoss()
    elif loss_override == "crossentropy":
        return nn.CrossEntropyLoss()

    # Defaults by problem type
    if problem_type == "binary_classification":
        return nn.BCEWithLogitsLoss()
    elif problem_type == "multiclass_classification":
        return nn.CrossEntropyLoss()
    else:  # regression
        return nn.MSELoss()


def get_optimizer(model: nn.Module, config: dict[str, Any]) -> torch.optim.Optimizer:
    """
    Returns the configured optimizer.
    Supports: adam | adamw | sgd | rmsprop
    """
    lr       = config.get("learning_rate", 1e-3)
    wd       = config.get("weight_decay", 1e-4)
    opt_name = config.get("optimizer", "adamw").lower()

    if opt_name == "adam":
        return Adam(model.parameters(), lr=lr, weight_decay=wd)
    elif opt_name == "adamw":
        return AdamW(model.parameters(), lr=lr, weight_decay=wd)
    elif opt_name == "sgd":
        momentum = config.get("momentum", 0.9)
        return SGD(model.parameters(), lr=lr, momentum=momentum, weight_decay=wd)
    elif opt_name == "rmsprop":
        return RMSprop(model.parameters(), lr=lr, weight_decay=wd)
    else:
        logger.warning("unknown_optimizer", optimizer=opt_name, fallback="adamw")
        return AdamW(model.parameters(), lr=lr, weight_decay=wd)


def get_scheduler(
    optimizer: torch.optim.Optimizer,
    config: dict[str, Any],
    total_epochs: int
) -> Any:
    """
    Returns an optional LR scheduler.
    Supports: cosine | step | plateau | warmup_cosine | None
    """
    sched_name = config.get("scheduler")

    if sched_name == "cosine":
        return CosineAnnealingLR(optimizer, T_max=total_epochs, eta_min=1e-6)
    elif sched_name == "step":
        return StepLR(optimizer, step_size=config.get("step_size", 10), gamma=config.get("gamma", 0.5))
    elif sched_name == "plateau":
        return ReduceLROnPlateau(optimizer, mode="min", patience=5, factor=0.5)
    elif sched_name == "warmup_cosine":
        warmup = config.get("warmup_epochs", 5)
        warmup_sched = LinearLR(optimizer, start_factor=0.1, total_iters=warmup)
        cosine_sched = CosineAnnealingLR(optimizer, T_max=total_epochs - warmup, eta_min=1e-6)
        return SequentialLR(optimizer, schedulers=[warmup_sched, cosine_sched], milestones=[warmup])
    return None
