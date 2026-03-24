# HalfFull Evals

Synthetic evaluation pipeline for the HalfFull health-assessment project.
Generates 600 synthetic user profiles, runs them through the full inference
pipeline, and scores MedGemma responses against ground-truth labels.

## Module Purpose

The `evals/` directory provides:

- **Cohort generation** — 600 reproducible synthetic profiles across 11 conditions
- **Pipeline orchestration** — profile loading, quiz simulation, MedGemma inference, response parsing, scoring
- **Metrics & reporting** — cohort-level metrics, DoD checks, per-condition breakdowns, Markdown reports

## Prerequisites

```bash
pip install jsonschema>=4.17.0 tqdm>=4.64.0 numpy>=1.24.0 requests>=2.28.0
# or
pip install -r requirements_eval.txt
```

Python 3.10+ is required.

## Quick Start

**Step 1 — Generate the cohort (run once):**
```bash
python evals/cohort_generator.py --seed 42
```

**Step 2 — Validate profiles without writing output:**
```bash
python evals/cohort_generator.py --seed 42 --validate
```

**Step 3 — Run the eval pipeline (dry run, no inference):**
```bash
python evals/run_eval.py --dry-run --n 10
```

## CLI Flags — `run_eval.py`

| Flag | Default | Description |
|------|---------|-------------|
| `--layer` | `1` | Eval layer: `1` (condition-first) or `4` (co-morbidity) |
| `--n` | all | Number of profiles to evaluate |
| `--condition` | — | Filter to a single condition ID (e.g. `menopause`) |
| `--type` | — | Filter by profile type: `positive`, `borderline`, `negative`, `healthy`, `edge` |
| `--dry-run` | — | Load and validate profiles only, no inference |
| `--no-medgemma` | — | Skip MedGemma; run scoring with null outputs (fast iteration) |
| `--output` | `evals/results/` | Override results output directory |
| `--seed` | `42` | Random seed for sampling when `--n` < total |

## Results Paths

| Path | Contents |
|------|----------|
| `evals/cohort/profiles.json` | Generated synthetic cohort (gitignored) |
| `evals/results/eval_run_TIMESTAMP.json` | Per-profile results + aggregate metrics |
| `evals/reports/eval_report_TIMESTAMP.md` | Human-readable Markdown report |

## DoD Targets

All four metrics must pass for the eval to be considered green:

| Metric | Target | Direction |
|--------|--------|-----------|
| Cohort Top-1 Accuracy | >= 70% | higher is better |
| Hallucination Rate | < 5% | lower is better |
| Parse Success Rate | >= 95% | higher is better |
| Over-Alert Rate (healthy) | < 10% | lower is better |

## Cohort Composition

- 11 conditions x 50 profiles = 550 (25 positive / 15 borderline / 10 negative)
- 30 healthy controls
- 20 edge cases (2-3 conflicting conditions)
- **Total: 600 profiles**

## Further Reading

- `evals/docs/concept.md` — Technical architecture and design rationale
- `evals/docs/how_to_run_evals.md` — Step-by-step operational guide
