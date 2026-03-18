"""
anemia_combined_model.py
------------------------
Anemia prediction combining three feature groups:

  Group A — Checkup labs (8 features):
    Total cholesterol, HDL, LDL, triglycerides, fasting glucose, age, gender, BMI

  Group B — Questionnaire, high-relevance (7 available in dataset):
    dpq040  feeling tired / little energy
    huq010  general health condition (self-rated)
    cdq010  shortness of breath on stairs/inclines
    sld012  sleep hours weekdays
    sld013  sleep hours weekends
    slq050  ever told doctor had trouble sleeping
    pad680  minutes sedentary activity

    ⚠️  Requested but NOT in merged dataset (dropped by merge pipeline):
        dpq010 (little interest), dpq020 (depressed/hopeless),
        dpq030 (trouble sleeping — PHQ-9 item), dpq070 (trouble concentrating),
        dpq100 (functional difficulty)
        → Only dpq040 from the PHQ-9 block survived the merge.

  Group C — Female reproductive (3 features, NaN for males — imputed):
    rhq031  had regular periods in past 12 months
    rhq060  age at last menstrual period
    rhq540  ever use female hormones (HRT)

Total usable features: 18
Target: anemia (binary, 4.81% prevalence)
Architecture mirrors anemia_checkup_v2_model.py for fair comparison.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, classification_report,
    confusion_matrix,
)
from xgboost import XGBClassifier

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "nhanes_merged_adults_final.csv")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# ── Feature definitions ────────────────────────────────────────────────────────

# Raw column names as they appear in the merged CSV
RAW_FEATURE_COLS = [
    # Group A: Checkup labs
    "total_cholesterol_mg_dl",
    "hdl_cholesterol_mg_dl",
    "LBDLDL_ldl_cholesterol_friedewald_mg_dl",
    "triglycerides_mg_dl",
    "fasting_glucose_mg_dl",
    "age_years",
    "gender",                                           # encoded → gender_female
    "bmi",
    # Group B: Questionnaire
    "dpq040___feeling_tired_or_having_little_energy",
    "huq010___general_health_condition",
    "cdq010___shortness_of_breath_on_stairs/inclines",
    "sld012___sleep_hours___weekdays_or_workdays",
    "sld013___sleep_hours___weekends",
    "slq050___ever_told_doctor_had_trouble_sleeping?",
    "pad680___minutes_sedentary_activity",
    # Group C: Female reproductive (NaN for males — handled by median imputation)
    "rhq031___had_regular_periods_in_past_12_months",
    "rhq060___age_at_last_menstrual_period",
    "rhq540___ever_use_female_hormones?",
]

TARGET_COL = "anemia"

# Clean names used in X DataFrame and metadata
ENCODED_FEATURE_NAMES = [
    # Group A
    "total_cholesterol_mg_dl",
    "hdl_cholesterol_mg_dl",
    "ldl_cholesterol_mg_dl",
    "triglycerides_mg_dl",
    "fasting_glucose_mg_dl",
    "age_years",
    "gender_female",
    "bmi",
    # Group B
    "dpq040_tired_little_energy",
    "huq010_general_health",
    "cdq010_sob_stairs",
    "sld012_sleep_hours_weekday",
    "sld013_sleep_hours_weekend",
    "slq050_told_trouble_sleeping",
    "pad680_sedentary_minutes",
    # Group C
    "rhq031_regular_periods",
    "rhq060_age_last_period",
    "rhq540_ever_hormones",
]

# Features missing from dataset (requested but not in merged CSV)
MISSING_FROM_DATASET = [
    "dpq010___little_interest_in_doing_things",
    "dpq020___feeling_down,_depressed,_or_hopeless",
    "dpq030___trouble_falling_or_staying_asleep,_or_sleeping_too_much",
    "dpq070___trouble_concentrating_on_things",
    "dpq100___difficulty_these_problems_have_caused",
]


# ── Data loading & preparation ─────────────────────────────────────────────────

def load_data(path: str = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    print(f"Loaded dataset: {df.shape[0]} rows × {df.shape[1]} columns")
    return df


def prepare_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Extract and encode features for the combined anemia model.

    Encoding:
      - gender:  Female → 1.0, Male → 0.0, NaN preserved
      - slq050:  1 (yes) → 1.0, 2 (no) → 0.0, NaN preserved
      - rhq031:  1 (yes) → 1.0, 2 (no) → 0.0, NaN preserved (NaN for males)
      - rhq540:  1 (yes) → 1.0, 2 (no) → 0.0, NaN preserved (NaN for males)
      - All other columns: used as-is (numeric); NaN imputed in pipeline
    """
    missing_cols = [c for c in RAW_FEATURE_COLS + [TARGET_COL] if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Required columns not found in dataset: {missing_cols}")

    if MISSING_FROM_DATASET:
        print("⚠️  The following requested features are NOT in the merged dataset "
              "and are excluded:")
        for c in MISSING_FROM_DATASET:
            print(f"    {c}")
        print()

    subset = df[RAW_FEATURE_COLS + [TARGET_COL]].copy()

    # gender: Female=1, Male=0
    subset["gender"] = (subset["gender"] == "Female").astype(float)
    subset.loc[df["gender"].isna(), "gender"] = np.nan

    # Binary yes/no encodings: 1 (yes) → 1.0, 2 (no) → 0.0
    for col in [
        "slq050___ever_told_doctor_had_trouble_sleeping?",
        "rhq031___had_regular_periods_in_past_12_months",
        "rhq540___ever_use_female_hormones?",
    ]:
        was_missing = subset[col].isna()
        subset[col] = (subset[col] == 1).astype(float)
        subset.loc[was_missing, col] = np.nan

    subset.rename(columns=dict(zip(RAW_FEATURE_COLS, ENCODED_FEATURE_NAMES)), inplace=True)

    X = subset[ENCODED_FEATURE_NAMES]
    y = subset[TARGET_COL]

    print(f"Feature matrix: {X.shape}")
    print(f"Target distribution:\n{y.value_counts().to_string()}")
    print(f"\nMissing values (%):")
    print((X.isnull().mean() * 100).round(1).to_string())

    return X, y


def split_data(X: pd.DataFrame, y: pd.Series,
               test_size: float = 0.2,
               random_state: int = 42) -> tuple:
    """Stratified 80/20 split — same seed as v2 for fair comparison."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    print(f"\nTrain: {X_train.shape[0]} | Test: {X_test.shape[0]}")
    print(f"Train prevalence: {y_train.mean():.3f} | Test: {y_test.mean():.3f}")
    return X_train, X_test, y_train, y_test


# ── Pipelines ──────────────────────────────────────────────────────────────────

def build_lr_pipeline(random_state: int = 42) -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=random_state,
            C=1.0,
        )),
    ])


def build_xgb_pipeline(random_state: int = 42) -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("clf", XGBClassifier(
            n_estimators=300,
            max_depth=4,
            learning_rate=0.05,
            scale_pos_weight=19,
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=random_state,
            verbosity=0,
        )),
    ])


# ── Evaluation ─────────────────────────────────────────────────────────────────

def evaluate_model(model, X_test: pd.DataFrame, y_test: pd.Series,
                   threshold: float = 0.3,
                   model_name: str = "Model") -> dict:
    y_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_proba >= threshold).astype(int)

    metrics = {
        "model":     model_name,
        "threshold": threshold,
        "accuracy":  round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall":    round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1":        round(f1_score(y_test, y_pred, zero_division=0), 4),
        "roc_auc":   round(roc_auc_score(y_test, y_proba), 4),
    }

    print(f"\n{'='*50}")
    print(f"  {model_name} (threshold={threshold})")
    print(f"{'='*50}")
    for k, v in metrics.items():
        if k not in ("model", "threshold"):
            print(f"  {k:12s}: {v}")
    print(f"\n{classification_report(y_test, y_pred, zero_division=0)}")
    print(f"Confusion Matrix:\n{confusion_matrix(y_test, y_pred)}")

    return metrics


def cross_validate_model(model, X: pd.DataFrame, y: pd.Series,
                          scoring: str = "roc_auc") -> float:
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(model, X, y, cv=cv, scoring=scoring)
    print(f"  5-fold CV {scoring}: {scores.mean():.4f} ± {scores.std():.4f}")
    return scores.mean()


# ── Saving ─────────────────────────────────────────────────────────────────────

def save_model(model, model_name: str, metrics: dict,
               models_dir: str = MODELS_DIR) -> str:
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, f"{model_name}.joblib")
    meta_path  = os.path.join(models_dir, f"{model_name}_metadata.json")

    joblib.dump(model, model_path)

    metadata = {
        "model_name":    model_name,
        "version":       "combined",
        "feature_names": ENCODED_FEATURE_NAMES,
        "n_features":    len(ENCODED_FEATURE_NAMES),
        "target":        TARGET_COL,
        "feature_groups": {
            "checkup_labs":      ENCODED_FEATURE_NAMES[:8],
            "questionnaire":     ENCODED_FEATURE_NAMES[8:15],
            "female_reproductive": ENCODED_FEATURE_NAMES[15:],
        },
        "excluded_requested_features": MISSING_FROM_DATASET,
        "exclusion_reason": "Not present in nhanes_merged_adults_final.csv — "
                            "dropped during merge pipeline",
        "metrics":       metrics,
        "trained_at":    datetime.now().isoformat(),
    }
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Saved model    → {model_path}")
    print(f"Saved metadata → {meta_path}")
    return model_path


# ── Main entry point ───────────────────────────────────────────────────────────

def run_training_pipeline():
    print("=" * 60)
    print("  Anemia Combined Model — Training Pipeline")
    print("=" * 60)

    df = load_data()
    X, y = prepare_features(df)
    X_train, X_test, y_train, y_test = split_data(X, y)

    print("\n[1/2] Training Logistic Regression...")
    lr = build_lr_pipeline()
    lr.fit(X_train, y_train)
    lr_metrics = evaluate_model(lr, X_test, y_test, threshold=0.3,
                                 model_name="LR Combined")
    save_model(lr, "anemia_combined_lr", lr_metrics)

    print("\n[2/2] Training XGBoost...")
    xgb = build_xgb_pipeline()
    xgb.fit(X_train, y_train)
    xgb_metrics = evaluate_model(xgb, X_test, y_test, threshold=0.3,
                                  model_name="XGBoost Combined")
    save_model(xgb, "anemia_combined_xgb", xgb_metrics)

    print("\n" + "=" * 60)
    print(pd.DataFrame([lr_metrics, xgb_metrics]).to_string(index=False))

    return lr, xgb, lr_metrics, xgb_metrics


if __name__ == "__main__":
    run_training_pipeline()
