"""
PyTorch Dataset Wrappers
========================
Generic tabular dataset supporting CSV, Pandas, and NumPy sources.
Future-extensible for images, text, time-series.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader, random_split
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)


class TabularDataset(Dataset):
    """
    Generic PyTorch Dataset for tabular data (CSV / Pandas / NumPy).
    Converts features and labels to float32 tensors.
    """

    def __init__(self, X: np.ndarray, y: np.ndarray):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int):
        return self.X[idx], self.y[idx]


def build_dataloaders(
    X: np.ndarray,
    y: np.ndarray,
    batch_size: int = 64,
    val_split: float = 0.2,
    num_workers: int = 0,
    seed: int = 42,
) -> tuple[DataLoader, DataLoader]:
    """
    Creates stratified Train/Validation DataLoaders from raw arrays.
    Returns (train_loader, val_loader).
    """
    dataset = TabularDataset(X, y)
    n_total = len(dataset)
    n_val   = max(1, int(n_total * val_split))
    n_train = n_total - n_val

    generator = torch.Generator().manual_seed(seed)
    train_ds, val_ds = random_split(dataset, [n_train, n_val], generator=generator)

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
        drop_last=False,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
    )

    logger.info(
        "dataloaders_built",
        n_train=n_train, n_val=n_val, batch_size=batch_size
    )
    return train_loader, val_loader
