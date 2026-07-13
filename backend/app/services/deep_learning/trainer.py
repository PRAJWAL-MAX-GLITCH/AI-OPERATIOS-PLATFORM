"""
Enterprise Training Engine
===========================
Full epoch-level training loop with:
- Training & validation passes
- Gradient clipping & gradient accumulation
- Learning rate scheduling
- TensorBoard logging
- Epoch-by-epoch metric streaming
- Early stopping integration
"""
from __future__ import annotations
import time
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from typing import Optional, Any
import structlog

from app.services.deep_learning.checkpointing import EarlyStopping, CheckpointManager

logger = structlog.get_logger(__name__)


def _compute_accuracy(preds: torch.Tensor, targets: torch.Tensor, problem_type: str) -> float:
    """Compute accuracy for classification tasks."""
    if problem_type == "binary_classification":
        predicted = (torch.sigmoid(preds) >= 0.5).float()
        return (predicted == targets).float().mean().item()
    elif problem_type == "multiclass_classification":
        predicted = preds.argmax(dim=1)
        return (predicted == targets.long()).float().mean().item()
    return 0.0  # regression has no "accuracy"


def run_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: Optional[torch.optim.Optimizer],
    device: torch.device,
    problem_type: str,
    is_train: bool,
    grad_clip: float = 1.0,
    accum_steps: int = 1,
) -> dict[str, float]:
    """
    Runs one training or validation epoch.
    Returns dict with loss and accuracy.
    """
    model.train() if is_train else model.eval()

    total_loss = 0.0
    total_acc  = 0.0
    n_batches  = 0

    context = torch.enable_grad() if is_train else torch.no_grad()

    with context:
        for step, (X_batch, y_batch) in enumerate(loader):
            X_batch = X_batch.to(device, non_blocking=True)
            y_batch = y_batch.to(device, non_blocking=True)

            if problem_type == "multiclass_classification":
                y_batch = y_batch.long()

            logits = model(X_batch)
            loss   = criterion(logits, y_batch)

            if is_train:
                loss = loss / accum_steps
                loss.backward()
                if (step + 1) % accum_steps == 0:
                    nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
                    optimizer.step()
                    optimizer.zero_grad()

            total_loss += loss.item() * accum_steps  # undo scaling for logging
            total_acc  += _compute_accuracy(logits.detach(), y_batch, problem_type)
            n_batches  += 1

    return {
        "loss":     total_loss / max(n_batches, 1),
        "accuracy": total_acc  / max(n_batches, 1),
    }


def train_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: Any,
    device: torch.device,
    problem_type: str,
    total_epochs: int,
    checkpoint_dir: str,
    tensorboard_dir: str,
    patience: int = 10,
    grad_clip: float = 1.0,
    accum_steps: int = 1,
) -> dict[str, Any]:
    """
    Full training loop.
    Returns final metrics and epoch history.
    """
    model = model.to(device)

    early_stop = EarlyStopping(
        patience=patience,
        checkpoint_path=f"{checkpoint_dir}/best_model.pt"
    )
    ckpt_manager = CheckpointManager(checkpoint_dir)
    writer = SummaryWriter(log_dir=tensorboard_dir)

    history: dict[str, list] = {
        "train_loss": [], "val_loss": [],
        "train_acc":  [], "val_acc":  [],
        "lr":         [],
    }

    logger.info("dl_training_started", epochs=total_epochs, device=str(device))

    for epoch in range(1, total_epochs + 1):
        t0 = time.perf_counter()

        # --- Training pass ---
        train_metrics = run_epoch(
            model, train_loader, criterion, optimizer, device,
            problem_type, is_train=True,
            grad_clip=grad_clip, accum_steps=accum_steps
        )

        # --- Validation pass ---
        val_metrics = run_epoch(
            model, val_loader, criterion, None, device,
            problem_type, is_train=False
        )

        # --- LR step ---
        current_lr = optimizer.param_groups[0]["lr"]
        if scheduler is not None:
            if hasattr(scheduler, "step") and "plateau" in type(scheduler).__name__.lower():
                scheduler.step(val_metrics["loss"])
            else:
                scheduler.step()

        # --- Record history ---
        history["train_loss"].append(round(train_metrics["loss"], 6))
        history["val_loss"].append(round(val_metrics["loss"], 6))
        history["train_acc"].append(round(train_metrics["accuracy"], 4))
        history["val_acc"].append(round(val_metrics["accuracy"], 4))
        history["lr"].append(current_lr)

        # --- TensorBoard ---
        writer.add_scalar("Loss/train",      train_metrics["loss"],     epoch)
        writer.add_scalar("Loss/val",        val_metrics["loss"],       epoch)
        writer.add_scalar("Accuracy/train",  train_metrics["accuracy"], epoch)
        writer.add_scalar("Accuracy/val",    val_metrics["accuracy"],   epoch)
        writer.add_scalar("LR",              current_lr,                epoch)

        elapsed = time.perf_counter() - t0
        logger.info(
            "dl_epoch",
            epoch=epoch, total=total_epochs,
            train_loss=round(train_metrics["loss"], 4),
            val_loss=round(val_metrics["loss"], 4),
            val_acc=round(val_metrics["accuracy"], 4),
            lr=current_lr, elapsed_s=round(elapsed, 2)
        )

        # --- Checkpointing (latest) ---
        ckpt_manager.save(model, optimizer, epoch, {**train_metrics, **{f"val_{k}": v for k, v in val_metrics.items()}})

        # --- Early stopping (saves best checkpoint) ---
        if early_stop(val_metrics["loss"], model, epoch):
            logger.info("dl_training_early_stopped", epoch=epoch)
            break

    writer.close()

    # --- Load best weights ---
    early_stop.load_best(model)

    final_metrics = {
        "best_val_loss":  early_stop.best_loss,
        "best_epoch":     early_stop.best_epoch,
        "final_train_loss": history["train_loss"][-1],
        "final_val_loss":   history["val_loss"][-1],
        "final_val_acc":    history["val_acc"][-1],
    }

    logger.info("dl_training_completed", **final_metrics)

    return {
        "final_metrics":  final_metrics,
        "metrics_history": history,
        "best_model_path": str(early_stop.checkpoint_path),
    }
