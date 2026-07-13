"""
Early Stopping & Checkpointing
===============================
Saves the best model checkpoint and halts training when validation loss stagnates.
"""
from __future__ import annotations
import json
import torch
import torch.nn as nn
from pathlib import Path
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)


class EarlyStopping:
    """
    Stops training when val_loss doesn't improve for `patience` epochs.
    Automatically saves the best model checkpoint.
    """

    def __init__(self, patience: int = 10, min_delta: float = 1e-4, checkpoint_path: str = "best_model.pt"):
        self.patience         = patience
        self.min_delta        = min_delta
        self.checkpoint_path  = Path(checkpoint_path)
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

        self.best_loss    : Optional[float] = None
        self.best_epoch   : int             = 0
        self.counter      : int             = 0
        self.should_stop  : bool            = False

    def __call__(self, val_loss: float, model: nn.Module, epoch: int) -> bool:
        """
        Returns True if training should stop.
        Saves model if val_loss improved.
        """
        if self.best_loss is None or val_loss < self.best_loss - self.min_delta:
            self.best_loss  = val_loss
            self.best_epoch = epoch
            self.counter    = 0
            torch.save(model.state_dict(), self.checkpoint_path)
            logger.info("checkpoint_saved", path=str(self.checkpoint_path), epoch=epoch, val_loss=round(val_loss, 6))
        else:
            self.counter += 1
            logger.debug("early_stopping_counter", counter=self.counter, patience=self.patience)
            if self.counter >= self.patience:
                self.should_stop = True
                logger.info("early_stopping_triggered", epoch=epoch, best_epoch=self.best_epoch)
        return self.should_stop

    def load_best(self, model: nn.Module) -> nn.Module:
        """Loads the best checkpoint into the model."""
        model.load_state_dict(torch.load(self.checkpoint_path, weights_only=True))
        return model


class CheckpointManager:
    """
    Saves both the latest and best model checkpoints with full metadata.
    Supports training resumption.
    """

    def __init__(self, checkpoint_dir: str):
        self.dir = Path(checkpoint_dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        model: nn.Module,
        optimizer: torch.optim.Optimizer,
        epoch: int,
        metrics: dict,
        tag: str = "latest"
    ) -> str:
        """Save a checkpoint with optimizer state and metadata."""
        ckpt = {
            "epoch":            epoch,
            "model_state_dict": model.state_dict(),
            "optim_state_dict": optimizer.state_dict(),
            "metrics":          metrics,
        }
        path = self.dir / f"checkpoint_{tag}.pt"
        torch.save(ckpt, path)

        # Save human-readable metadata alongside
        meta_path = self.dir / f"checkpoint_{tag}_meta.json"
        meta = {"epoch": epoch, "metrics": metrics}
        meta_path.write_text(json.dumps(meta, indent=2))

        logger.info("checkpoint_manager_saved", tag=tag, path=str(path), epoch=epoch)
        return str(path)

    def load(self, model: nn.Module, optimizer: torch.optim.Optimizer, tag: str = "latest") -> int:
        """Resume from a saved checkpoint. Returns the next epoch number."""
        path = self.dir / f"checkpoint_{tag}.pt"
        if not path.exists():
            return 0
        ckpt = torch.load(path, weights_only=False)
        model.load_state_dict(ckpt["model_state_dict"])
        optimizer.load_state_dict(ckpt["optim_state_dict"])
        logger.info("checkpoint_loaded", tag=tag, epoch=ckpt["epoch"])
        return ckpt["epoch"] + 1
