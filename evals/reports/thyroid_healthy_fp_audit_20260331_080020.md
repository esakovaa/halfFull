# Thyroid Healthy False Positive Audit

- Source run: `evals/results/layer1_20260331_075321.json`
- Cohort: `evals/cohort/nhanes_balanced_760.json`
- Git SHA: `6344d21a034b351c1a454ae49d3bbe06d6509582`
- Runtime artifact: `thyroid_lr_hardneg_v5.joblib`
- User-facing threshold: `0.75`
- Healthy profiles: `100`
- Healthy thyroid false positives: `3`
- Healthy flag rate: `3.0%`

## Most Enriched Patterns

| Pattern | Flagged | FP share | Healthy baseline | Baseline share | Enrichment |
|---|---:|---:|---:|---:|---:|
| poor_health | 3 | 100.0% | 32 | 32.0% | 3.12x |
| high_med_count | 2 | 66.7% | 5 | 5.0% | 13.33x |
| age_45_plus | 2 | 66.7% | 24 | 24.0% | 2.78x |
| high_cholesterol | 1 | 33.3% | 18 | 18.0% | 1.85x |
| short_sleep | 1 | 33.3% | 6 | 6.0% | 5.56x |
| no_alcohol | 1 | 33.3% | 74 | 74.0% | 0.45x |

## Most Common Pattern Combos

| Combo | Count |
|---|---:|
| older+polypharmacy | 1 |

## Highest-Score Healthy False Positives

| Profile | Score | Age | Gender | Fatigue | Sleep trouble | Sleep hours | Meds | General health | Combos |
|---|---:|---:|---|---:|---:|---:|---:|---:|---|
| NHANES-C-21502 | 0.9416 | 84.0 | Male | 0.8 | 2.0 | 6.4 | 7.0 | 4.0 | older+polypharmacy |
| NHANES-C-27455 | 0.7984 | 36.0 | Male | 0.6 | 2.0 | 7.3 | 7.0 | 3.0 |  |
| NHANES-C-27418 | 0.7690 | 85.0 | Male | 0.5 | 2.0 | 6.6 | 1.0 | 3.0 |  |
