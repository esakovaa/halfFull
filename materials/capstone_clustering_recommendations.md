# HalfFull Capstone: Clustering Layer Recommendations

## Main Recommendation

Do not treat the clustering layer as a generic unsupervised model over all 800 NHANES variables.

Instead, separate the problem into two spaces:

- `anchor features`: the limited set of features a real user can provide at inference time
- `enrichment features`: the wider NHANES-only feature space used after neighbour assignment to surface additional signals

This is the key design principle for making the clustering layer usable in the real product.

## Why This Matters

If clustering is trained on all 800 features, a real user with only about 80 available inputs cannot be placed into that space reliably. The model would depend on information the user never provides.

The better approach is:

1. learn neighbourhood structure using only shared inference-time features
2. assign the user using those same features
3. compute enrichments over the full NHANES profile of similar people

This supports the true product goal:

- use limited user input
- locate similar NHANES profiles
- project what else is statistically enriched among those similar profiles

## Recommendation On Normalization

Do not add a blanket `StandardScaler` on top of `final_normalized`.

The normalization script shows that `final_normalized` is already a hybrid clinical normalization pipeline:

- some columns are reference-normalized against clinical intervals
- some are sex/age-stratified z-scores
- some categorical or protected columns are left untouched

Therefore:

- `final_normalized` should be treated as the canonical clustering input representation
- train and inference should reuse the same saved normalizer contract
- any extra scaling after that should be justified only by benchmark results

## What The Normalization Script Revealed

The script in `scripts/normalize_final_dataset.py` does the following:

- drops dietary columns during normalization
- reference-normalizes many core labs using sex- and age-aware clinical rules
- z-scores continuous non-reference numeric columns within sex-age bands, with gender-only and global fallbacks
- leaves low-cardinality and protected fields untouched
- saves a fitted normalizer object for reuse

Implication:

- the cluster layer should not casually rescale all features again
- the preprocessing contract must stay identical between training and inference

## Recommended Clustering Architecture

### 1. Build The Anchor Feature Set

Use a cleaned version of the real product-time features.

This should include:

- labs that can realistically be entered or uploaded by users
- core questionnaire items that can be asked in-product
- a small set of demographic or derived features needed for interpretation

This anchor set should be the only input to cluster assignment.

### 2. Build Cluster Geometry On Anchor Features Only

Recommended benchmark candidates:

- HDBSCAN directly on selected normalized anchor features
- PCA followed by HDBSCAN
- UMAP with about 10 to 15 dimensions followed by HDBSCAN

Use 2D UMAP only for visualization, not as the main clustering space.

### 3. Compute Cluster Enrichments Using The Full NHANES Feature Space

For each cluster or local neighbourhood, compute:

- condition prevalence lift
- extra lab abnormalities
- non-model questionnaire patterns
- sleep, activity, lifestyle, and reproductive enrichments
- any other statistically concentrated factors from the broader NHANES table

These become the basis for the cluster fingerprint.

### 4. Return Separate Output Buckets

The user explicitly preferred separate buckets instead of one combined block.

Recommended cluster output structure:

- `conditions`
- `labs`
- `lifestyle_and_symptom_factors`

Each bucket should be phrased probabilistically, for example:

- people with similar profiles more often show X
- similar profiles are more likely to have Y
- this neighbourhood shows elevated prevalence of Z

## Recommendation On Downstream Use

The clustering layer should do both:

- provide explanatory enrichment
- softly influence the ranking / threshold layer

It should not hard-override the supervised model probabilities.

A good operational pattern is:

- use cluster outputs as auxiliary ranking evidence
- include cluster confidence or membership strength
- require the cluster layer to be neutral or helpful on top-5 coverage

This aligns with the `cluster coverage delta` metric.

## Recommended Cluster Fingerprint Fields

Each cluster fingerprint should contain:

- cluster id
- size
- membership strength statistics
- dominant conditions and prevalence
- condition lift versus the full cohort
- enriched abnormal labs
- enriched symptom or lifestyle factors
- notable enrichment-only NHANES variables
- example or prototype summaries
- any extended lab suggestions inferred from the neighbourhood

## Recommendation On Age And Sex In Anchor Features

Tradeoff:

- including age and sex directly can improve clinical realism
- excluding them reduces the risk of clusters becoming demographic buckets

Current recommendation:

- keep `age_years`
- keep one stable sex representation, preferably `gender_female`
- then evaluate whether clusters are over-driven by demographics

## Current State Of The Feature Matrix

The roadmap CSV was updated from the actual `models_normalized/*_metadata.json` files.

Current findings:

- there are 77 unique features used by the current 11 models
- the old matrix was missing:
  - `education_ord`
  - `gender_female`
  - `pregnancy_status_bin`
- a first-pass annotation layer was added to distinguish:
  - input bucket
  - anchor candidates
  - conditional follow-up logic
  - provisional cluster role

At the moment:

- 77 rows are marked as anchor candidates
- 52 rows are marked as enrichment-only or future
- legacy `gender` is excluded from the anchor because current metadata uses `gender_female`

## Recommended Next Cleanup Pass

The next pass on the matrix should finalize:

- `core_anchor`
- `conditional_anchor`
- `enrichment_only`
- `drop`

This should replace the current rough `anchor_v1` and `cluster_role_v1` labels with a more product-ready split.

## Recommendation On Clustering-Only Questions

The user is open to adding about 1 to 5 extra questions not currently covered by the supervised models if they improve clustering.

Best candidate domains for these additions:

- sleep quality or sleep fragmentation
- recent infection or inflammatory burden
- menstrual or hormonal change
- exercise intolerance or post-exertional fatigue
- dietary pattern relevant to iron, B12, or protein intake

These are attractive because they can improve neighbourhood quality without limiting the system to the current 11 disease models.

## Clarified Validation Label Concept

Condition labels should not be used as clustering inputs.

They should be held aside only for validation, such as:

- neighbour label consistency
- prevalence lift checks
- cluster interpretability checks

This means labels are for evaluation, not feature construction.

## Summary Of The Best Working Plan

1. Use the updated feature matrix as the source of truth for anchor versus enrichment design.
2. Finalize a clean anchor set representing only product-time features.
3. Train cluster geometry only on anchor features in `final_normalized`.
4. Attach full-NHANES enrichments after cluster assignment.
5. Output separate cluster buckets for conditions, labs, and lifestyle / symptom factors.
6. Feed the cluster layer into downstream ranking as a soft signal.
7. Evaluate with:
   - extended lab precision
   - cluster coverage delta
   - neighbour label consistency
