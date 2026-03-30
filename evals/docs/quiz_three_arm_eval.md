# Quiz-Only Three-Arm Eval

This eval compares three arms on the same stratified sample from [`nhanes_balanced_760.json`](C:\Users\Philipp\AIBootcamp\halfFull\evals\cohort\nhanes_balanced_760.json):

1. `models_only`
2. `medgemma_only`
3. `hybrid_top5`

## Defaults

- Cohort: real NHANES balanced benchmark
- Conditions: 12 only (`vitamin_b12_deficiency` excluded)
- Sampling: small stratified iteration set
- No Bayesian follow-up
- No KNN neighbour signals
- Primary metric: `recall@3`
- Guardrails:
  - healthy over-alert rate
  - per-condition neighbour false positives

## Why The Eval Mode Is Protected

`medgemma_only` intentionally bypasses the normal product flow by sending quiz answers to the existing [`/api/deep-analyze`](C:\Users\Philipp\AIBootcamp\halfFull\frontend\app\api\deep-analyze\route.ts) route **without ML scores**.

To avoid exposing that behaviour to normal users, the route only enables this mode when:

- the deployment defines `EVAL_MODE_SECRET`
- the request includes a matching `x-eval-mode-secret` header

This keeps the production user journey unchanged:

- normal users still go through the standard quiz -> ML scores -> Bayesian follow-up path
- eval traffic can reuse the same Vercel -> MedGemma connection safely on a preview deployment

## Command

```bash
python evals/run_quiz_three_arm_eval.py --base-url http://127.0.0.1:3000
```

Preview deployment example:

```bash
python evals/run_quiz_three_arm_eval.py \
  --base-url https://your-preview-deployment.vercel.app \
  --eval-secret your_eval_secret_here
```

Helpful flags:

- `--sample-per-condition 8`
- `--multi-per-condition 2`
- `--healthy-n 24`
- `--seed 42`
- `--timeout 180`
- `--eval-secret ...`
- `--dry-run`

## Arm Definitions

### `models_only`

Runs the 12 condition models locally on quiz-only inputs and ranks conditions by score.

### `medgemma_only`

Calls the live [`/api/deep-analyze`](C:\Users\Philipp\AIBootcamp\halfFull\frontend\app\api\deep-analyze\route.ts) route with quiz answers only. An eval-specific request mode keeps the product route but withholds ML scores from the MedGemma grounding prompt.

On protected preview deployments, this arm requires `--eval-secret` so the runner can send the matching `x-eval-mode-secret` header.

### `hybrid_top5`

Calls the same live route with quiz answers plus only the top-5 model scores.

## Outputs

- `evals/results/quiz_three_arm_YYYYMMDD_HHMMSS.json`
- `evals/reports/quiz_three_arm_YYYYMMDD_HHMMSS.md`

## Recommended Team Workflow

1. Push the eval branch to GitHub.
2. Let Vercel build a preview deployment for that branch.
3. Add the same `HF_API_TOKEN` already used by the app plus a new `EVAL_MODE_SECRET` on the preview environment.
4. Run a smoke test on a tiny sample:

```bash
python evals/run_quiz_three_arm_eval.py \
  --base-url https://your-preview-deployment.vercel.app \
  --eval-secret your_eval_secret_here \
  --sample-per-condition 1 \
  --multi-per-condition 0 \
  --healthy-n 3
```

5. Confirm that `medgemma_only` returns non-empty `top3_predictions` with `parse_success=true`.
6. Run the larger stratified sample or full benchmark once the smoke test is clean.

## Recommendation Logic

Per condition:

- `keep`: hybrid improves recall@3 over MedGemma-only without a large neighbour-FP penalty
- `maybe`: mixed result
- `skip_candidate`: MedGemma-only already performs better and the condition model does not recover the gap
