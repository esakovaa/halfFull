"""
train_thyroid_v5.py
-------------------
ML-THYROID-04: improve on gated thyroid v2 without reopening healthy-user noise.

Strategy:
  - start closer to the validated v2 signal shape instead of the broader v4
  - train against both the residual gated-v2 healthy false positives and the
    seven false positives that v4 reintroduced
  - keep the runtime thyroid gate in place as a temporary backstop
  - bias the model away from broad male chronic-illness shortcuts unless paired
    with more thyroid-shaped metabolic or fatigue signal
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
AUDIT_PATHS = [
    _ROOT / "evals" / "results" / "thyroid_healthy_fp_audit_20260331_072759.json",
    _ROOT / "evals" / "results" / "thyroid_healthy_fp_audit_20260331_074232.json",
]
MODELS_DIR = _DIR
MODEL_NAME = "thyroid_lr_hardneg_v5"
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
    "weight_kg",
    "pulse_1",
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
    "thyroid_specific_anchor",
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
    visits = out["huq051___#times_receive_healthcare_over_past_year"].fillna(0)
    overweight = out["mcq080___doctor_ever_said_you_were_overweight"].fillna(2)
    tried = out["whq070___tried_to_lose_weight_in_past_year"].fillna(2)
    weight = out["weight_kg"].fillna(0)
    pulse = out["pulse_1"].fillna(0)
    chol = out["total_cholesterol_mg_dl"].fillna(0)
    hdl = out["hdl_cholesterol_mg_dl"].fillna(0)
    alcohol = out["alq130___avg_#_alcoholic_drinks/day___past_12_mos"].fillna(0)
    nocturia = out["kiq480___how_many_times_urinate_in_night?"].fillna(0)
    meds = out["med_count"].fillna(0)
    male = (out["gender_female"].fillna(0) < 0.5).astype(float)

    out["thyroid_metabolic_bundle"] = (
        (fat >= 1).astype(float)
        + (poor >= 3).astype(float)
        + (chol > 0.15).astype(float)
        + (hdl < -0.10).astype(float)
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
        + (weight > 0.10).astype(float)
    )
    out["male_chronic_illness_bundle"] = (
        male
        + (poor >= 3).astype(float)
        + (meds >= 3).astype(float)
        + (sleep == 2).astype(float)
        + (visits > 4).astype(float)
    )
    out["thyroid_specific_anchor"] = (
        (fat >= 1).astype(float)
        + (sleep == 2).astype(float)
        + (chol > 0.15).astype(float)
        + (pulse < -0.05).astype(float)
        + (alcohol < -0.10).astype(float)
    )
    return out


def _sleep_like_negatives(n: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "age_years": _ri(28, 62, n),
            "med_count": _ru(-0.2, 0.8, n),
            "huq010___general_health_condition": _ri(2, 4, n),
            "huq051___#times_receive_healthcare_over_past_year": _ru(-0.2, 1.2, n),
            "dpq040___feeling_tired_or_having_little_energy": _ri(1, 3, n),
            "slq050___ever_told_doctor_had_trouble_sleeping?": np.full(n, 1.0),
            "sld012___sleep_hours___weekdays_or_workdays": _ru(-1.3, -0.2, n),
            "mcq080___doctor_ever_said_you_were_overweight": _ri(1, 2, n),
            "whq070___tried_to_lose_weight_in_past_year": _ri(1, 2, n),
            "whq040___like_to_weigh_more,_less_or_same": _ri(1, 3, n),
            "weight_kg": _ru(-0.2, 0.8, n),
            "pulse_1": _ru(0.0, 0.9, n),
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
            "huq051___#times_receive_healthcare_over_past_year": _ru(-0.5, 0.8, n),
            "dpq040___feeling_tired_or_having_little_energy": _ri(1, 3, n),
            "slq050___ever_told_doctor_had_trouble_sleeping?": _ri(1, 2, n),
            "sld012___sleep_hours___weekdays_or_workdays": _ru(-0.2, 0.5, n),
            "mcq080___doctor_ever_said_you_were_overweight": _ri(1, 2, n),
            "whq070___tried_to_lose_weight_in_past_year": _ri(1, 2, n),
            "whq040___like_to_weigh_more,_less_or_same": _ri(1, 3, n),
            "weight_kg": _ru(-0.4, 0.5, n),
            "pulse_1": _ru(0.0, 0.8, n),
            "total_cholesterol_mg_dl": _ru(-0.4, 0.1, n),
            "hdl_cholesterol_mg_dl": _ru(-0.2, 0.2, n),
            "alq130___avg_#_alcoholic_drinks/day___past_12_mos": _ru(-0.2, 0.7, n),
            "kiq480___how_many_times_urinate_in_night?": _ru(-0.2, 0.4, n),
            "gender_female": np.ones(n),
            TARGET: np.zeros(n),
        }
    )


def _male_chronic_negatives(n: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "age_years": _ri(55, 88, n),
            "med_count": _ru(1.0, 7.5, n),
            "huq010___general_health_condition": _ri(2, 4, n),
            "huq051___#times_receive_healthcare_over_past_year": _ru(1.0, 10.0, n),
            "dpq040___feeling_tired_or_having_little_energy": _ru(0.0, 1.1, n),
            "slq050___ever_told_doctor_had_trouble_sleeping?": np.full(n, 2.0),
            "sld012___sleep_hours___weekdays_or_workdays": _ru(6.2, 8.0, n),
            "mcq080___doctor_ever_said_you_were_overweight": _ri(1, 2, n),
            "whq070___tried_to_lose_weight_in_past_year": _ri(1, 2, n),
            "whq040___like_to_weigh_more,_less_or_same": _ri(1, 3, n),
            "weight_kg": _ru(-0.1, 0.8, n),
            "pulse_1": _ru(-0.05, 0.35, n),
            "total_cholesterol_mg_dl": _ru(-0.05, 0.35, n),
            "hdl_cholesterol_mg_dl": _ru(-0.1, 0.3, n),
            "alq130___avg_#_alcoholic_drinks/day___past_12_mos": _ru(-0.3, 0.4, n),
            "kiq480___how_many_times_urinate_in_night?": _ru(0.0, 0.8, n),
            "gender_female": np.zeros(n),
            TARGET: np.zeros(n),
        }
    )


def _load_audit_profiles() -> pd.DataFrame:
    rows: list[dict[str, float]] = []
    seen: set[str] = set()
    for path in AUDIT_PATHS:
        audit = json.loads(path.read_text())
        for profile in audit["profiles"]:
            profile_id = profile["profile_id"]
            if profile_id in seen:
                continue
            seen.add(profile_id)
            raw = profile["raw_inputs"]
            rows.append(
                {
                    "profile_id": profile_id,
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
                    "weight_kg": float(raw["weight_kg"]),
                    "pulse_1": float(raw["pulse_1"]) if raw.get("pulse_1") is not None else np.nan,
                    "total_cholesterol_mg_dl": float(raw["total_cholesterol_mg_dl"]),
                    "hdl_cholesterol_mg_dl": float(raw["hdl_cholesterol_mg_dl"]),
                    "alq130___avg_#_alcoholic_drinks/day___past_12_mos": float(raw["alq130___avg_#_alcoholic_drinks/day___past_12_mos"]),
                    "kiq480___how_many_times_urinate_in_night?": float(raw["kiq480___how_many_times_urinate_in_night?"]),
                    "gender_female": float(raw.get("gender_female", 0.0)),
                    TARGET: 0.0,
                }
            )
    return pd.DataFrame(rows)


def _expanded_audit_negatives(n_per_profile: int = 36) -> pd.DataFrame:
    base = _load_audit_profiles()
    rows = []
    for _, row in base.iterrows():
        male = row["gender_female"] < 0.5
        older = row["age_years"] >= 60
        for _ in range(n_per_profile):
            rows.append(
                {
                    "age_years": float(np.clip(row["age_years"] + RNG.normal(0, 4 if older else 6), 28, 90)),
                    "med_count": float(np.clip(row["med_count"] + RNG.normal(0, 1.0), 0, 9)),
                    "huq010___general_health_condition": float(np.clip(round(row["huq010___general_health_condition"] + RNG.normal(0, 0.35)), 1, 5)),
                    "huq051___#times_receive_healthcare_over_past_year": float(np.clip(row["huq051___#times_receive_healthcare_over_past_year"] + RNG.normal(0, 1.8), 0, 16)),
                    "dpq040___feeling_tired_or_having_little_energy": float(np.clip(row["dpq040___feeling_tired_or_having_little_energy"] + RNG.normal(0, 0.12), 0, 1.2)),
                    "slq050___ever_told_doctor_had_trouble_sleeping?": float(1.0 if RNG.random() < 0.08 else 2.0),
                    "sld012___sleep_hours___weekdays_or_workdays": float(np.clip(row["sld012___sleep_hours___weekdays_or_workdays"] + RNG.normal(0, 0.35), 6.0, 8.3)),
                    "mcq080___doctor_ever_said_you_were_overweight": float(row["mcq080___doctor_ever_said_you_were_overweight"]),
                    "whq070___tried_to_lose_weight_in_past_year": float(row["whq070___tried_to_lose_weight_in_past_year"]),
                    "whq040___like_to_weigh_more,_less_or_same": float(row["whq040___like_to_weigh_more,_less_or_same"]),
                    "weight_kg": float(np.clip(row["weight_kg"] + RNG.normal(0, 2.5), 55, 105)),
                    "pulse_1": float(np.clip((0.05 if np.isnan(row["pulse_1"]) else row["pulse_1"]) + RNG.normal(0, 0.18), -0.25, 0.8)),
                    "total_cholesterol_mg_dl": float(np.clip(row["total_cholesterol_mg_dl"] + RNG.normal(0, 12), 130, 260)),
                    "hdl_cholesterol_mg_dl": float(np.clip(row["hdl_cholesterol_mg_dl"] + RNG.normal(0, 7), 25, 90)),
                    "alq130___avg_#_alcoholic_drinks/day___past_12_mos": float(np.clip(row["alq130___avg_#_alcoholic_drinks/day___past_12_mos"] + RNG.normal(0, 0.25), 0, 2.5)),
                    "kiq480___how_many_times_urinate_in_night?": float(np.clip(row["kiq480___how_many_times_urinate_in_night?"] + RNG.normal(0, 0.25), 0, 2.5)),
                    "gender_female": 0.0 if male else 1.0,
                    TARGET: 0.0,
                }
            )
    return pd.DataFrame(rows)


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("imp", SimpleImputer(strategy="median", add_indicator=True)),
            ("clf", LogisticRegression(class_weight="balanced", C=0.45, max_iter=3000, random_state=SEED)),
        ]
    )


def main() -> None:
    print("=" * 60)
    print("  Thyroid LR v5 — Expanded Healthy-FP Hard Negatives")
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

    audit_base = _load_audit_profiles()
    hard_neg = pd.concat(
        [
            _sleep_like_negatives(180),
            _anemia_like_negatives(120),
            _male_chronic_negatives(220),
            audit_base,
            _expanded_audit_negatives(36),
        ],
        ignore_index=True,
    )
    X_hard = _add_derived_columns(hard_neg[BASE_FEATURES + ["gender_female"]])
    y_hard = hard_neg[TARGET].astype(int)
    print(f"Audited healthy FPs used: {len(audit_base):,}")
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
        "version": "v5",
        "condition": "thyroid",
        "algorithm": "LogisticRegression expanded healthy-FP hard-neg v5",
        "data_source": DATA_PATH.name,
        "audit_sources": [str(path.relative_to(_ROOT)) for path in AUDIT_PATHS],
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
        "recommended_threshold_criterion": "Chosen to keep the current strict thyroid surface threshold while training directly against audited healthy false positives.",
        "train_recall_at_recommended_threshold": recall_rec,
        "train_precision_at_recommended_threshold": precision_rec,
        "hard_negative_leak_at_recommended_threshold": hard_neg_leak,
        "pipeline_steps": [
            "SimpleImputer(strategy=median, add_indicator=True)",
            "LogisticRegression(L2, class_weight=balanced, C=0.45)",
        ],
        "changes_from_v4": [
            "Expanded hard negatives to include both the gated-v2 residual healthy FPs and the seven healthy FPs reintroduced by v4",
            "Moved back closer to the validated v2 feature shape",
            "Restored pulse as a thyroid-shaped anchor",
            "Reduced reliance on the broader v4 feature expansion",
        ],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    meta_path.write_text(json.dumps(metadata, indent=2) + "\n")

    print(f"Saved artifact: {artifact_path}")
    print(f"Saved metadata: {meta_path}")


if __name__ == "__main__":
    main()
