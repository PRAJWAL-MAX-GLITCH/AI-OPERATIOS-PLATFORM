"""
Dataset Seed Script
===================
Yeh script aapke real datasets ko project ke data/datasets/ folder mein copy karta hai
aur ek readable summary/profile generate karta hai.

Run karo:
    cd backend
    python scripts/seed_datasets.py
"""

import sys
import os
import shutil
import hashlib
import json
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

# ── Dataset Source Paths ────────────────────────────────────────────── #
DATASETS = [
    {
        "name":        "UCI Adult Income Dataset",
        "source":      Path(r"C:\Users\prajw\Downloads\adult\adult.data"),
        "description": "1994 US Census data. Predict if income > $50K/year. "
                       "32,561 instances, 15 features (age, education, occupation, etc.)",
        "type":        "raw",
        "format":      "csv",
        "column_names": [
            "age", "workclass", "fnlwgt", "education", "education_num",
            "marital_status", "occupation", "relationship", "race", "sex",
            "capital_gain", "capital_loss", "hours_per_week", "native_country", "income"
        ],
    },
    {
        "name":        "Telco Customer Churn Dataset",
        "source":      Path(r"C:\Users\prajw\Downloads\archive (1)\Telco_customer_churn.xlsx"),
        "description": "Telecom customer data to predict churn. "
                       "Contains demographics, account info, and services subscribed.",
        "type":        "raw",
        "format":      "xlsx",
        "column_names": None,   # Excel has its own headers
    },
]

STORAGE_ROOT = Path(__file__).parent.parent / "data" / "datasets"
STORAGE_ROOT.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def profile_adult(df: pd.DataFrame) -> dict:
    return {
        "total_rows":    len(df),
        "total_columns": len(df.columns),
        "missing_cells": int(df.isna().sum().sum()),
        "missing_pct":   round(df.isna().mean().mean() * 100, 2),
        "income_distribution": df["income"].value_counts().to_dict(),
        "age_stats": {
            "mean":  round(float(df["age"].mean()), 2),
            "min":   int(df["age"].min()),
            "max":   int(df["age"].max()),
        },
        "top_occupations": df["occupation"].value_counts().head(5).to_dict(),
        "top_education":   df["education"].value_counts().head(5).to_dict(),
    }


def profile_generic(df: pd.DataFrame) -> dict:
    return {
        "total_rows":    len(df),
        "total_columns": len(df.columns),
        "columns":       list(df.columns),
        "missing_cells": int(df.isna().sum().sum()),
        "missing_pct":   round(df.isna().mean().mean() * 100, 2),
        "dtypes":        {c: str(t) for c, t in df.dtypes.items()},
    }


def seed():
    print("")
    print("=" * 60)
    print("  Enterprise AI Platform - Dataset Seeder")
    print("=" * 60)

    for ds in DATASETS:
        src = ds["source"]
        if not src.exists():
            print(f"\n[SKIP] File not found: {src}")
            continue

        # Create destination folder
        dest_folder = STORAGE_ROOT / ds["format"] / src.stem
        dest_folder.mkdir(parents=True, exist_ok=True)
        dest_file = dest_folder / src.name

        # Copy file
        shutil.copy2(src, dest_file)
        checksum = sha256(dest_file)
        size_mb  = dest_file.stat().st_size / (1024 * 1024)

        print(f"\n[OK] {ds['name']}")
        print(f"    Source  : {src}")
        print(f"    Stored  : {dest_file}")
        print(f"    Size    : {size_mb:.2f} MB")
        print(f"    SHA-256 : {checksum[:32]}...")

        # Parse and profile
        try:
            if ds["format"] == "csv":
                df = pd.read_csv(
                    dest_file,
                    header=None,
                    names=ds["column_names"],
                    na_values=["?", "", " "],
                    skipinitialspace=True,
                )
                p = profile_adult(df)
            else:
                df = pd.read_excel(dest_file, engine="openpyxl")
                p = profile_generic(df)

            print(f"    Rows    : {p['total_rows']:,}")
            print(f"    Columns : {p['total_columns']}")
            print(f"    Missing : {p['missing_pct']}%")

            # Save profile JSON next to the data file
            profile_path = dest_folder / f"{src.stem}_profile.json"
            with open(profile_path, "w", encoding="utf-8") as pf:
                json.dump(p, pf, indent=2, default=str)
            print(f"    Profile : {profile_path}")

        except Exception as e:
            print(f"    [WARN] Profile generation failed: {e}")

    print("")
    print("=" * 60)
    print(f"  Datasets stored in:")
    print(f"  {STORAGE_ROOT.resolve()}")
    print("=" * 60)
    print("")


if __name__ == "__main__":
    seed()
