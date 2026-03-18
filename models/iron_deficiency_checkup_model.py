"""
iron_deficiency_checkup_model.py
---------------------------------
Iron deficiency prediction — checkup-constrained deployment version.

Group A iron-specific labs (ferritin, serum iron, TIBC, transferrin saturation,
UIBC, transferrin receptor) are EXCLUDED BY DESIGN: in a real screening scenario
those biomarkers are unknown — ordering them is precisely the decision the tool
is trying to support.

Starting feature pool: same as anemia_combined_model.py (checkup labs +
questionnaire + female reproductive).

Feature selection: point-biserial r vs iron_deficiency (|r| < 0.03 AND p > 0.05
→ dropped):

  Checkup labs (7 kept, 1 dropped):
    total_cholesterol_mg_dl                  r=-0.046  p<0.001  KEPT
    hdl_cholesterol_mg_dl                    r=+0.073  p<0.001  KEPT
    LBDLDL_ldl_cholesterol_friedewald_mg_dl  r=-0.053  p<0.001  KEPT
    triglycerides_mg_dl                      r=-0.054  p<0.001  KEPT
    fasting_glucose_mg_dl                    r=-0.078  p<0.001  KEPT (57% missing)
    age_years                                r=-0.099  p<0.001  KEPT
    gender (female=1)                        r=+0.198  p<0.001  KEPT
    bmi                                      r=-0.003  p=0.836  DROPPED (|r|<0.03 & p>0.05)

  Questionnaire (2 kept, 5 dropped):
    sld013  sleep hours weekends             r=+0.023  p=0.049  KEPT (p<0.05)
    slq050  ever told doctor trouble sleeping r=+0.030  p=0.010  KEPT (|r|≥0.03)
    dpq040  feeling tired / little energy    r=+0.023  p=0.067  DROPPED
    huq010  general health condition         r=-0.004  p=0.718  DROPPED
    cdq010  shortness of breath on stairs    r=-0.015  p=0.334  DROPPED
    sld012  sleep hours weekdays             r=+0.020  p=0.087  DROPPED
    pad680  minutes sedentary activity       r=-0.017  p=0.139  DROPPED

  Female reproductive (3 kept):
    rhq031  regular periods past 12 months   r=-0.220  p<0.001  KEPT
    rhq060  age at last menstrual period      r=+0.073  p<0.001  KEPT
    rhq540  ever use female hormones          r=+0.035  p=0.050  KEPT (|r|≥0.03)

Total features: 12
Target: iron_deficiency (binary, 6.05% prevalence, 15.5:1 class imbalance)

Architecture mirrors iron_deficiency_model.py for direct comparison.
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
    # Checkup labs (Group B — safe, no leakage)
    "total_cholesterol_mg_dl",
    "hdl_cholesterol_mg_dl",
    "LBDLDL_ldl_cholesterol_friedewald_mg_dl",
    "triglycerides_mg_dl",
    "fasting_glucose_mg_dl",
    "age_years",
    "gender",                                            # encoded → gender_female
    # Questionnaire (marginal signal — kept by threshold rules)
    "sld013___sleep_hours___weekends",
    "slq050___ever_told_doctor_had_trouble_sleeping?",
    # Female reproductive (Group C — safe)
    "rhq031___had_regular_periods_in_past_12_months",
    "rhq060___age_at_last_menstrual_period",
    "rhq540___ever_use_female_hormones?",
]

TARGET_COL = "iron_deficiency"

ENCODED_FEATURE_NAMES = [
    # Checkup labs
    "total_cholesterol_mg_dl",
    "hdl_cholesterol_mg_dl",
    "ldl_cholesterol_mg_dl",
    "triglycerides_mg_dl",
    "fasting_glucose_mg_dl",
    "age_years",
    "gender_female",
    # Questionnaire
    "sld013_sleep_hours_weekend",
    "slq050_told_trouble_sleeping",
    # Female reproductive
    "rhq031_regular_periods",
    "rhq060_age_last_period",
    "rhq540_ever_hormones",
]

FEATURE_GROUPS = {
    "checkup_labs":        ENCODED_FEATURE_NAMES[:7],
    "questionnaire":       ENCODED_FEATURE_NAMES[7:9],
    "female_reproductive": ENCODED_FEATURE_NAMES[9:],
}

# Features excluded from the full iron_deficiency_model.py — by design (leakage)
EXCLUDED_IRON_SPECIFIC = [
    "ferritin_ng_ml",
    "serum_iron_ug_dl",
    "tibc_ug_dl",
    "transferrin_saturation_pct",
    "LBXUIB_uibc_serum_ug_dl",
    "transferrin_receptor_mg_l",
]

# Features dropped by correlation threshold (|r| < 0.03 AND p > 0.05)
DROPPED_BY_THRESHOLD = {
    "bmi":                                           "r=-0.003, p=0.836",
    "dpq040___feeling_tired_or_having_little_energy":"r=+0.023, p=0.067",
    "huq010___general_health_condition":             "r=-0.004, p=0.718",
    "cdq010___shortness_of_breath_on_stairs/inclines":"r=-0.015, p=0.334",
    "sld012___sleep_hours___weekdays_or_workdays":   "r=+0.020, p=0.087",
    "pad680___minutes_sedentary_activity":           "r=-0.017, p=0.139",
}


# ── Data loading & preparation ─────────────────────────────────────────────────

def load_data(path: str = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    print(f"Loaded dataset: {df.shape[0]} rows × {df.shape[1]} columns")
    return df


def prepare_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Extract and encode features for the checkup-constrained iron deficiency model.

    Encoding:
      - gender:  Female → 1.0, Male → 0.0, NaN preserved
      - slq050:  1 (yes) → 1.0, 2 (no) → 0.0, NaN preserved
      - rhq031:  1 (yes) → 1.0, 2 (no) → 0.0, NaN preserved (NaN for males)
      - rhq540:  1 (yes) → 1.0, 2 (no) → 0.0, NaN preserved (NaN for males)
      - All other columns: numeric as-is; NaN imputed inside pipeline
    """
    missing_cols = [c for c in RAW_FEATURE_COLS + [TARGET_COL] if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Required columns not found in dataset: {missing_cols}")

    subset = df[RAW_FEATURE_COLS + [TARGET_COL]].copy()

    # gender: Female=1, Male=0
    subset["gender"] = (subset["gender"] == "Female").astype(float)
    subset.loc[df["gender"].isna(), "gender"] = np.nan

    # Binary yes/no: 1 (yes) → 1.0, 2 (no) → 0.0, NaN preserved
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
    print(f"Prevalence: {y.mean():.3f} ({y.sum():.0f} positive)")
    print(f"\nMissing values (%):")
    print((X.isnull().mean() * 100).round(1).to_string())

    return X, y


def split_data(X: pd.DataFrame, y: pd.Series,
               test_size: float = 0.2,
               random_state: int = 42) -> tuple:
    """Stratified 80/20 split — same seed as iron_deficiency_model for direct comparison."""
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
        ("scaler",  StandardScaler()),
        ("clf",     LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=random_state,
            C=1.0,
        )),
    ])


