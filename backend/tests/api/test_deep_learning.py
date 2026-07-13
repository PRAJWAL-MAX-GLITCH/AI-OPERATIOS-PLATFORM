"""
Deep Learning Tests
====================
Tests for device config, model factory, training engine, checkpointing, and inference.
"""
import pytest
import uuid
import numpy as np
import torch
import tempfile
import os

from app.services.deep_learning.config import get_device, set_seed, get_device_info
from app.services.deep_learning.dataset import TabularDataset, build_dataloaders
from app.services.deep_learning.models import (
    DLModelFactory, BinaryClassificationNet, MultiClassNet, RegressionNet
)
from app.services.deep_learning.losses import get_loss_function, get_optimizer, get_scheduler
from app.services.deep_learning.checkpointing import EarlyStopping, CheckpointManager
from app.services.deep_learning.trainer import run_epoch, train_model
from app.services.deep_learning.inference import DLInferenceEngine


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def sample_binary_data():
    np.random.seed(42)
    X = np.random.randn(200, 10).astype(np.float32)
    y = (X[:, 0] > 0).astype(np.float32)
    return X, y


@pytest.fixture
def sample_multiclass_data():
    np.random.seed(42)
    X = np.random.randn(300, 8).astype(np.float32)
    y = np.random.randint(0, 3, size=300).astype(np.float32)
    return X, y


@pytest.fixture
def sample_regression_data():
    np.random.seed(42)
    X = np.random.randn(200, 5).astype(np.float32)
    y = (X[:, 0] * 2 + np.random.randn(200) * 0.1).astype(np.float32)
    return X, y


# ===========================================================================
# Step 2: Device & Config
# ===========================================================================

def test_get_device():
    device = get_device()
    assert isinstance(device, torch.device)
    assert device.type in ("cuda", "mps", "cpu")


def test_set_seed():
    set_seed(42)
    val1 = torch.randn(5)
    set_seed(42)
    val2 = torch.randn(5)
    assert torch.allclose(val1, val2), "Seed should produce reproducible tensors"


def test_device_info():
    info = get_device_info()
    assert "cuda_available" in info
    assert "selected_device" in info
    assert "mps_available" in info


# ===========================================================================
# Step 3-4: Dataset & DataLoader
# ===========================================================================

def test_tabular_dataset(sample_binary_data):
    X, y = sample_binary_data
    ds = TabularDataset(X, y)
    assert len(ds) == 200
    x_item, y_item = ds[0]
    assert x_item.shape == (10,)
    assert y_item.dtype == torch.float32


def test_build_dataloaders(sample_binary_data):
    X, y = sample_binary_data
    train_loader, val_loader = build_dataloaders(X, y, batch_size=32, val_split=0.2)
    assert len(train_loader) > 0
    assert len(val_loader) > 0
    # Check that train+val = total samples
    total_batches = sum(1 for _ in train_loader) + sum(1 for _ in val_loader)
    assert total_batches > 0


# ===========================================================================
# Step 5-6: Models & Factory
# ===========================================================================

def test_binary_classification_net():
    model = BinaryClassificationNet(input_dim=10, hidden_dims=[64, 32])
    x = torch.randn(8, 10)
    out = model(x)
    assert out.shape == (8,), "Binary output should be (batch,) logits"


def test_multiclass_net():
    model = MultiClassNet(input_dim=8, num_classes=3, hidden_dims=[64, 32])
    x = torch.randn(8, 8)
    out = model(x)
    assert out.shape == (8, 3), "Multiclass output should be (batch, num_classes)"


def test_regression_net():
    model = RegressionNet(input_dim=5, hidden_dims=[32, 16])
    x = torch.randn(8, 5)
    out = model(x)
    assert out.shape == (8,), "Regression output should be (batch,)"


def test_model_factory_binary():
    model = DLModelFactory.create("binary_classification", 10, {"hidden_dims": [64, 32], "dropout": 0.1})
    assert isinstance(model, BinaryClassificationNet)


def test_model_factory_multiclass():
    model = DLModelFactory.create("multiclass_classification", 8, {"hidden_dims": [64], "dropout": 0.1, "num_classes": 3})
    assert isinstance(model, MultiClassNet)


def test_model_factory_regression():
    model = DLModelFactory.create("regression", 5, {"hidden_dims": [32], "dropout": 0.1})
    assert isinstance(model, RegressionNet)


def test_model_factory_unknown():
    with pytest.raises(ValueError, match="Unknown problem_type"):
        DLModelFactory.create("unknown_type", 5, {})


# ===========================================================================
# Step 8-9: Optimizers & Loss Functions
# ===========================================================================

def test_loss_binary():
    model = BinaryClassificationNet(10, [32])
    loss_fn = get_loss_function("binary_classification", {})
    assert isinstance(loss_fn, torch.nn.BCEWithLogitsLoss)


def test_loss_multiclass():
    loss_fn = get_loss_function("multiclass_classification", {})
    assert isinstance(loss_fn, torch.nn.CrossEntropyLoss)


def test_loss_regression():
    loss_fn = get_loss_function("regression", {})
    assert isinstance(loss_fn, torch.nn.MSELoss)


def test_optimizer_adamw():
    model = RegressionNet(5, [32])
    opt = get_optimizer(model, {"optimizer": "adamw", "learning_rate": 1e-3, "weight_decay": 1e-4})
    assert isinstance(opt, torch.optim.AdamW)


