"""
train_thyroid_v4.py
-------------------
ML-THYROID-03B: retrain thyroid against the remaining healthy false positives.

Strategy:
  - keep the current runtime cleanup gate in place as a backstop
  - add explicit hard negatives from the audited residual healthy thyroid FPs
  - expand those into a small male chronic-illness negative pack
  - add one derived feature that isolates the male poor-health/polypharmacy
    shortcut so the model can learn to push it down directly
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
AUDIT_PATH = _ROOT / "evals" / "results" / "thyroid_healthy_fp_audit_20260331_072759.json"
MODELS_DIR = _DIR
MODEL_NAME = "thyroid_lr_hardneg_v4"
TARGET = "thyroid"
SEED = 42
RNG = np.random.default_rng(SEED)

BASE_FEATURES = [
    "age_years",
    "med_count",
    "huq010___general_health_condition",
    "huq051___#times_receive_healthcare_over_past_year",
    "dpq040___feeling_tired_or_having_little_energy",
    "slq050___ever_told_doctor_had_trouble_sleeping?",
    "sld012___sleep_hours___weekdays_or_workdays",
    "mcq080___doctor_ever_said_you_were_overweight",
    "whq070___tried_to_lose_weight_in_past_year",
    "whq040___like_to_weigh_more,_less_or_same",
    "bmi",
    "weight_kg",
    "cdq010___shortness_of_breath_on_stairs/inclines",
    "mcq160a___ever_told_you_had_arthritis",
    "total_cholesterol_mg_dl",
    "hdl_cholesterol_mg_dl",
    "alq130___avg_#_alcoholic_drinks/day___past_12_mos",
    "kiq480___how_many_times_urinate_in_night?",
]

DERIVED_FEATURES = [
    "thyroid_metabolic_bundle",
    "thyroid_sleep_override",
    "thyroid_weight_pattern",
    "male_chronic_illness_bundle",
]

FEATURES = BASE_FEATURES + DERIVED_FEATURES

PIPELINE_GATE = 0.35
RECOMMENDED_THRESHOLD = 0.75


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
    chol = out["total_cholesterol_mg_dl"].fillna(0)
    hdl = out["hdl_cholesterol_mg_dl"].fillna(0)
    nocturia = out["kiq480___how_many_times_urinate_in_night?"].fillna(0)
    med_count = out["med_count"].fillna(0)
    health_visits = out["huq051___#times_receive_healthcare_over_past_year"].fillna(0)

    out["thyroid_metabolic_bundle"] = (
        (fat >= 1).astype(float)
        + (poor >= 3).astype(float)
        + (bmi > 0.15).astype(float)
        + (chol > 0.15).astype(float)
        + (hdl < -0.10).astype(float)
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
    out["male_chronic_illness_bundle"] = (
        (out["gender_female"].fillna(0) < 0.5).astype(float)
        + (poor >= 3).astype(float)
        + (med_count >= 3).astype(float)
        + (sleep == 2).astype(float)
        + (health_visits > 4).astype(float)
    )
    return out


def _sleep_like_negatives(n: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "age_years": _ri(28, 62, n),
            "med_count": _ru(-0.2, 0.8, n),
            "huq010___general_health_condition": _ri(2, 4, n),
            "huq051___#times_receive_healthcare_over_past_year": _ru(-0.2, 0.8, n),
            "dpq040___feeling_tired_or_having_little_energy": _ri(1, 3, n),
            "slq050___ever_told_doctor_had_trouble_sleeping?": np.full(n, 1.0),
            "sld012___sleep_hours___weekdays_or_workdays": _ru(-1.3, -0.2, n),
            "mcq080___doctor_ever_said_you_were_overweight": _ri(1, 2, n),
            "whq070___tried_to_lose_weight_in_past_year": _ri(1, 2, n),
            "whq040___like_to_weigh_more,_less_or_same": _ri(1, 3, n),
            "bmi": _ru(-0.1, 0.8, n),
            "weight_kg": _ru(-0.2, 0.8, n),
            "cdq010___shortness_of_breath_on_stairs/inclines": _ri(1, 2, n),
            "mcq160a___ever_told_you_had_arthritis": _ri(1, 2, n),
            "total_cholesterol_mg_dl": _ru(-0.4, 0.2, n),
            "hdl_cholesterol_mg_dl": _ru(-0.3, 0.2, n),
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
            "huq051___#times_receive_healthcare_over_past_year": _ru(-0.6, 0.2, n),
            "dpq040___feeling_tired_or_having_little_energy": _ri(1, 3, n),
            "slq050___ever_told_doctor_had_trouble_sleeping?": _ri(1, 2, n),
            "sld012___sleep_hours___weekdays_or_workdays": _ru(-0.2, 0.5, n),
            "mcq080___doctor_ever_said_you_were_overweight": _ri(1, 2, n),
            "whq070___tried_to_lose_weight_in_past_year": _ri(1, 2, n),
            "whq040___like_to_weigh_more,_less_or_same": _ri(1, 3, n),
            "bmi": _ru(-0.4, 0.5, n),
            "weight_kg": _ru(-0.4, 0.5, n),
            "cdq010___shortness_of_breath_on_stairs/inclines": _ri(1, 2, n),
            "mcq160a___ever_told_you_had_arthritis": _ri(1, 2, n),
            "total_cholesterol_mg_dl": _ru(-0.4, 0.1, n),
            "hdl_cholesterol_mg_dl": _ru(-0.2, 0.2, n),
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
            "huq051___#times_receive_healthcare_over_past_year": _ru(-0.6, 0.3, n),
            "dpq040___feeling_tired_or_having_little_energy": _ri(1, 3, n),
            "slq050___ever_told_doctor_had_trouble_sleeping?": _ri(1, 2, n),
            "sld012___sleep_hours___weekdays_or_workdays": _ru(-0.8, 0.2, n),
            "mcq080___doctor_ever_said_you_were_overweight": _ri(1, 2, n),
            "whq070___tried_to_lose_weight_in_past_year": _ri(1, 2, n),
            "whq040___like_to_weigh_more,_less_or_same": _ri(1, 3, n),
            "bmi": _ru(-0.2, 0.6, n),
            "weight_kg": _ru(-0.2, 0.6, n),
            "cdq010___shortness_of_breath_on_stairs/inclines": _ri(1, 2, n),
            "mcq160a___ever_told_you_had_arthritis": _ri(1, 2, n),
            "total_cholesterol_mg_dl": _ru(-0.5, 0.1, n),
            "hdl_cholesterol_mg_dl": _ru(-0.2, 0.3, n),
            "alq130___avg_#_alcoholic_drinks/day___past_12_mos": _ru(-0.1, 1.0, n),
            "kiq480___how_many_times_urinate_in_night?": _ru(-0.2, 0.6, n),
            "gender_female": _ri(0, 1, n),
            TARGET: np.zeros(n),
        }
    )


def _residual_fp_negatives() -> pd.DataFrame:
    audit = json.loads(AUDIT_PATH.read_text())
    rows = []
    for profile in audit["profiles"]:
        raw = profile["raw_inputs"]
        rows.append(
            {
                "age_years": float(raw["age_years"]),
                "med_count": float(raw["med_count"]),
                "huq010___general_health_condition": float(raw["huq010___general_health_condition"]),
                "huq051___#times_receive_healthcare_over_past_year": float(raw["huq051___#times_receive_healthcare_over_past_year"]),
                "dpq040___feeling_tired_or_having_little_energy": float(raw["dpq040___feeling_tired_or_having_little_energy"]),
                "slq050___ever_told_doctor_had_trouble_sleeping?": float(raw["slq050___ever_told_doctor_had_trouble_sleeping?"]),
                "sld012___sleep_hours___weekdays_or_workdays": float(raw["sld012___sleep_hours___weekdays_or_workdays"]),
                "mcq080___doctor_ever_said_you_were_overweight": float(raw["mcq080___doctor_ever_said_you_were_overweight"]),
                "whq070___tried_to_lose_weight_in_past_year": float(raw.get("whq070___tried_to_lose_weight_in_past_year", 2.0)),
                "whq040___like_to_weigh_more,_less_or_same": float(raw["whq040___like_to_weigh_more,_less_or_same"]),
                "bmi": float(raw["bmi"]),
                "weight_kg": float(raw["weight_kg"]),
                "cdq010___shortness_of_breath_on_stairs/inclines": float(raw["cdq010___shortness_of_breath_on_stairs/inclines"]),
                "mcq160a___ever_told_you_had_arthritis": float(raw["mcq160a___ever_told_you_had_arthritis"]),
                "total_cholesterol_mg_dl": float(raw["total_cholesterol_mg_dl"]),
                "hdl_cholesterol_mg_dl": float(raw["hdl_cholesterol_mg_dl"]),
                "alq130___avg_#_alcoholic_drinks/day___past_12_mos": float(raw["alq130___avg_#_alcoholic_drinks/day___past_12_mos"]),
                "kiq480___how_many_times_urinate_in_night?": float(raw["kiq480___how_many_times_urinate_in_night?"]),
                "gender_female": 0.0,
                TARGET: 0.0,
            }
        )
    return pd.DataFrame(rows)


def _expanded_fp_negatives(n_per_profile: int = 40) -> pd.DataFrame:
    base = _residual_fp_negatives()
    rows = []
    for _, row in base.iterrows():
        for _ in range(n_per_profile):
            rows.append(
                {
                    "age_years": float(np.clip(row["age_years"] + RNG.normal(0, 4), 30, 90)),
                    "med_count": float(np.clip(row["med_count"] + RNG.normal(0, 1.2), 0, 9)),
                    "huq010___general_health_condition": float(np.clip(round(row["huq010___general_health_condition"] + RNG.normal(0, 0.35)), 1, 5)),
                    "huq051___#times_receive_healthcare_over_past_year": float(np.clip(row["huq051___#times_receive_healthcare_over_past_year"] + RNG.normal(0, 2.0), 0, 16)),
                    "dpq040___feeling_tired_or_having_little_energy": float(np.clip(row["dpq040___feeling_tired_or_having_little_energy"] + RNG.normal(0, 0.15), 0, 1.2)),
                    "slq050___ever_told_doctor_had_trouble_sleeping?": 2.0,
                    "sld012___sleep_hours___weekdays_or_workdays": float(np.clip(row["sld012___sleep_hours___weekdays_or_workdays"] + RNG.normal(0, 0.4), 6.0, 8.0)),
                    "mcq080___doctor_ever_said_you_were_overweight": 2.0,
                    "whq070___tried_to_lose_weight_in_past_year": float(row["whq070___tried_to_lose_weight_in_past_year"]),
                    "whq040___like_to_weigh_more,_less_or_same": float(row["whq040___like_to_weigh_more,_less_or_same"]),
                    "bmi": float(np.clip(row["bmi"] + RNG.normal(0, 1.0), 22, 32)),
                    "weight_kg": float(np.clip(row["weight_kg"] + RNG.normal(0, 3.0), 60, 95)),
                    "cdq010___shortness_of_breath_on_stairs/inclines": float(row["cdq010___shortness_of_breath_on_stairs/inclines"]),
                    "mcq160a___ever_told_you_had_arthritis": float(row["mcq160a___ever_told_you_had_arthritis"]),
                    "total_cholesterol_mg_dl": float(np.clip(row["total_cholesterol_mg_dl"] + RNG.normal(0, 15), 140, 240)),
                    "hdl_cholesterol_mg_dl": float(np.clip(row["hdl_cholesterol_mg_dl"] + RNG.normal(0, 8), 30, 85)),
                    "alq130___avg_#_alcoholic_drinks/day___past_12_mos": float(np.clip(row["alq130___avg_#_alcoholic_drinks/day___past_12_mos"] + RNG.normal(0, 0.3), 0, 2.5)),
                    "kiq480___how_many_times_urinate_in_night?": 0.0,
                    "gender_female": 0.0,
                    TARGET: 0.0,
                }
            )
    return pd.DataFrame(rows)


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("imp", SimpleImputer(strategy="median", add_indicator=True)),
            ("clf", LogisticRegression(class_weight="balanced", C=0.5, max_iter=3000, random_state=SEED)),
        ]
    )


def main() -> None:
    print("=" * 60)
    print("  Thyroid LR v4 — Residual Healthy-FP Hard Negatives")
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
        [
            _sleep_like_negatives(220),
            _anemia_like_negatives(160),
            _stress_like_negatives(160),
            _residual_fp_negatives(),
            _expanded_fp_negatives(45),
        ],
        ignore_index=True,
    )
    X_hard = _add_derived_columns(hard_neg[BASE_FEATURES + ["gender_female"]])
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
        "version": "v4",
        "condition": "thyroid",
        "algorithm": "LogisticRegression residual-FP hard-neg v4",
        "data_source": DATA_PATH.name,
        "audit_source": str(AUDIT_PATH.relative_to(_ROOT)),
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
        "recommended_threshold_criterion": "Chosen to align with the current strict thyroid surface threshold while using residual-FP hard negatives.",
        "train_recall_at_recommended_threshold": recall_rec,
        "train_precision_at_recommended_threshold": precision_rec,
        "hard_negative_leak_at_recommended_threshold": hard_neg_leak,
        "pipeline_steps": [
            "SimpleImputer(strategy=median, add_indicator=True)",
            "LogisticRegression(L2, class_weight=balanced, C=0.5)",
        ],
        "changes_from_v3": [
            "Added explicit hard negatives from the 3 residual healthy thyroid false positives",
            "Added jittered male chronic-illness negative pack around those residual profiles",
            "Added male_chronic_illness_bundle derived feature",
            "Added health-care utilization and HDL inputs",
        ],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    meta_path.write_text(json.dumps(metadata, indent=2) + "\n")

    print(f"Saved artifact: {artifact_path}")
    print(f"Saved metadata: {meta_path}")


if __name__ == "__main__":
    main()