def build_xgb_pipeline(random_state: int = 42) -> Pipeline:
    """XGBoost with scale_pos_weight=15 (6987/450 ≈ 15.5) for class imbalance."""
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("clf",     XGBClassifier(
            n_estimators=300,
            max_depth=4,
            learning_rate=0.05,
            scale_pos_weight=15,
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
        "deployment_note": (
            "Checkup-constrained version — iron-specific labs (Group A) excluded by design. "
            "Safe to use in screening scenarios where iron status is unknown."
        ),
        "prevalence":     "6.05% (450/7437)",
        "class_imbalance":"15.5:1",
        "feature_names":  ENCODED_FEATURE_NAMES,
        "n_features":     len(ENCODED_FEATURE_NAMES),
        "feature_groups": FEATURE_GROUPS,
        "excluded_iron_specific": EXCLUDED_IRON_SPECIFIC,
        "exclusion_reason_iron_specific": (
            "These biomarkers likely define the iron_deficiency label (data leakage). "
            "They are unavailable in a pre-diagnosis screening context."
        ),
        "dropped_by_threshold": DROPPED_BY_THRESHOLD,
        "drop_rule": "|r| < 0.03 AND p > 0.05 vs iron_deficiency target",
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
    print("  Iron Deficiency Checkup Model — Training Pipeline")
    print("  (Group A iron-specific labs excluded by design)")
    print("=" * 60)

    df = load_data()
    X, y = prepare_features(df)
    X_train, X_test, y_train, y_test = split_data(X, y)

    print("\n[1/2] Training Logistic Regression...")
    lr = build_lr_pipeline()
    lr.fit(X_train, y_train)
    lr_metrics = evaluate_model(lr, X_test, y_test, threshold=0.3,
                                model_name="LR Iron Deficiency Checkup")
    save_model(lr, "iron_deficiency_checkup_lr", lr_metrics)

    print("\n[2/2] Training XGBoost...")
    xgb = build_xgb_pipeline()
    xgb.fit(X_train, y_train)
    xgb_metrics = evaluate_model(xgb, X_test, y_test, threshold=0.3,
                                 model_name="XGBoost Iron Deficiency Checkup")
    save_model(xgb, "iron_deficiency_checkup_xgb", xgb_metrics)

    print("\n" + "=" * 60)
    print(pd.DataFrame([lr_metrics, xgb_metrics]).to_string(index=False))

    return lr, xgb, lr_metrics, xgb_metrics


if __name__ == "__main__":
    run_training_pipeline()
