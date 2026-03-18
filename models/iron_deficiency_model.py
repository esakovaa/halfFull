"""
iron_deficiency_model.py
------------------------
Iron deficiency prediction using NHANES data.
Architecture mirrors anemia_combined_model.py for cross-condition comparison.

Target: iron_deficiency (binary, 6.05% prevalence, 15.5:1 class imbalance)

Feature selection: point-biserial correlation vs target (|r| > 0.05, p < 0.05)
14 features selected across 3 groups:

  Group A — Iron-specific labs (6 features):
    ⚠️  LEAKAGE RISK: these biomarkers likely define the target label.
    They are included for modelling completeness but should NOT be used
    in a checkup-only deployment where the label is unknown.
    ferritin_ng_ml                   r=-0.22  (13.2% missing)
    serum_iron_ug_dl                 r=-0.30  (13.9% missing)
    tibc_ug_dl                       r=+0.44  (14.4% missing)
    transferrin_saturation_pct       r=-0.36  (14.4% missing)
    LBXUIB_uibc_serum_ug_dl (UIBC)  r=+0.51  (14.3% missing)
    transferrin_receptor_mg_l        r=+0.52  (71.6% missing — high missingness)

  Group B — Checkup labs (6 features, safe from leakage):
    hdl_cholesterol_mg_dl            r=+0.07
    fasting_glucose_mg_dl            r=-0.08  (57% missing — fasting subsample)
    age_years                        r=-0.10
    gender                           r=+0.20  (Female at higher risk)
    triglycerides_mg_dl              r=-0.05  (57% missing — fasting subsample)
    LBDLDL_ldl_cholesterol_friedewald_mg_dl  r=-0.05  (58% missing)

  Group C — Female reproductive (2 features, NaN for males):
    rhq031  regular periods past 12 months  r=-0.22  (menstrual blood loss)
    rhq060  age at last menstrual period    r=+0.07

  Questionnaire features all dropped (|r| < 0.05 or p > 0.05):
    Iron deficiency is often subclinical — fatigue/dyspnoea signals
    from dpq040, cdq010, huq010 etc. did not carry significant signal.

Total features: 14
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
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "nhanes_merged_adults_final.csv")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# ── Feature definitions ────────────────────────────────────────────────────────

RAW_FEATURE_COLS = [
    # Group A: Iron-specific labs (leakage-risk — see docstring)
    "ferritin_ng_ml",
    "serum_iron_ug_dl",
    "tibc_ug_dl",
    "transferrin_saturation_pct",
    "LBXUIB_uibc_serum_ug_dl",
    "transferrin_receptor_mg_l",
    # Group B: Checkup labs (safe)
    "hdl_cholesterol_mg_dl",
    "fasting_glucose_mg_dl",
    "age_years",
    "gender",                                    # encoded → gender_female
    "triglycerides_mg_dl",
    "LBDLDL_ldl_cholesterol_friedewald_mg_dl",
    # Group C: Female reproductive (NaN for males — median-imputed)
    "rhq031___had_regular_periods_in_past_12_months",
    "rhq060___age_at_last_menstrual_period",
]

TARGET_COL = "iron_deficiency"

ENCODED_FEATURE_NAMES = [
    # Group A
    "ferritin_ng_ml",
    "serum_iron_ug_dl",
    "tibc_ug_dl",
    "transferrin_saturation_pct",
    "uibc_serum_ug_dl",
    "transferrin_receptor_mg_l",
    # Group B
    "hdl_cholesterol_mg_dl",
    "fasting_glucose_mg_dl",
    "age_years",
    "gender_female",
    "triglycerides_mg_dl",
    "ldl_cholesterol_mg_dl",
    # Group C
    "rhq031_regular_periods",
    "rhq060_age_last_period",
]

FEATURE_GROUPS = {
    "iron_specific_labs":  ENCODED_FEATURE_NAMES[:6],
    "checkup_labs":        ENCODED_FEATURE_NAMES[6:12],
    "female_reproductive": ENCODED_FEATURE_NAMES[12:],
}

# Questionnaire features dropped (all |r| < 0.05 vs iron_deficiency target)
DROPPED_FEATURES = {
    "dpq040___feeling_tired_or_having_little_energy": "r=0.023, p=0.067 — not significant",
    "huq010___general_health_condition":              "r=-0.004, p=0.718 — not significant",
    "cdq010___shortness_of_breath_on_stairs/inclines":"r=-0.015, p=0.334 — not significant",
    "sld012___sleep_hours___weekdays_or_workdays":    "r=0.020, p=0.087 — not significant",
    "sld013___sleep_hours___weekends":                "r=0.023, p=0.049 — |r|<0.05",
    "slq050___ever_told_doctor_had_trouble_sleeping?":"r=0.030, p=0.010 — |r|<0.05",
    "pad680___minutes_sedentary_activity":            "r=-0.017, p=0.139 — not significant",
    "total_cholesterol_mg_dl":                       "r=-0.046, p=0.000 — |r|<0.05",
    "bmi":                                            "r=-0.003, p=0.836 — not significant",
    "rhq540___ever_use_female_hormones?":             "r=0.035, p=0.050 — |r|<0.05",
}


# ── Data loading & preparation ─────────────────────────────────────────────────

def load_data(path: str = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    print(f"Loaded dataset: {df.shape[0]} rows × {df.shape[1]} columns")
    return df


def prepare_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Extract and encode features for the iron deficiency model.

    Encoding:
      - gender:  Female → 1.0, Male → 0.0
      - rhq031:  1 (yes) → 1.0, 2 (no) → 0.0, NaN preserved (NaN for males)
      - All other columns: numeric as-is; NaN imputed inside pipeline
    """
    missing_cols = [c for c in RAW_FEATURE_COLS + [TARGET_COL] if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Required columns not found in dataset: {missing_cols}")

    subset = df[RAW_FEATURE_COLS + [TARGET_COL]].copy()

    # gender encoding
    subset["gender"] = (subset["gender"] == "Female").astype(float)
    subset.loc[df["gender"].isna(), "gender"] = np.nan

    # Binary yes/no: 1=yes → 1.0, 2=no → 0.0, NaN preserved
    col = "rhq031___had_regular_periods_in_past_12_months"
    was_missing = subset[col].isna()
    subset[col] = (subset[col] == 1).astype(float)
    subset.loc[was_missing, col] = np.nan

    subset.rename(columns=dict(zip(RAW_FEATURE_COLS, ENCODED_FEATURE_NAMES)), inplace=True)

    X = subset[ENCODED_FEATURE_NAMES]
    y = subset[TARGET_COL]

    print(f"Feature matrix: {X.shape}")
    print(f"Target distribution:\n{y.value_counts().to_string()}")
    print(f"Prevalence: {y.mean():.3f} ({y.sum()} positive)")
    print(f"\nMissing values (%):")
    print((X.isnull().mean() * 100).round(1).to_string())

    return X, y


def split_data(X: pd.DataFrame, y: pd.Series,
               test_size: float = 0.2,
               random_state: int = 42) -> tuple:
    """Stratified 80/20 split — same seed as anemia model for cross-condition fairness."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    print(f"\nTrain: {X_train.shape[0]} | Test: {X_test.shape[0]}")
    print(f"Train prevalence: {y_train.mean():.4f} | Test: {y_test.mean():.4f}")
    return X_train, X_test, y_train, y_test


# ── Pipelines ──────────────────────────────────────────────────────────────────

def build_lr_pipeline(random_state: int = 42) -> Pipeline:
    """Logistic Regression with class balancing — prioritises recall for screening."""
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
    """XGBoost with scale_pos_weight=15 (6987/450) for class imbalance."""
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("clf", XGBClassifier(
            n_estimators=300,
            max_depth=4,
            learning_rate=0.05,
            scale_pos_weight=15,       # 6987 / 450 ≈ 15.5
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
    """Evaluate with adjustable threshold — default 0.3 prioritises recall."""
    y_proba = model.predict_proba(X_test)[:, 1]
    y_pred  = (y_proba >= threshold).astype(int)

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
        "model_name":     model_name,
        "target":         TARGET_COL,
        "prevalence":     "6.05% (450/7437)",
        "class_imbalance":"15.5:1",
        "feature_names":  ENCODED_FEATURE_NAMES,
        "n_features":     len(ENCODED_FEATURE_NAMES),
        "feature_groups": FEATURE_GROUPS,
        "dropped_features": DROPPED_FEATURES,
        "leakage_warning": (
            "Group A (iron-specific labs) may be derived from the target label definition. "
            "Use Group B + C only for checkup-constrained deployment."
        ),
        "metrics":        metrics,
        "trained_at":     datetime.now().isoformat(),
    }
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Saved model    → {model_path}")
    print(f"Saved metadata → {meta_path}")
    return model_path


# ── Main entry point ───────────────────────────────────────────────────────────

def run_training_pipeline():
    print("=" * 60)
    print("  Iron Deficiency Model — Training Pipeline")
    print("=" * 60)

    df = load_data()
    X, y = prepare_features(df)
    X_train, X_test, y_train, y_test = split_data(X, y)

    print("\n[1/2] Training Logistic Regression...")
    lr = build_lr_pipeline()
    lr.fit(X_train, y_train)
    lr_metrics = evaluate_model(lr, X_test, y_test, threshold=0.3,
                                model_name="LR Iron Deficiency")
    save_model(lr, "iron_deficiency_lr", lr_metrics)

    print("\n[2/2] Training XGBoost...")
    xgb = build_xgb_pipeline()
    xgb.fit(X_train, y_train)
    xgb_metrics = evaluate_model(xgb, X_test, y_test, threshold=0.3,
                                 model_name="XGBoost Iron Deficiency")
    save_model(xgb, "iron_deficiency_xgb", xgb_metrics)

    print("\n" + "=" * 60)
    print(pd.DataFrame([lr_metrics, xgb_metrics]).to_string(index=False))

    return lr, xgb, lr_metrics, xgb_metrics


if __name__ == "__main__":
    run_training_pipeline()
