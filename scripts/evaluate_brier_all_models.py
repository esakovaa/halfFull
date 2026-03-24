"""
Compute Brier scores for all finalized normalized models.

Outputs:
  - evaluation/brier_scores_models_normalized.csv
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss
from sklearn.model_selection import train_test_split


SEED = 42
ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "nhanes_merged_adults_final_normalized.csv"
MODELS_DIR = ROOT / "models_normalized"
OUT_PATH = ROOT / "evaluation" / "brier_scores_models_normalized.csv"

EDU_ORDER = {
    "Less than 9th grade": 0,
    "9-11th grade": 1,
    "High school / GED": 2,
    "Some college / AA": 3,
    "College graduate or above": 4,
}


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    derived = {}

    if "gender" in df.columns:
        derived["gender_female"] = (df["gender"] == "Female").astype(float)
    else:
        derived["gender_female"] = pd.Series(np.nan, index=df.index)

    if "education" in df.columns:
        derived["education_ord"] = df["education"].map(EDU_ORDER)
    else:
        derived["education_ord"] = pd.Series(np.nan, index=df.index)

    if "pregnancy_status" in df.columns:
        preg = (df["pregnancy_status"] == "Yes, pregnant").astype(float)
        preg = preg.mask(df["pregnancy_status"].isna(), np.nan)
        derived["pregnancy_status_bin"] = preg
    else:
        derived["pregnancy_status_bin"] = pd.Series(np.nan, index=df.index)

    return pd.concat([df, pd.DataFrame(derived, index=df.index)], axis=1)


def evaluate_model(df: pd.DataFrame, meta_path: Path) -> dict:
    with open(meta_path) as f:
        meta = json.load(f)

    model_name = meta["model"]
    condition = meta["condition"]
    features = meta["features"]
    model = joblib.load(MODELS_DIR / model_name)

    subset = df[features + [condition]].copy().dropna(subset=[condition])
    X = subset[features]
    y = subset[condition].astype(int)

    _, X_test, _, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        stratify=y,
        random_state=SEED,
    )
    y_prob = model.predict_proba(X_test)[:, 1]

    return {
        "model": model_name,
        "condition": condition,
        "n_test": len(y_test),
        "prevalence": round(float(y_test.mean()), 5),
        "mean_pred": round(float(y_prob.mean()), 5),
        "brier_score": round(float(brier_score_loss(y_test, y_prob)), 5),
    }


def main() -> None:
    df = pd.read_csv(DATA_PATH, low_memory=False)
    df = add_derived_columns(df)

    rows = []
    for meta_path in sorted(MODELS_DIR.glob("*_metadata.json")):
        rows.append(evaluate_model(df, meta_path))

    results = pd.DataFrame(rows).sort_values(["brier_score", "model"]).reset_index(drop=True)
    OUT_PATH.parent.mkdir(exist_ok=True)
    results.to_csv(OUT_PATH, index=False)

    print(results.to_string(index=False))
    print(f"\nSaved -> {OUT_PATH}")


if __name__ == "__main__":
    main()
