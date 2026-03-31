"""
build_thyroid_healthy_fp_audit.py
---------------------------------
ML-THYROID-03A: audit healthy thyroid false positives on the current runtime.

Outputs:
  - JSON payload with per-profile thyroid false positives and summary patterns
  - CSV hard-negative pack for follow-up retraining
  - Markdown summary report for quick review
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evals.archive.run_layer1_eval import _build_raw_inputs_from_nhanes
from models_normalized.model_runner import ModelRunner

DEFAULT_COHORT = ROOT / "evals" / "cohort" / "nhanes_balanced_760.json"
DEFAULT_RUN = ROOT / "evals" / "results" / "layer1_20260331_004741.json"
RESULTS_DIR = ROOT / "evals" / "results"
REPORTS_DIR = ROOT / "evals" / "reports"


def _pick(raw: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in raw:
            return raw[key]
    return None


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _gender_label(raw: dict[str, Any]) -> str | None:
    value = _pick(raw, "gender")
    if isinstance(value, str):
        label = value.strip().title()
        return label if label in {"Male", "Female"} else None
    if value is None:
        return None
    try:
        return {1: "Male", 2: "Female"}.get(int(float(value)))
    except (TypeError, ValueError):
        return None


def _score_all(runner: ModelRunner, raw_inputs: dict[str, Any]) -> dict[str, float]:
    ctx = {
        "gender": raw_inputs.get("gender"),
        "age_years": raw_inputs.get("age_years"),
        "rhq031_regular_periods_raw": _pick(
            raw_inputs,
            "rhq031___had_regular_periods_in_past_12_months",
            "rhq031_regular_periods",
        ),
        "raw_bmi": raw_inputs.get("bmi"),
        "raw_fasting_glucose": raw_inputs.get("fasting_glucose_mg_dl"),
        "raw_general_health": raw_inputs.get("huq010___general_health_condition"),
        "raw_med_count": raw_inputs.get("med_count"),
        "raw_sleep_trouble": raw_inputs.get("slq050___ever_told_doctor_had_trouble_sleeping?"),
    }
    feature_vectors = runner._get_normalizer().build_feature_vectors(raw_inputs)
    return runner.run_all_with_context(feature_vectors, patient_context=ctx)


def _age_bucket(age: float | None) -> str:
    if age is None:
        return "unknown"
    if age < 25:
        return "<25"
    if age < 45:
        return "25-44"
    if age < 65:
        return "45-64"
    return "65+"


def _pattern_flags(raw: dict[str, Any]) -> dict[str, bool]:
    age = _as_float(_pick(raw, "age_years"))
    fatigue = _as_float(_pick(raw, "dpq040___feeling_tired_or_having_little_energy", "dpq040_fatigue"))
    sleep_trouble = _as_float(_pick(raw, "slq050___ever_told_doctor_had_trouble_sleeping?", "slq050_sleep_trouble_doctor"))
    sleep_hours = _as_float(_pick(raw, "sld012___sleep_hours___weekdays_or_workdays", "sld012_sleep_hours_weekday"))
    health = _as_float(_pick(raw, "huq010___general_health_condition", "huq010_general_health"))
    overweight = _as_float(_pick(raw, "mcq080___doctor_ever_said_you_were_overweight", "doctor_said_overweight"))
    tried_weight_loss = _as_float(_pick(raw, "whq070___tried_to_lose_weight_in_past_year", "tried_to_lose_weight"))
    med_count = _as_float(_pick(raw, "med_count"))
    alcohol = _as_float(_pick(raw, "alq130___avg_#_alcoholic_drinks/day___past_12_mos", "alq130_avg_drinks_per_day"))
    pulse = _as_float(_pick(raw, "pulse_1"))
    chol = _as_float(_pick(raw, "total_cholesterol_mg_dl"))

    return {
        "female": _gender_label(raw) == "Female",
        "age_45_plus": age is not None and age >= 45,
        "fatigue_present": fatigue is not None and fatigue >= 1.0,
        "sleep_trouble": sleep_trouble is not None and sleep_trouble == 1.0,
        "short_sleep": sleep_hours is not None and sleep_hours < 6.5,
        "poor_health": health is not None and health >= 3.0,
        "overweight_history": overweight is not None and overweight == 1.0,
        "active_weight_loss": tried_weight_loss is not None and tried_weight_loss == 1.0,
        "high_med_count": med_count is not None and med_count >= 4.0,
        "no_alcohol": alcohol is not None and alcohol == 0.0,
        "low_pulse": pulse is not None and pulse < 60.0,
        "high_cholesterol": chol is not None and chol >= 200.0,
    }


def _combo_labels(flags: dict[str, bool]) -> list[str]:
    combos: list[str] = []
    if flags["female"] and flags["fatigue_present"]:
        combos.append("female+fatigue")
    if flags["female"] and flags["fatigue_present"] and flags["sleep_trouble"]:
        combos.append("female+fatigue+sleep")
    if flags["female"] and flags["high_med_count"] and flags["poor_health"]:
        combos.append("female+high_med+poor_health")
    if flags["fatigue_present"] and flags["sleep_trouble"]:
        combos.append("fatigue+sleep")
    if flags["overweight_history"] and flags["active_weight_loss"]:
        combos.append("weight_concern")
    if flags["no_alcohol"] and flags["female"]:
        combos.append("female+no_alcohol")
    if flags["age_45_plus"] and flags["high_med_count"]:
        combos.append("older+polypharmacy")
    if flags["low_pulse"] and flags["high_cholesterol"]:
        combos.append("metabolic_anchor")
    return combos


@dataclass
class AuditRow:
    profile_id: str
    thyroid_score: float
    age_years: float | None
    age_bucket: str
    gender: str | None
    fatigue: float | None
    sleep_trouble: float | None
    sleep_hours: float | None
    general_health: float | None
    med_count: float | None
    overweight_history: float | None
    tried_weight_loss: float | None
    alcohol_per_day: float | None
    pulse_1: float | None
    total_cholesterol_mg_dl: float | None
    combo_labels: list[str]
    raw_inputs: dict[str, Any]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort-path", type=Path, default=DEFAULT_COHORT)
    parser.add_argument("--run-json", type=Path, default=DEFAULT_RUN)
    args = parser.parse_args()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_data = json.loads(args.run_json.read_text())
    thyroid_meta = run_data["run_metadata"]["model_registry"]["thyroid"]
    threshold = float(thyroid_meta["user_facing_threshold"])
    git_sha = run_data["run_metadata"]["git_sha"]

    cohort = json.loads(args.cohort_path.read_text())
    runner = ModelRunner()

    healthy_rows: list[AuditRow] = []
    all_healthy_flags: list[dict[str, bool]] = []

    for profile in cohort:
        if profile.get("profile_type") != "healthy":
            continue

        raw = _build_raw_inputs_from_nhanes(profile)
        scores = _score_all(runner, raw)
        thyroid_score = float(scores.get("thyroid", 0.0))
        flags = _pattern_flags(raw)
        all_healthy_flags.append(flags)

        if thyroid_score < threshold:
            continue

        age_years = _as_float(_pick(raw, "age_years"))
        row = AuditRow(
            profile_id=profile["profile_id"],
            thyroid_score=round(thyroid_score, 4),
            age_years=age_years,
            age_bucket=_age_bucket(age_years),
            gender=_gender_label(raw),
            fatigue=_as_float(_pick(raw, "dpq040___feeling_tired_or_having_little_energy", "dpq040_fatigue")),
            sleep_trouble=_as_float(_pick(raw, "slq050___ever_told_doctor_had_trouble_sleeping?", "slq050_sleep_trouble_doctor")),
            sleep_hours=_as_float(_pick(raw, "sld012___sleep_hours___weekdays_or_workdays", "sld012_sleep_hours_weekday")),
            general_health=_as_float(_pick(raw, "huq010___general_health_condition", "huq010_general_health")),
            med_count=_as_float(_pick(raw, "med_count")),
            overweight_history=_as_float(_pick(raw, "mcq080___doctor_ever_said_you_were_overweight", "doctor_said_overweight")),
            tried_weight_loss=_as_float(_pick(raw, "whq070___tried_to_lose_weight_in_past_year", "tried_to_lose_weight")),
            alcohol_per_day=_as_float(_pick(raw, "alq130___avg_#_alcoholic_drinks/day___past_12_mos", "alq130_avg_drinks_per_day")),
            pulse_1=_as_float(_pick(raw, "pulse_1")),
            total_cholesterol_mg_dl=_as_float(_pick(raw, "total_cholesterol_mg_dl")),
            combo_labels=_combo_labels(flags),
            raw_inputs=raw,
        )
        healthy_rows.append(row)

    total_healthy = len(all_healthy_flags)
    pattern_counts = Counter()
    combo_counts = Counter()
    baseline_counts = Counter()

    for flags in all_healthy_flags:
        for label, active in flags.items():
            if active:
                baseline_counts[label] += 1

    for row in healthy_rows:
        row_flags = _pattern_flags(row.raw_inputs)
        for label, active in row_flags.items():
            if active:
                pattern_counts[label] += 1
        for combo in row.combo_labels:
            combo_counts[combo] += 1

    summary_patterns = []
    for label, count in pattern_counts.most_common():
        base = baseline_counts.get(label, 0)
        summary_patterns.append(
            {
                "pattern": label,
                "flagged_count": count,
                "flagged_rate_within_fp_set": round(count / max(len(healthy_rows), 1), 4),
                "healthy_baseline_count": base,
                "healthy_baseline_rate": round(base / max(total_healthy, 1), 4),
                "enrichment_ratio": round((count / max(len(healthy_rows), 1)) / max(base / max(total_healthy, 1), 1e-9), 2),
            }
        )

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_run_json": str(args.run_json.relative_to(ROOT)),
        "source_cohort": str(args.cohort_path.relative_to(ROOT)),
        "git_sha": git_sha,
        "thyroid_registry": thyroid_meta,
        "threshold": threshold,
        "n_healthy_profiles": total_healthy,
        "n_healthy_thyroid_false_positives": len(healthy_rows),
        "healthy_flag_rate": round(len(healthy_rows) / max(total_healthy, 1), 4),
        "summary_patterns": summary_patterns,
        "summary_combos": [{"combo": combo, "count": count} for combo, count in combo_counts.most_common()],
        "profiles": [
            {
                "profile_id": row.profile_id,
                "thyroid_score": row.thyroid_score,
                "age_years": row.age_years,
                "age_bucket": row.age_bucket,
                "gender": row.gender,
                "fatigue": row.fatigue,
                "sleep_trouble": row.sleep_trouble,
                "sleep_hours": row.sleep_hours,
                "general_health": row.general_health,
                "med_count": row.med_count,
                "overweight_history": row.overweight_history,
                "tried_weight_loss": row.tried_weight_loss,
                "alcohol_per_day": row.alcohol_per_day,
                "pulse_1": row.pulse_1,
                "total_cholesterol_mg_dl": row.total_cholesterol_mg_dl,
                "combo_labels": row.combo_labels,
                "raw_inputs": row.raw_inputs,
            }
            for row in sorted(healthy_rows, key=lambda x: x.thyroid_score, reverse=True)
        ],
    }

    json_path = RESULTS_DIR / f"thyroid_healthy_fp_audit_{timestamp}.json"
    csv_path = RESULTS_DIR / f"thyroid_healthy_fp_hard_negatives_{timestamp}.csv"
    md_path = REPORTS_DIR / f"thyroid_healthy_fp_audit_{timestamp}.md"

    json_path.write_text(json.dumps(payload, indent=2) + "\n")

    fieldnames = [
        "profile_id",
        "thyroid_score",
        "age_years",
        "age_bucket",
        "gender",
        "fatigue",
        "sleep_trouble",
        "sleep_hours",
        "general_health",
        "med_count",
        "overweight_history",
        "tried_weight_loss",
        "alcohol_per_day",
        "pulse_1",
        "total_cholesterol_mg_dl",
        "combo_labels",
    ]
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in payload["profiles"]:
            writer.writerow({**{k: row[k] for k in fieldnames if k != "combo_labels"}, "combo_labels": "|".join(row["combo_labels"])})

    lines = [
        "# Thyroid Healthy False Positive Audit",
        "",
        f"- Source run: `{args.run_json.relative_to(ROOT)}`",
        f"- Cohort: `{args.cohort_path.relative_to(ROOT)}`",
        f"- Git SHA: `{git_sha}`",
        f"- Runtime artifact: `{thyroid_meta['artifact']}`",
        f"- User-facing threshold: `{threshold:.2f}`",
        f"- Healthy profiles: `{total_healthy}`",
        f"- Healthy thyroid false positives: `{len(healthy_rows)}`",
        f"- Healthy flag rate: `{len(healthy_rows) / max(total_healthy, 1) * 100:.1f}%`",
        "",
        "## Most Enriched Patterns",
        "",
        "| Pattern | Flagged | FP share | Healthy baseline | Baseline share | Enrichment |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in summary_patterns[:8]:
        lines.append(
            f"| {item['pattern']} | {item['flagged_count']} | {item['flagged_rate_within_fp_set']*100:.1f}% | "
            f"{item['healthy_baseline_count']} | {item['healthy_baseline_rate']*100:.1f}% | {item['enrichment_ratio']:.2f}x |"
        )

    lines += [
        "",
        "## Most Common Pattern Combos",
        "",
        "| Combo | Count |",
        "|---|---:|",
    ]
    for combo, count in combo_counts.most_common(10):
        lines.append(f"| {combo} | {count} |")

    lines += [
        "",
        "## Highest-Score Healthy False Positives",
        "",
        "| Profile | Score | Age | Gender | Fatigue | Sleep trouble | Sleep hours | Meds | General health | Combos |",
        "|---|---:|---:|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in sorted(healthy_rows, key=lambda x: x.thyroid_score, reverse=True)[:10]:
        lines.append(
            f"| {row.profile_id} | {row.thyroid_score:.4f} | {row.age_years or ''} | {row.gender or ''} | "
            f"{row.fatigue if row.fatigue is not None else ''} | {row.sleep_trouble if row.sleep_trouble is not None else ''} | "
            f"{row.sleep_hours if row.sleep_hours is not None else ''} | {row.med_count if row.med_count is not None else ''} | "
            f"{row.general_health if row.general_health is not None else ''} | {', '.join(row.combo_labels)} |"
        )

    md_path.write_text("\n".join(lines) + "\n")

    print(json_path)
    print(csv_path)
    print(md_path)


if __name__ == "__main__":
    main()
