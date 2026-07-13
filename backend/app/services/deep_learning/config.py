"""
PyTorch Device & Environment Configuration
==========================================
Handles GPU detection, CPU fallback, seed management and deterministic training.
"""
from __future__ import annotations
import os
import random
import numpy as np
import torch
import structlog

logger = structlog.get_logger(__name__)


def get_device() -> torch.device:
    """Detects and returns the best available device (CUDA → MPS → CPU)."""
    if torch.cuda.is_available():
        device = torch.device("cuda")
        logger.info("dl_device_selected", device="cuda", name=torch.cuda.get_device_name(0))
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
        logger.info("dl_device_selected", device="mps")
    else:
        device = torch.device("cpu")
        logger.info("dl_device_selected", device="cpu")
    return device


def set_seed(seed: int = 42) -> None:
    """Sets global seed for full reproducibility across Python, NumPy and PyTorch."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    logger.info("dl_seed_set", seed=seed)


def get_device_info() -> dict:
    """Returns a summary of the available compute resources."""
    info: dict = {
        "cuda_available": torch.cuda.is_available(),
        "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "mps_available": torch.backends.mps.is_available(),
        "selected_device": str(get_device()),
    }
    if torch.cuda.is_available():
        info["gpu_name"] = torch.cuda.get_device_name(0)
        info["gpu_memory_gb"] = round(torch.cuda.get_device_properties(0).total_memory / 1e9, 2)
    return info
