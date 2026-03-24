# HalfFull Capstone: Clustering Layer Brief

## Architecture Context

The HalfFull architecture has:

- A supervised ML models layer with 11 condition classifiers:
  - Thyroid
  - Sleep disorder
  - Prediabetes
  - Electrolytes
  - Kidney
  - Anemia
  - Liver
  - Hidden inflammation
  - Hepatitis B/C
  - Perimenopause
  - Iron deficiency
- A Bayesian update layer for questionnaire follow-up.
- A cluster layer for unsupervised neighbour matching.
- A threshold/ranking layer for top-condition selection.
- An LLM synthesis layer for clinical-style narrative output.
- A safety layer and final personalized fatigue report output.

The clustering layer is intended to complement the 11 supervised models, not replace them.

## Goal Of The Clustering Layer

Build an unsupervised clustering / neighbour-matching layer that:

- Places a user into a clinically meaningful neighbourhood.
- Surfaces condition co-occurrence beyond the 11 classifiers.
- Suggests extended labs or out-of-range signals not directly captured by the supervised models.
- Identifies broader statistically significant patterns across NHANES features, including questionnaire, lab, lifestyle, sleep, and reproductive signals.

The user can provide only a limited product-time feature set, roughly 80 features, while NHANES contains more than 800 features. The aim is to use the limited user inputs to position them near similar NHANES participants, then use the richer NHANES feature space of those neighbours to infer additional useful signals.

## Metrics To Evaluate The Cluster Layer

### 1. Extended Lab Precision

Definition:
Of the out-of-range labs the cluster suggests, what fraction are clinically meaningful, confirmed by a condition label or medical advisor review.

Target:
- At least 40%

Test:
- For synthetic users with known condition labels, check whether cluster-driven extended lab suggestions correlate with labs known to be associated with their true conditions.

### 2. Cluster Coverage Delta

Definition:
Whether adding the cluster layer increases top-5 coverage rate versus the models-only system.

Target:
- At least +3 percentage points
- Neutral at minimum
- The cluster layer should never hurt coverage

Test:
- Run a synthetic cohort with and without cluster signals entering the threshold step, then compare top-5 coverage.

### 3. Neighbour Label Consistency

Definition:
Within each cluster, what fraction of members share at least one condition label.

Target:
- At least 60% intra-cluster agreement on the dominant condition

Test:
- For each HDBSCAN cluster, compute the most common condition label among members and measure what percentage of members share it.

## Original Proposed Plan

### Step 1. Feature Preparation

- Use the merged NHANES dataframe from the existing pipeline.
- Use the same broad feature families as the ML layer:
  - labs
  - questionnaire responses
- Keep condition labels separate for validation.
- The preference is to include questionnaire features plus full labs, not labs-only.

Important note:
- The input file `final_normalized` is already normalized by sex and age.

### Step 2. Dimensionality Reduction With UMAP

- Use UMAP for lower-dimensional embedding.
- Use a 2D version for visualization.
- Use a higher-dimensional version, such as 10 to 15 dimensions, for clustering.
- Use the 2D view to show whether clinically meaningful groups appear, for example thyroid cases clustering together.

### Step 3. HDBSCAN Clustering

- Use HDBSCAN on the embedding.
- Tune `min_cluster_size` based on dataset size.
- Treat cluster `-1` points as valid noise or unusual profiles.

### Step 4. Build Cluster Fingerprints

For each cluster, compute a fingerprint summarizing:

- dominant conditions
- lab patterns
- clinically interesting out-of-range tendencies
- characteristic questionnaire / lifestyle patterns

Save cluster fingerprints as JSON for inference-time use.

### Step 5. Inference Function

For a new user:

- place them into the learned embedding
- identify their nearest cluster
- compute a membership strength score from 0 to 1
- pass the cluster fingerprint and strength into the downstream reasoning layer

### Step 6. Validation Before Wiring In

- Check whether clusters with high thyroid prevalence also show thyroid-related lab abnormalities.
- Adjust UMAP or HDBSCAN if clusters look random.
- Check intra-cluster label consistency and aim for 50 to 60% or better.

## Feature Selection Concerns Raised

### Why 800 Features Is Too Many For Clustering

The concern raised was that:

- 800 features is too high-dimensional
- UMAP and HDBSCAN often degrade with too many weak features
- 20 to 60 strong features may produce better clustering than a very wide noisy matrix

### Proposed Feature Selection Strategy

Three-pass suggestion:

1. Clinical relevance filter:
   - remove administrative variables
   - remove sampling weights
   - remove metadata
   - remove redundant derivative fields

2. Variance filter:
   - remove low-variance features

3. Importance filter:
   - use supervised Random Forest feature importance and keep top features

Suggested target:
- 40 to 60 features into UMAP

## How Clustering Was Intended To Cover More Than The ML Models

The idea was to use:

- the core ML model features for known-condition signal
- plus some additional NHANES variables outside the supervised models

Suggested extra domains:

- physical activity
- diet quality
- sleep quality
- recent illness
- reproductive / hormonal history
- body composition beyond BMI

The intended output was not just:

- "this looks like thyroid"

but richer cluster stories such as:

- "this group has high thyroid prevalence and also low dietary iron and disrupted sleep"

## Practical Starting Plan Originally Envisioned

- Day 1 morning: manually reduce features
- Day 1 afternoon: variance filter and RF feature ranking
- Day 2 morning: stratified normalization
- Day 2 afternoon: UMAP 2D visualization
- Day 3: HDBSCAN and fingerprint generation

The 2D visualization was intended as a checkpoint:

- if medically meaningful patterns appear, continue
- if the embedding is only a blob, revisit feature selection