def test_optimizer_sgd():
    model = RegressionNet(5, [32])
    opt = get_optimizer(model, {"optimizer": "sgd", "learning_rate": 0.01, "weight_decay": 0.0})
    assert isinstance(opt, torch.optim.SGD)


def test_scheduler_cosine():
    model = RegressionNet(5, [32])
    opt   = get_optimizer(model, {"optimizer": "adam", "learning_rate": 1e-3, "weight_decay": 0})
    sched = get_scheduler(opt, {"scheduler": "cosine"}, total_epochs=20)
    assert sched is not None


# ===========================================================================
# Step 10-11: Checkpointing & Early Stopping
# ===========================================================================

def test_early_stopping_saves_best(tmp_path):
    model = RegressionNet(5, [32])
    ckpt_path = str(tmp_path / "best.pt")
    es = EarlyStopping(patience=3, checkpoint_path=ckpt_path)

    # Improving loss → should save
    assert not es(1.0, model, 1)
    assert not es(0.8, model, 2)  # Better → counter reset
    assert not es(0.9, model, 3)  # Worse  → counter=1
    assert not es(1.0, model, 4)  # Worse  → counter=2
    assert es(1.1, model, 5)      # Worse  → counter=3 → STOP

    assert os.path.exists(ckpt_path)
    assert es.best_loss == pytest.approx(0.8, abs=1e-5)


def test_early_stopping_load_best(tmp_path):
    model = RegressionNet(5, [32])
    ckpt_path = str(tmp_path / "best.pt")
    es = EarlyStopping(patience=3, checkpoint_path=ckpt_path)
    es(0.5, model, 1)  # Saves best
    loaded = es.load_best(RegressionNet(5, [32]))
    assert loaded is not None


def test_checkpoint_manager(tmp_path):
    model = RegressionNet(5, [32])
    opt   = torch.optim.Adam(model.parameters(), lr=1e-3)
    mgr   = CheckpointManager(str(tmp_path))

    path = mgr.save(model, opt, epoch=5, metrics={"val_loss": 0.3})
    assert os.path.exists(path)

    new_model = RegressionNet(5, [32])
    start_ep  = mgr.load(new_model, opt)
    assert start_ep == 6  # resumes from next epoch


# ===========================================================================
# Step 7: Training Engine (Mini integration test)
# ===========================================================================

def test_run_epoch_binary(sample_binary_data, tmp_path):
    X, y = sample_binary_data
    train_loader, _ = build_dataloaders(X, y, batch_size=32, val_split=0.2)
    model     = BinaryClassificationNet(10, [32, 16], dropout=0.0)
    criterion = torch.nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    device    = torch.device("cpu")

    metrics = run_epoch(model, train_loader, criterion, optimizer, device, "binary_classification", is_train=True)
    assert "loss" in metrics
    assert "accuracy" in metrics
    assert 0.0 <= metrics["accuracy"] <= 1.0


def test_full_training_binary(sample_binary_data, tmp_path):
    X, y = sample_binary_data
    train_loader, val_loader = build_dataloaders(X, y, batch_size=32, val_split=0.2)
    model     = BinaryClassificationNet(10, [32], dropout=0.0)
    criterion = torch.nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    device    = torch.device("cpu")

    result = train_model(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        criterion=criterion,
        optimizer=optimizer,
        scheduler=None,
        device=device,
        problem_type="binary_classification",
        total_epochs=3,
        checkpoint_dir=str(tmp_path / "ckpts"),
        tensorboard_dir=str(tmp_path / "tb"),
        patience=5,
    )

    assert "final_metrics" in result
    assert "best_val_loss" in result["final_metrics"]
    assert os.path.exists(result["best_model_path"])
    assert "train_loss" in result["metrics_history"]
    assert len(result["metrics_history"]["train_loss"]) == 3


# ===========================================================================
# Step 14: Inference Engine
# ===========================================================================

def test_inference_binary(tmp_path):
    X = np.random.randn(10, 10).astype(np.float32)
    y = (X[:, 0] > 0).astype(np.float32)
    train_loader, val_loader = build_dataloaders(X, y, batch_size=10, val_split=0.2)
    model     = BinaryClassificationNet(10, [32], dropout=0.0)
    criterion = torch.nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters())
    device    = torch.device("cpu")

    result = train_model(
        model=model, train_loader=train_loader, val_loader=val_loader,
        criterion=criterion, optimizer=optimizer, scheduler=None,
        device=device, problem_type="binary_classification",
        total_epochs=2,
        checkpoint_dir=str(tmp_path / "ckpts"),
        tensorboard_dir=str(tmp_path / "tb"),
        patience=5,
    )

    # Load best and infer
    loaded_model, loaded_device = DLInferenceEngine.load_model_from_checkpoint(
        checkpoint_path=result["best_model_path"],
        problem_type="binary_classification",
        input_dim=10,
        model_config={"hidden_dims": [32], "dropout": 0.0},
    )

    preds = DLInferenceEngine.predict(
        loaded_model, loaded_device,
        np.random.randn(3, 10).astype(np.float32),
        "binary_classification"
    )
    assert "predictions" in preds
    assert "confidence" in preds
    assert len(preds["predictions"]) == 3
    assert all(p in [0, 1] for p in preds["predictions"])
