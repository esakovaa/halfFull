# Thyroid Healthy False Positive Audit

- Source run: `evals/results/layer1_20260331_072410.json`
- Cohort: `evals/cohort/nhanes_balanced_760.json`
- Git SHA: `6344d21a034b351c1a454ae49d3bbe06d6509582`
- Runtime artifact: `thyroid_lr_l2_reduced-12feat_v2.joblib`
- User-facing threshold: `0.75`
- Healthy profiles: `100`
- Healthy thyroid false positives: `5`
- Healthy flag rate: `5.0%`

## Most Enriched Patterns

| Pattern | Flagged | FP share | Healthy baseline | Baseline share | Enrichment |
|---|---:|---:|---:|---:|---:|
| poor_health | 5 | 100.0% | 32 | 32.0% | 3.12x |
| age_45_plus | 4 | 80.0% | 24 | 24.0% | 3.33x |
| high_med_count | 3 | 60.0% | 5 | 5.0% | 12.00x |
| no_alcohol | 2 | 40.0% | 74 | 74.0% | 0.54x |
| high_cholesterol | 1 | 20.0% | 18 | 18.0% | 1.11x |
| short_sleep | 1 | 20.0% | 6 | 6.0% | 3.33x |

## Most Common Pattern Combos

| Combo | Count |
|---|---:|
| older+polypharmacy | 2 |

## Highest-Score Healthy False Positives

| Profile | Score | Age | Gender | Fatigue | Sleep trouble | Sleep hours | Meds | General health | Combos |
|---|---:|---:|---|---:|---:|---:|---:|---:|---|
| NHANES-C-21502 | 0.9513 | 84.0 | Male | 0.8 | 2.0 | 6.4 | 7.0 | 4.0 | older+polypharmacy |
| NHANES-C-27418 | 0.8249 | 85.0 | Male | 0.5 | 2.0 | 6.6 | 1.0 | 3.0 |  |
| NHANES-C-23730 | 0.8126 | 69.0 | Male | 0.5 | 2.0 | 6.9 | 5.0 | 3.0 | older+polypharmacy |
| NHANES-C-23579 | 0.7864 | 73.0 | Male | 0.7 | 2.0 | 6.8 | 3.0 | 3.0 |  |
| NHANES-C-27455 | 0.7754 | 36.0 | Male | 0.6 | 2.0 | 7.3 | 7.0 | 3.0 |  |
