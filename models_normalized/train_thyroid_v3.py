"""
train_thyroid_v3.py
-------------------
ML-THYROID-02: reduce saturated fatigue-heavy overfiring.

Strategy:
  - keep a compact LR for runtime simplicity
  - add thyroid-shaped derived features (metabolic bundle, sleep-overlap bundle,
    weight-pattern bundle)
  - retrain with hard negatives from sleep, anemia, and stress/fatigue lookalikes
  - target a user-facing threshold around 0.72 for better recall/flag balance
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_val_score
from sklearn.pipeline import Pipeline

_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
_ROOT = _DIR.parent

DATA_PATH = _ROOT / "data" / "processed" / "nhanes_merged_adults_final_normalized.csv"
MODELS_DIR = _DIR
MODEL_NAME = "thyroid_lr_hardneg_v3"
TARGET = "thyroid"
SEED = 42
RNG = np.random.default_rng(SEED)

BASE_FEATURES = [
    "age_years",
    "med_count",
    "huq010___general_health_condition",
    "dpq040___feeling_tired_or_having_little_energy",
    "slq050___ever_told_doctor_had_trouble_sleeping?",
    "sld012___sleep_hours___weekdays_or_workdays",
    "mcq080___doctor_ever_said_you_were_overweight",
    "whq070___tried_to_lose_weight_in_past_year",
    "whq040___like_to_weigh_more,_less_or_same",
    "bmi",
    "weight_kg",
    "pulse_1",
    "total_cholesterol_mg_dl",
    "alq130___avg_#_alcoholic_drinks/day___past_12_mos",
    "kiq480___how_many_times_urinate_in_night?",
]

DERIVED_FEATURES = [
    "thyroid_metabolic_bundle",
    "thyroid_sleep_override",
    "thyroid_weight_pattern",
]

FEATURES = BASE_FEATURES + DERIVED_FEATURES

PIPELINE_GATE = 0.35
RECOMMENDED_THRESHOLD = 0.72


def _ri(lo: int, hi: int, size: int) -> np.ndarray:
    return RNG.integers(lo, hi + 1, size=size).astype(float)


def _ru(lo: float, hi: float, size: int) -> np.ndarray:
    return RNG.uniform(lo, hi, size)


def _add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "gender_female" not in out.columns:
        if "gender" in out.columns:
            out["gender_female"] = (out["gender"] == 2).astype(float)
        else:
            out["gender_female"] = np.nan

    fat = out["dpq040___feeling_tired_or_having_little_energy"].fillna(0)
    sleep = out["slq050___ever_told_doctor_had_trouble_sleeping?"].fillna(2)
    sleep_hours = out["sld012___sleep_hours___weekdays_or_workdays"].fillna(0)
    poor = out["huq010___general_health_condition"].fillna(3)
    overweight = out["mcq080___doctor_ever_said_you_were_overweight"].fillna(2)
    tried = out["whq070___tried_to_lose_weight_in_past_year"].fillna(2)
    bmi = out["bmi"].fillna(0)
    pulse = out["pulse_1"].fillna(0)
    chol = out["total_cholesterol_mg_dl"].fillna(0)
    nocturia = out["kiq480___how_many_times_urinate_in_night?"].fillna(0)

    out["thyroid_metabolic_bundle"] = (
        (fat >= 1).astype(float)
        + (poor >= 3).astype(float)
        + (bmi > 0.15).astype(float)
        + (chol > 0.15).astype(float)
        + (pulse < -0.05).astype(float)
    )
    out["thyroid_sleep_override"] = (
        (sleep == 1).astype(float)
        + (sleep_hours < -0.25).astype(float)
        + (tried == 1).astype(float)
        + (nocturia > 0.20).astype(float)
    )
    out["thyroid_weight_pattern"] = (
        (overweight == 1).astype(float)
        + (tried == 2).astype(float)
        + (bmi > 0.15).astype(float)
    )
    return out


def _sleep_like_negatives(n: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "age_years": _ri(28, 62, n),
            "med_count": _ru(-0.2, 0.8, n),
            "huq010___general_health_condition": _ri(2, 4, n),
            "dpq040___feeling_tired_or_having_little_energy": _ri(1, 3, n),
            "slq050___ever_told_doctor_had_trouble_sleeping?": np.full(n, 1.0),
            "sld012___sleep_hours___weekdays_or_workdays": _ru(-1.3, -0.2, n),
            "mcq080___doctor_ever_said_you_were_overweight": _ri(1, 2, n),
            "whq070___tried_to_lose_weight_in_past_year": _ri(1, 2, n),
            "whq040___like_to_weigh_more,_less_or_same": _ri(1, 3, n),
            "bmi": _ru(-0.1, 0.8, n),
            "weight_kg": _ru(-0.2, 0.8, n),
            "pulse_1": _ru(0.0, 0.9, n),
            "total_cholesterol_mg_dl": _ru(-0.4, 0.2, n),
            "alq130___avg_#_alcoholic_drinks/day___past_12_mos": _ru(-0.3, 0.6, n),
            "kiq480___how_many_times_urinate_in_night?": _ru(0.0, 0.8, n),
            "gender_female": _ri(0, 1, n),
            TARGET: np.zeros(n),
        }
    )


def _anemia_like_negatives(n: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "age_years": _ri(20, 55, n),
            "med_count": _ru(-0.6, 0.2, n),
            "huq010___general_health_condition": _ri(2, 4, n),
            "dpq040___feeling_tired_or_having_little_energy": _ri(1, 3, n),
            "slq050___ever_told_doctor_had_trouble_sleeping?": _ri(1, 2, n),
            "sld012___sleep_hours___weekdays_or_workdays": _ru(-0.2, 0.5, n),
            "mcq080___doctor_ever_said_you_were_overweight": _ri(1, 2, n),
            "whq070___tried_to_lose_weight_in_past_year": _ri(1, 2, n),
            "whq040___like_to_weigh_more,_less_or_same": _ri(1, 3, n),
            "bmi": _ru(-0.4, 0.5, n),
            "weight_kg": _ru(-0.4, 0.5, n),
            "pulse_1": _ru(0.0, 0.8, n),
            "total_cholesterol_mg_dl": _ru(-0.4, 0.1, n),
            "alq130___avg_#_alcoholic_drinks/day___past_12_mos": _ru(-0.2, 0.7, n),
            "kiq480___how_many_times_urinate_in_night?": _ru(-0.2, 0.4, n),
            "gender_female": np.ones(n),
            TARGET: np.zeros(n),
        }
    )


def _stress_like_negatives(n: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "age_years": _ri(22, 50, n),
            "med_count": _ru(-0.8, 0.1, n),
            "huq010___general_health_condition": _ri(2, 4, n),
            "dpq040___feeling_tired_or_having_little_energy": _ri(1, 3, n),
            "slq050___ever_told_doctor_had_trouble_SLEEPING?": _ri(1, 2, n),
            "sld012___sleep_hours___weekdays_or_workdays": _ru(-0.8, 0.2, n),
            "mcq080___doctor_ever_said_you_were_overweight": _ri(1, 2, n),
            "whq070___tried_to_lose_weight_in_past_year": _ri(1, 2, n),
            "whq040___like_to_weigh_more,_less_or_same": _ri(1, 3, n),
            "bmi": _ru(-0.2, 0.6, n),
            "weight_kg": _ru(-0.2, 0.6, n),
            "pulse_1": _ru(0.2, 1.1, n),
            "total_cholesterol_mg_dl": _ru(-0.5, 0.1, n),
            "alq130___avg_#_alcoholic_drinks/day___past_12_mos": _ru(-0.1, 1.0, n),
            "kiq480___how_many_times_urinate_in_night?": _ru(-0.2, 0.6, n),
            "gender_female": _ri(0, 1, n),
            TARGET: np.zeros(n),
        }
    ).rename(columns={"slq050___ever_told_doctor_had_trouble_SLEEPING?": "slq050___ever_told_doctor_had_trouble_sleeping?"})


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("imp", SimpleImputer(strategy="median", add_indicator=True)),
            ("clf", LogisticRegression(class_weight="balanced", C=0.7, max_iter=3000, random_state=SEED)),
        ]
    )


def main() -> None:
    print("=" * 60)
    print("  Thyroid LR v3 — Hard Negatives + Sleep/Metabolic Bundles")
    print("=" * 60)

    df = pd.read_csv(DATA_PATH, low_memory=False)
    required_cols = BASE_FEATURES + [TARGET]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    real_cols = list(BASE_FEATURES)
    if "gender" in df.columns:
        real_cols.append("gender")
    X_real = _add_derived_columns(df[real_cols].copy())
    y_real = df[TARGET].fillna(0).astype(int)
    prevalence = float(y_real.mean())
    print(f"Loaded: {len(df):,} rows")
    print(f"Target prevalence: {prevalence:.3%} ({int(y_real.sum())}/{len(y_real)})")

    hard_neg = pd.concat(
        [_sleep_like_negatives(250), _anemia_like_negatives(180), _stress_like_negatives(180)],
        ignore_index=True,
    )
    X_hard = _add_derived_columns(hard_neg[BASE_FEATURES])
    y_hard = hard_neg[TARGET].astype(int)
    print(f"Hard negatives: {len(hard_neg):,}")

    X = pd.concat([X_real[FEATURES], X_hard[FEATURES]], ignore_index=True)
    y = pd.concat([y_real, y_hard], ignore_index=True)

    pipe = build_pipeline()
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)

    auc_scores = cross_val_score(pipe, X, y, cv=cv, scoring="roc_auc", n_jobs=1)
    ap_scores = cross_val_score(pipe, X, y, cv=cv, scoring="average_precision", n_jobs=1)
    oof = cross_val_predict(pipe, X, y, cv=cv, method="predict_proba", n_jobs=1)[:, 1]

    pipe.fit(X, y)
    train_proba = pipe.predict_proba(X)[:, 1]

    real_train = train_proba[: len(y_real)]
    hard_train = train_proba[len(y_real):]

    recall_gate = float(((real_train >= PIPELINE_GATE) & (y_real == 1)).sum() / max(int(y_real.sum()), 1))
    recall_rec = float(((real_train >= RECOMMENDED_THRESHOLD) & (y_real == 1)).sum() / max(int(y_real.sum()), 1))
    precision_rec = float(((real_train >= RECOMMENDED_THRESHOLD) & (y_real == 1)).sum() / max(int((real_train >= RECOMMENDED_THRESHOLD).sum()), 1))
    hard_neg_leak = float((hard_train >= RECOMMENDED_THRESHOLD).mean())

    print(f"CV AUC:            {auc_scores.mean():.4f} ± {auc_scores.std():.4f}")
    print(f"CV Avg Precision:  {ap_scores.mean():.4f}")
    print(f"OOF AUC:           {roc_auc_score(y, oof):.4f}")
    print(f"OOF Avg Precision: {average_precision_score(y, oof):.4f}")
    print(f"Train recall @ {PIPELINE_GATE:.2f}: {recall_gate:.4f}")
    print(f"Train recall @ {RECOMMENDED_THRESHOLD:.2f}: {recall_rec:.4f}")
    print(f"Train prec   @ {RECOMMENDED_THRESHOLD:.2f}: {precision_rec:.4f}")
    print(f"Hard-neg leak@ {RECOMMENDED_THRESHOLD:.2f}: {hard_neg_leak:.4f}")

    artifact_path = MODELS_DIR / f"{MODEL_NAME}.joblib"
    meta_path = MODELS_DIR / f"{MODEL_NAME}_metadata.json"

    joblib.dump(pipe, artifact_path)

    metadata = {
        "model": artifact_path.name,
        "version": "v3",
        "condition": "thyroid",
        "algorithm": "LogisticRegression hard-neg v3",
        "data_source": DATA_PATH.name,
        "n_train": int(len(X)),
        "prevalence": prevalence,
        "features": FEATURES,
        "n_features": len(FEATURES),
        "cv_folds": 5,
        "cv_auc_mean": float(auc_scores.mean()),
        "cv_auc_std": float(auc_scores.std()),
        "cv_avg_precision": float(ap_scores.mean()),
        "pipeline_gate": PIPELINE_GATE,
        "pipeline_gate_rationale": "Global routing gate: scores above 0.35 escalate to next pipeline step",
        "recommended_threshold": RECOMMENDED_THRESHOLD,
        "recommended_threshold_criterion": "Chosen for better recall/flag balance after hard-negative retraining; intended to replace the blunt 0.75 cleanup threshold.",
        "train_recall_at_recommended_threshold": recall_rec,
        "train_precision_at_recommended_threshold": precision_rec,
        "hard_negative_leak_at_recommended_threshold": hard_neg_leak,
        "pipeline_steps": [
            "SimpleImputer(strategy=median, add_indicator=True)",
            "LogisticRegression(L2, class_weight=balanced, C=0.7)",
        ],
        "changes_from_v2": [
            "Expanded features to include sleep hours, BMI, pulse, cholesterol, and weight-pattern fields",
            "Added thyroid_metabolic_bundle, thyroid_sleep_override, thyroid_weight_pattern",
            "Added hard negatives from sleep, anemia, and stress/fatigue lookalikes",
        ],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    meta_path.write_text(json.dumps(metadata, indent=2) + "\n")

    print(f"Saved artifact: {artifact_path}")
    print(f"Saved metadata: {meta_path}")


if __name__ == "__main__":
    main()
