# Thyroid Healthy False Positive Audit

- Source run: `evals/results/layer1_20260331_004741.json`
- Cohort: `evals/cohort/nhanes_balanced_760.json`
- Git SHA: `6344d21a034b351c1a454ae49d3bbe06d6509582`
- Runtime artifact: `thyroid_lr_l2_reduced-12feat_v2.joblib`
- User-facing threshold: `0.75`
- Healthy profiles: `100`
- Healthy thyroid false positives: `3`
- Healthy flag rate: `3.0%`

## Most Enriched Patterns

| Pattern | Flagged | FP share | Healthy baseline | Baseline share | Enrichment |
|---|---:|---:|---:|---:|---:|
| age_45_plus | 3 | 100.0% | 24 | 24.0% | 4.17x |
| poor_health | 3 | 100.0% | 32 | 32.0% | 3.12x |
| high_med_count | 2 | 66.7% | 5 | 5.0% | 13.33x |
| no_alcohol | 2 | 66.7% | 74 | 74.0% | 0.90x |
| short_sleep | 1 | 33.3% | 6 | 6.0% | 5.56x |

## Most Common Pattern Combos

| Combo | Count |
|---|---:|
| older+polypharmacy | 2 |

## Highest-Score Healthy False Positives

| Profile | Score | Age | Gender | Fatigue | Sleep trouble | Sleep hours | Meds | General health | Combos |
|---|---:|---:|---|---:|---:|---:|---:|---:|---|
| NHANES-C-21502 | 0.9344 | 84.0 | Male | 0.8 | 2.0 | 6.4 | 7.0 | 4.0 | older+polypharmacy |
| NHANES-C-27418 | 0.7747 | 85.0 | Male | 0.5 | 2.0 | 6.6 | 1.0 | 3.0 |  |
| NHANES-C-23730 | 0.7599 | 69.0 | Male | 0.5 | 2.0 | 6.9 | 5.0 | 3.0 | older+polypharmacy |
