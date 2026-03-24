#!/usr/bin/env python3
"""
cohort_generator.py — Generates 600 synthetic user profiles for HalfFull evals.

Cohort composition (11 conditions):
    11 conditions × 50 profiles = 550
        25 positive  (strong signal, sigma=0.08)
        15 borderline (mu×0.6, sigma=0.12)
        10 negative  (healthy distribution, sigma=0.06)
    +  30 healthy controls  (no conditions, all sub-threshold)
    +  20 edge cases        (2–3 conflicting conditions)
    = 600 total

Profile ID format:
    SYN-{PREFIX}{INDEX:05d} where PREFIX is 3 uppercase chars
    e.g. SYN-CFS00001, SYN-HLT00001, SYN-EDG00001
    NOTE: The schema requires exactly 8 uppercase alphanumeric chars after "SYN-"
    so we use 3-char prefix + 5-digit zero-padded index = 8 chars total ✓

Usage:
    python cohort_generator.py [--seed 42] [--output PATH] [--validate]
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Path setup — allow running from any working directory
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVALS_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = EVALS_DIR / "schema" / "profile_schema.json"
OUTPUT_PATH = EVALS_DIR / "cohort" / "profiles.json"

sys.path.insert(0, str(PROJECT_ROOT))

try:
    from config import CONDITION_IDS
except ImportError:
    # Fallback if config.py is not available
    CONDITION_IDS = [
        "menopause", "perimenopause", "hypothyroidism", "kidney_disease",
        "sleep_disorder", "anemia", "iron_deficiency", "hepatitis",
        "prediabetes", "inflammation", "electrolyte_imbalance",
    ]

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install jsonschema")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# All symptoms in the vector
# ---------------------------------------------------------------------------
SYMPTOMS = [
    "fatigue_severity", "sleep_quality", "post_exertional_malaise",
    "joint_pain", "cognitive_impairment", "depressive_mood",
    "anxiety_level", "digestive_symptoms", "heat_intolerance", "weight_change",
]

# NOTE: weight_change is [-1, 1] — negative = weight loss, positive = weight gain
# All other symptoms are [0, 1] — 0 = absent/minimal, 1 = severe

# ---------------------------------------------------------------------------
# Condition-specific symptom profiles (clinically informed means for POSITIVE)
# ---------------------------------------------------------------------------
# Default healthy baseline for any unspecified symptom
HEALTHY_BASELINE = {s: 0.12 for s in SYMPTOMS}
HEALTHY_BASELINE["weight_change"] = 0.0

CONDITION_SYMPTOM_PROFILES: dict[str, dict[str, float]] = {
    "menopause": {
        "fatigue_severity":        0.72,
        "sleep_quality":           0.30,   # poor sleep
        "post_exertional_malaise": 0.45,
        "joint_pain":              0.55,
        "cognitive_impairment":    0.60,   # brain fog
        "depressive_mood":         0.55,
        "anxiety_level":           0.60,
        "digestive_symptoms":      0.30,
        "heat_intolerance":        0.85,   # hot flashes
        "weight_change":           0.30,   # weight gain
    },
    "perimenopause": {
        "fatigue_severity":        0.65,
        "sleep_quality":           0.35,
        "post_exertional_malaise": 0.40,
        "joint_pain":              0.45,
        "cognitive_impairment":    0.55,
        "depressive_mood":         0.50,
        "anxiety_level":           0.55,
        "digestive_symptoms":      0.28,
        "heat_intolerance":        0.75,   # night sweats / hot flashes
        "weight_change":           0.25,
    },
    "hypothyroidism": {
        "fatigue_severity":        0.78,
        "sleep_quality":           0.40,
        "post_exertional_malaise": 0.55,
        "joint_pain":              0.50,
        "cognitive_impairment":    0.55,
        "depressive_mood":         0.55,
        "anxiety_level":           0.30,
        "digestive_symptoms":      0.35,
        "heat_intolerance":        0.75,   # cold intolerance (inverted: high = intolerant)
        "weight_change":           0.45,   # weight gain
    },
    "kidney_disease": {
        "fatigue_severity":        0.70,
        "sleep_quality":           0.38,
        "post_exertional_malaise": 0.60,
        "joint_pain":              0.45,
        "cognitive_impairment":    0.50,
        "depressive_mood":         0.45,
        "anxiety_level":           0.40,
        "digestive_symptoms":      0.60,   # nausea, anorexia
        "heat_intolerance":        0.35,
        "weight_change":           -0.20,  # unintentional weight loss
    },
    "sleep_disorder": {
        "fatigue_severity":        0.80,
        "sleep_quality":           0.15,   # very poor sleep
        "post_exertional_malaise": 0.60,
        "joint_pain":              0.30,
        "cognitive_impairment":    0.65,
        "depressive_mood":         0.55,
        "anxiety_level":           0.60,
        "digestive_symptoms":      0.25,
        "heat_intolerance":        0.25,
        "weight_change":           0.15,
    },
    "anemia": {
        "fatigue_severity":        0.82,
        "sleep_quality":           0.40,
        "post_exertional_malaise": 0.70,
        "joint_pain":              0.25,
        "cognitive_impairment":    0.50,
        "depressive_mood":         0.45,
        "anxiety_level":           0.35,
        "digestive_symptoms":      0.35,
        "heat_intolerance":        0.40,
        "weight_change":           -0.15,
    },
    "iron_deficiency": {
        "fatigue_severity":        0.75,
        "sleep_quality":           0.38,
        "post_exertional_malaise": 0.65,
        "joint_pain":              0.20,
        "cognitive_impairment":    0.45,
        "depressive_mood":         0.40,
        "anxiety_level":           0.35,
        "digestive_symptoms":      0.30,
        "heat_intolerance":        0.30,
        "weight_change":           -0.10,
    },
    "hepatitis": {
        "fatigue_severity":        0.75,
        "sleep_quality":           0.35,
        "post_exertional_malaise": 0.65,
        "joint_pain":              0.50,
        "cognitive_impairment":    0.40,
        "depressive_mood":         0.50,
        "anxiety_level":           0.40,
        "digestive_symptoms":      0.80,   # nausea, jaundice-related symptoms
        "heat_intolerance":        0.30,
        "weight_change":           -0.25,
    },
    "prediabetes": {
        "fatigue_severity":        0.65,
        "sleep_quality":           0.38,
        "post_exertional_malaise": 0.45,
        "joint_pain":              0.40,
        "cognitive_impairment":    0.45,
        "depressive_mood":         0.40,
        "anxiety_level":           0.38,
        "digestive_symptoms":      0.40,
        "heat_intolerance":        0.35,
        "weight_change":           0.40,   # overweight tendency
    },
    "inflammation": {
        "fatigue_severity":        0.70,
        "sleep_quality":           0.35,
        "post_exertional_malaise": 0.60,
        "joint_pain":              0.75,   # key marker
        "cognitive_impairment":    0.45,
        "depressive_mood":         0.45,
        "anxiety_level":           0.40,
        "digestive_symptoms":      0.50,
        "heat_intolerance":        0.45,
        "weight_change":           0.20,
    },
    "electrolyte_imbalance": {
        "fatigue_severity":        0.68,
        "sleep_quality":           0.38,
        "post_exertional_malaise": 0.55,
        "joint_pain":              0.45,
        "cognitive_impairment":    0.55,
        "depressive_mood":         0.42,
        "anxiety_level":           0.50,
        "digestive_symptoms":      0.55,
        "heat_intolerance":        0.40,
        "weight_change":           -0.10,
    },
}

# 3-char uppercase prefix for each condition (used in profile IDs)
CONDITION_PREFIX: dict[str, str] = {
    "menopause":            "MNP",
    "perimenopause":        "PMN",
    "hypothyroidism":       "THY",
    "kidney_disease":       "KDN",
    "sleep_disorder":       "SLP",
    "anemia":               "ANM",
    "iron_deficiency":      "IRN",
    "hepatitis":            "HEP",
    "prediabetes":          "PRD",
    "inflammation":         "INF",
    "electrolyte_imbalance":"ELC",
}

# Lab reference ranges [mean, std] for [normal, positive_shift]
# format: { lab: [normal_mean, normal_std, positive_mean_shift] }
LAB_REFERENCE: dict[str, tuple[float, float, float]] = {
    "tsh":        (2.0,  0.8,  5.5),    # elevated in hypothyroidism
    "ferritin":   (80.0, 30.0, 15.0),   # low in iron deficiency / anemia
    "hemoglobin": (13.5, 1.2,  10.5),   # low in anemia
    "crp":        (1.0,  0.5,  8.0),    # elevated in inflammation / hepatitis
    "vitamin_d":  (35.0, 10.0, 18.0),   # low in many conditions
    "hba1c":      (5.2,  0.3,  6.5),    # elevated in prediabetes
    "cortisol":   (15.0, 4.0,  8.0),    # low in fatigue conditions
}

# Which labs are most affected (shifted) per condition
CONDITION_LAB_SHIFT: dict[str, list[str]] = {
    "menopause":            ["cortisol", "vitamin_d"],
    "perimenopause":        ["cortisol", "vitamin_d"],
    "hypothyroidism":       ["tsh", "vitamin_d"],
    "kidney_disease":       ["crp", "hemoglobin"],
    "sleep_disorder":       ["cortisol"],
    "anemia":               ["hemoglobin", "ferritin"],
    "iron_deficiency":      ["ferritin", "hemoglobin"],
    "hepatitis":            ["crp", "vitamin_d"],
    "prediabetes":          ["hba1c", "vitamin_d"],
    "inflammation":         ["crp", "vitamin_d"],
    "electrolyte_imbalance":["crp"],
}


def _make_profile_id(prefix: str, index: int) -> str:
    """Generate a valid SYN-XXXXXXXX profile ID (8 alphanumeric uppercase chars)."""
    # prefix is 3 chars, index is zero-padded to 5 digits → total 8 chars
    return f"SYN-{prefix}{index:05d}"


def _generate_demographics(rng: random.Random, nprng: np.random.Generator, condition: str | None = None) -> dict:
    """Generate demographically plausible values."""
    # Age distribution varies by condition
    if condition in ("menopause", "perimenopause"):
        age = int(np.clip(nprng.normal(52, 6), 40, 65))
        sex = "F"
    elif condition in ("kidney_disease", "hepatitis"):
        age = int(np.clip(nprng.normal(55, 12), 30, 80))
        sex = rng.choice(["M", "F"])
    else:
        age = int(np.clip(nprng.normal(45, 15), 18, 85))
        sex = rng.choices(["M", "F", "F", "F"], weights=[1, 1, 1, 1])[0]  # slight female skew (NHANES)

    bmi = round(float(np.clip(nprng.normal(27.5, 5.5), 16.0, 55.0)), 1)
    smoking_status = rng.choices(
        ["never", "former", "current"], weights=[55, 30, 15]
    )[0]
    activity_level = rng.choices(
        ["sedentary", "low", "moderate", "high"], weights=[30, 30, 30, 10]
    )[0]

    return {
        "age": age,
        "sex": sex,
        "bmi": bmi,
        "smoking_status": smoking_status,
        "activity_level": activity_level,
    }


def _clip_symptom(value: float, symptom: str) -> float:
    """Clip symptom to valid range (weight_change is [-1,1]; others [0,1])."""
    if symptom == "weight_change":
        return float(np.clip(value, -1.0, 1.0))
    return float(np.clip(value, 0.0, 1.0))


def _generate_symptom_vector(
    profile_type: str,
    condition: str | None,
    nprng: np.random.Generator,
) -> dict[str, float]:
    """Generate symptom scores based on profile type and condition."""
    mu_base = CONDITION_SYMPTOM_PROFILES.get(condition, HEALTHY_BASELINE) if condition else HEALTHY_BASELINE
    vector: dict[str, float] = {}

    for symptom in SYMPTOMS:
        mu = mu_base.get(symptom, HEALTHY_BASELINE.get(symptom, 0.12))

        if profile_type == "positive":
            raw = nprng.normal(mu, 0.08)
        elif profile_type == "borderline":
            raw = nprng.normal(mu * 0.6, 0.12)
        elif profile_type == "negative":
            # Healthy distribution regardless of condition
            raw = nprng.normal(0.12, 0.06)
        elif profile_type == "healthy":
            raw = nprng.normal(0.12, 0.06)
        else:
            # edge — handled separately
            raw = nprng.normal(mu, 0.08)

        vector[symptom] = round(_clip_symptom(raw, symptom), 4)

    return vector


def _generate_edge_symptom_vector(
    conditions: list[str],
    nprng: np.random.Generator,
) -> dict[str, float]:
    """Average mu vectors for 2–3 conditions, add noise sigma=0.15."""
    avg_mu: dict[str, float] = {s: 0.0 for s in SYMPTOMS}

    for cond in conditions:
        mu_map = CONDITION_SYMPTOM_PROFILES.get(cond, HEALTHY_BASELINE)
        for symptom in SYMPTOMS:
            avg_mu[symptom] += mu_map.get(symptom, HEALTHY_BASELINE.get(symptom, 0.12))

    for symptom in SYMPTOMS:
        avg_mu[symptom] /= len(conditions)

    vector: dict[str, float] = {}
    for symptom in SYMPTOMS:
        raw = nprng.normal(avg_mu[symptom], 0.15)
        vector[symptom] = round(_clip_symptom(raw, symptom), 4)

    return vector


def _generate_lab_values(
    profile_type: str,
    condition: str | None,
    nprng: np.random.Generator,
) -> dict[str, float]:
    """Generate lab values. Positive profiles have condition-specific shifts."""
    labs: dict[str, float] = {}
    shifted = CONDITION_LAB_SHIFT.get(condition, []) if (condition and profile_type == "positive") else []

    for lab, (normal_mean, normal_std, positive_mean) in LAB_REFERENCE.items():
        if lab in shifted:
            raw = nprng.normal(positive_mean, normal_std)
        else:
            raw = nprng.normal(normal_mean, normal_std)
        # Ensure positive values (labs can't be negative)
        labs[lab] = round(max(0.1, float(raw)), 2)

    return labs


def _make_ground_truth(
    profile_type: str,
    condition: str | None,
    edge_conditions: list[str] | None = None,
) -> dict:
    """Build the ground_truth block."""
    if profile_type == "healthy":
        return {"expected_conditions": [], "notes": "Healthy control — no condition expected"}

    if profile_type == "edge" and edge_conditions:
        return {
            "expected_conditions": [
                {"condition_id": cid, "confidence": "medium", "rank": i + 1}
                for i, cid in enumerate(edge_conditions)
            ],
            "notes": f"Edge case with conflicting signals for: {', '.join(edge_conditions)}",
        }

    if not condition:
        return {"expected_conditions": []}

    confidence_map = {"positive": "high", "borderline": "medium", "negative": "low"}
    confidence = confidence_map.get(profile_type, "low")

    expected = [{"condition_id": condition, "confidence": confidence, "rank": 1}]
    if profile_type == "negative":
        expected = []  # negative = ruled out

    return {
        "expected_conditions": expected,
        "notes": f"{profile_type.capitalize()} profile for {condition}",
    }


def generate_profile(
    profile_type: str,
    condition: str | None,
    prefix: str,
    index: int,
    rng: random.Random,
    nprng: np.random.Generator,
    edge_conditions: list[str] | None = None,
) -> dict:
    """Build a single complete profile dict."""
    has_labs = rng.random() < 0.40

    if profile_type == "edge" and edge_conditions:
        symptom_vector = _generate_edge_symptom_vector(edge_conditions, nprng)
    else:
        symptom_vector = _generate_symptom_vector(profile_type, condition, nprng)

    lab_values = _generate_lab_values(profile_type, condition, nprng) if has_labs else None
    quiz_path = "hybrid" if lab_values is not None else "full"

    profile = {
        "profile_id":       _make_profile_id(prefix, index),
        "profile_type":     profile_type,
        "target_condition": condition if condition else "",
        "demographics":     _generate_demographics(rng, nprng, condition),
        "symptom_vector":   symptom_vector,
        "lab_values":       lab_values,
        "quiz_path":        quiz_path,
        "ground_truth":     _make_ground_truth(profile_type, condition, edge_conditions),
        "metadata": {
            "generated_by":    "cohort_generator.py",
            "generation_date": date.today().isoformat(),
            "source_basis":    "NHANES 2017-2019 distributions",
            "eval_layer":      [1],
        },
    }

    return profile


def generate_cohort(seed: int = 42) -> list[dict]:
    """Generate the full 600-profile cohort."""
    rng = random.Random(seed)
    nprng = np.random.default_rng(seed)

    profiles: list[dict] = []

    # -----------------------------------------------------------------------
    # Per-condition profiles: 25 positive + 15 borderline + 10 negative = 50
    # -----------------------------------------------------------------------
    global_index = 0
    for condition in CONDITION_IDS:
        prefix = CONDITION_PREFIX.get(condition, condition[:3].upper())
        cond_index = 0

        # 25 positive
        for _ in range(25):
            cond_index += 1
            global_index += 1
            profiles.append(generate_profile(
                "positive", condition, prefix, cond_index, rng, nprng
            ))

        # 15 borderline
        for _ in range(15):
            cond_index += 1
            global_index += 1
            profiles.append(generate_profile(
                "borderline", condition, prefix, cond_index, rng, nprng
            ))

        # 10 negative
        for _ in range(10):
            cond_index += 1
            global_index += 1
            profiles.append(generate_profile(
                "negative", condition, prefix, cond_index, rng, nprng
            ))

    # -----------------------------------------------------------------------
    # 30 healthy controls
    # -----------------------------------------------------------------------
    for i in range(1, 31):
        profiles.append(generate_profile(
            "healthy", None, "HLT", i, rng, nprng
        ))

    # -----------------------------------------------------------------------
    # 20 edge cases (2–3 conflicting conditions)
    # -----------------------------------------------------------------------
    for i in range(1, 21):
        n_conditions = rng.choice([2, 2, 3])  # 2/3 split weighted toward 2
        edge_conditions = rng.sample(CONDITION_IDS, n_conditions)
        profiles.append(generate_profile(
            "edge", None, "EDG", i, rng, nprng,
            edge_conditions=edge_conditions,
        ))

    assert len(profiles) == 600, f"Expected 600 profiles, got {len(profiles)}"
    return profiles


def validate_all(profiles: list[dict], schema: dict) -> None:
    """Validate every profile against the schema. Raises on first error."""
    validator = jsonschema.Draft7Validator(schema)
    for i, profile in enumerate(profiles):
        errors = list(validator.iter_errors(profile))
        if errors:
            error = errors[0]
            raise jsonschema.ValidationError(
                f"Profile {i} ({profile.get('profile_id', '?')}) failed validation: {error.message}\n"
                f"Path: {' -> '.join(str(p) for p in error.absolute_path)}"
            )


def print_summary(profiles: list[dict], seed: int, output: Path) -> None:
    """Print cohort generation summary table to stdout."""
    n_total = len(profiles)
    n_with_labs = sum(1 for p in profiles if p.get("lab_values") is not None)
    n_conditions = len(CONDITION_IDS)
    n_healthy = sum(1 for p in profiles if p["profile_type"] == "healthy")
    n_edge = sum(1 for p in profiles if p["profile_type"] == "edge")

    print()
    print("Cohort generation complete")
    print("──────────────────────────────")
    print(f"Total profiles:   {n_total}")
    print(f"Conditions:        {n_conditions}")
    print(f"Profiles/condition: 50  (25 pos / 15 borderline / 10 neg)")
    print(f"Healthy controls:  {n_healthy}")
    print(f"Edge cases:        {n_edge}")
    print(f"With lab values:  ~{n_with_labs} ({n_with_labs / n_total * 100:.0f}%)")
    print(f"Seed:              {seed}")
    print(f"Output: {output}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate 600 synthetic HalfFull evaluation profiles."
    )
    parser.add_argument("--seed",     type=int,  default=42,          help="Random seed (default: 42)")
    parser.add_argument("--output",   type=str,  default=str(OUTPUT_PATH), help="Output path for profiles.json")
    parser.add_argument("--validate", action="store_true",            help="Validate schema only — do not write output")
    args = parser.parse_args()

    output_path = Path(args.output)

    # Load schema
    if not SCHEMA_PATH.exists():
        print(f"ERROR: Schema not found at {SCHEMA_PATH}")
        sys.exit(1)

    with SCHEMA_PATH.open() as f:
        schema = json.load(f)

    logger.info("Generating cohort with seed=%d ...", args.seed)
    profiles = generate_cohort(seed=args.seed)

    logger.info("Validating %d profiles against schema ...", len(profiles))
    validate_all(profiles, schema)
    logger.info("All profiles passed schema validation")

    if args.validate:
        print(f"\n--validate mode: schema check passed for {len(profiles)} profiles. No file written.\n")
        return

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)

    print_summary(profiles, args.seed, output_path)


if __name__ == "__main__":
    main()
