# Thyroid Healthy False Positive Audit

- Source run: `evals/results/layer1_20260331_073956.json`
- Cohort: `evals/cohort/nhanes_balanced_760.json`
- Git SHA: `6344d21a034b351c1a454ae49d3bbe06d6509582`
- Runtime artifact: `thyroid_lr_hardneg_v4.joblib`
- User-facing threshold: `0.75`
- Healthy profiles: `100`
- Healthy thyroid false positives: `7`
- Healthy flag rate: `7.0%`

## Most Enriched Patterns

| Pattern | Flagged | FP share | Healthy baseline | Baseline share | Enrichment |
|---|---:|---:|---:|---:|---:|
| age_45_plus | 6 | 85.7% | 24 | 24.0% | 3.57x |
| poor_health | 4 | 57.1% | 32 | 32.0% | 1.79x |
| high_cholesterol | 4 | 57.1% | 18 | 18.0% | 3.17x |
| high_med_count | 3 | 42.9% | 5 | 5.0% | 8.57x |
| short_sleep | 2 | 28.6% | 6 | 6.0% | 4.76x |
| no_alcohol | 2 | 28.6% | 74 | 74.0% | 0.39x |

## Most Common Pattern Combos

| Combo | Count |
|---|---:|
| older+polypharmacy | 2 |

## Highest-Score Healthy False Positives

| Profile | Score | Age | Gender | Fatigue | Sleep trouble | Sleep hours | Meds | General health | Combos |
|---|---:|---:|---|---:|---:|---:|---:|---:|---|
| NHANES-C-21502 | 0.9719 | 84.0 | Male | 0.8 | 2.0 | 6.4 | 7.0 | 4.0 | older+polypharmacy |
| NHANES-C-27455 | 0.8454 | 36.0 | Male | 0.6 | 2.0 | 7.3 | 7.0 | 3.0 |  |
| NHANES-C-29195 | 0.8342 | 72.0 | Male | 0.3 | 2.0 | 6.6 | 3.0 | 1.0 |  |
| NHANES-C-27418 | 0.8335 | 85.0 | Male | 0.5 | 2.0 | 6.6 | 1.0 | 3.0 |  |
| NHANES-C-28207 | 0.7973 | 75.0 | Male | 0.0 | 2.0 | 6.3 | 2.0 | 1.0 |  |
| NHANES-C-30520 | 0.7713 | 63.0 | Male | 0.1 | 2.0 | 6.6 | 5.0 | 2.0 | older+polypharmacy |
| NHANES-C-28473 | 0.7529 | 76.0 | Male | 0.4 | 2.0 | 6.8 | 1.0 | 3.0 |  |
