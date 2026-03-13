"""
Updates disease_definitions.ipynb:
 - Bumps 20 → 23 in intro + setup
 - Updates sleep_disorder section with rxd enrichment note
 - Inserts 3 new disease sections: myalgia, anxiety, depression
 - Adds helper rxd_disease_list section before them
 - Updates summary cell to ALL_23
"""
import json, copy

NB = 'notebooks/disease_definitions.ipynb'

def code_cell(src):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": src}

def md_cell(src):
    return {"cell_type": "markdown", "metadata": {}, "source": src}

with open(NB) as f:
    nb = json.load(f)

cells = nb['cells']

# ── Cell 0: intro markdown — update 20 → 23, add 3 new rows ─────────────────
cells[0]['source'] = """\
# Disease Label Definitions

**Dataset:** `nhanes_merged_adults_final.csv`
**Population:** NHANES adults (n = 7,437)
**Total disease labels:** 23

This notebook documents the exact derivation formula for every binary disease column in the dataset.
Each label is `1` = condition present, `0` = absent.
Source column names refer to the **renamed columns** as they appear in the merged file (e.g. `mcq053___taking_treatment_for_anemia/past_3_mos`), with the original NHANES variable code noted alongside.

---

| # | Label | Type | Primary source |
|---|-------|------|----------------|
| 1 | `anemia` | Questionnaire | MCQ053 |
| 2 | `diabetes` | Questionnaire | DIQ010, DIQ160 |
| 3 | `thyroid` | Questionnaire | MCQ170M |
| 4 | `sleep_disorder` | Questionnaire + RXD | SLQ040, SLQ050, RXDRSD1-3 |
| 5 | `kidney` | Questionnaire + Lab | KIQ022, LBXSCR |
| 6 | `hepatitis_bc` | Questionnaire | HEQ010, HEQ030 |
| 7 | `liver` | Questionnaire | MCQ510A–F |
| 8 | `heart_failure` | Questionnaire | MCQ160B |
| 9 | `coronary_heart` | Questionnaire | MCQ160C |
| 10 | `emphysema_lungs` | Questionnaire | MCQ160P |
| 11 | `high_blood_pressure` | Questionnaire | BPQ020 |
| 12 | `high_cholesterol` | Questionnaire | BPQ080 |
| 13 | `menopause` | Questionnaire | RHQ305, RHD043, RHQ031 |
| 14 | `overweight` | Questionnaire | MCQ080 |
| 15 | `alcohol` | Questionnaire | ALQ151 |
| 16 | `iron_deficiency` | Lab | LBXFER |
| 17 | `hepatic_insufficiency` | Lab | LBXSATSI, LBXSASSI, LBXSGTSI |
| 18 | `electrolyte_imbalance` | Lab | LBXSNASI, LBXSKSI, LBXSCA |
| 19 | `infection_inflammation` | Lab | LBXWBCSI |
| 20 | `CFS_suspect` | Questionnaire + Lab | Multi-criterion |
| 21 | `myalgia` | RXD | RXDRSD1-3 keyword |
| 22 | `anxiety` | RXD | RXDRSD1-3 keyword |
| 23 | `depression` | RXD | RXDRSD1-3 keyword |
"""

# ── Cell 1: setup code — ALL_20 → ALL_23 ─────────────────────────────────────
cells[1]['source'] = """\
import pandas as pd
import numpy as np

df = pd.read_csv('../data/processed/nhanes_merged_adults_final.csv', low_memory=False)

ALL_23 = [
    'anemia','diabetes','thyroid','sleep_disorder','kidney',
    'hepatitis_bc','liver','heart_failure','coronary_heart',
    'emphysema_lungs','high_blood_pressure','high_cholesterol',
    'menopause','overweight','alcohol',
    'iron_deficiency','hepatic_insufficiency','electrolyte_imbalance',
    'infection_inflammation','CFS_suspect',
    'myalgia','anxiety','depression',
]

print(f'Dataset: {df.shape[0]:,} rows x {df.shape[1]:,} columns')
print(f'All 23 labels present: {all(c in df.columns for c in ALL_23)}')
print(f'rxd_disease_list present: {"rxd_disease_list" in df.columns}')
"""

# ── Cell 8: sleep_disorder markdown — add RXD enrichment note ────────────────
cells[8]['source'] = """\
---
## 4 · sleep_disorder

**Definition:** Clinically significant sleep-disordered breathing OR doctor-acknowledged sleep trouble
**— enriched** with medication prescription data (RXDRSD columns).

| NHANES variable | Renamed column | Question text |
|-----------------|----------------|---------------|
| SLQ040 | `slq040___how_often_do_you_snort_or_stop_breathing` | *"How often do you snort, gasp, or stop breathing?"* |
| SLQ050 | `slq050___ever_told_doctor_had_trouble_sleeping?` | *"Have you ever told a doctor that you have trouble sleeping?"* |
| RXDRSD1-3 | `rxd_disease_list` | Medication disease indications (P_RXQ_RX.xpt) |

**Formula:**
```
sleep_disorder = 1   if  SLQ040 ∈ {2, 3}                   # Occasionally or Frequently
                      OR SLQ050 == 1                         # Told doctor about sleep trouble
                      OR rxd_disease_list contains "Insomnia"
                      OR rxd_disease_list contains "Sleep disorder"
               = 0   otherwise
```

**SLQ040 encoding:** 0=Never · 1=Rarely · 2=Occasionally · 3=Frequently · 4=Almost always
**SLQ050 encoding:** 1=Yes · 2=No
**Notes:** SLQ120 (daytime sleepiness) was specified in the original definition but is **not present** in this dataset.
The RXD enrichment added **19** additional positives (people prescribed sleep medication whose questionnaire responses were borderline/missing).
"""

# ── Cell 9: sleep_disorder code — add rxd line ───────────────────────────────
cells[9]['source'] = """\
for col, name in [('slq040___how_often_do_you_snort_or_stop_breathing','SLQ040'),
                  ('slq050___ever_told_doctor_had_trouble_sleeping?','SLQ050')]:
    print(f'{name} value counts:')
    print(df[col].value_counts(dropna=False).sort_index().to_string())
    print()

# RXD enrichment check
rxd_sleep = df['rxd_disease_list'].str.contains('Insomnia|Sleep disorder', case=False, na=False)
print(f'People with Insomnia/Sleep disorder in RXD: {rxd_sleep.sum():,}')
print(f'sleep_disorder  ->  1: {int(df["sleep_disorder"].sum()):,}   0: {int((df["sleep_disorder"]==0).sum()):,}')
"""

# ── After cell 41 (CFS code, index 41), insert new sections ──────────────────
# New cells to insert (in order), before old cell 42 (summary separator)

new_md_rxd = md_cell("""\
---
## Supplementary · rxd_disease_list

**Source:** `P_RXQ_RX.xpt` — NHANES prescription medication file
**Column:** `rxd_disease_list` (added to final dataset)

Each person may appear multiple times in the raw file (once per medication).
`RXDRSD1`, `RXDRSD2`, `RXDRSD3` record up to 3 disease indications per medication.

**Derivation:**
```
1. Stack RXDRSD1/RXDRSD2/RXDRSD3 into long format (one row per disease mention)
2. Strip whitespace; drop empty / NaN values
3. Deduplicate per SEQN (unique diseases only)
4. Join with ", " separator → rxd_disease_list
5. Left-join onto final dataset on SEQN
```

**Coverage:** 3,529 of 7,437 adults have at least one RXDRSD entry.
Used directly as source for `myalgia`, `anxiety`, `depression`, and to enrich `sleep_disorder`.
""")

new_code_rxd = code_cell("""\
# Coverage and sample entries
n_with_rxd = df['rxd_disease_list'].notna().sum()
print(f'Adults with rxd_disease_list populated: {n_with_rxd:,} / {len(df):,}')
print()
print('Sample disease lists (first 8 non-null):')
sample = df[df['rxd_disease_list'].notna()][['SEQN','rxd_disease_list']].head(8)
for _, row in sample.iterrows():
    diseases = row['rxd_disease_list']
    print(f'  SEQN {int(row["SEQN"])}: {diseases[:100]}{"..." if len(diseases)>100 else ""}')
""")

new_md_myalgia = md_cell("""\
---
## 21 · myalgia

**Definition:** Person takes medication prescribed for myalgia (muscle pain).

| Source | Column | Description |
|--------|--------|-------------|
| P_RXQ_RX RXDRSD1-3 | `rxd_disease_list` | Comma-separated medication disease indications |

**Formula:**
```
myalgia = 1   if  rxd_disease_list contains "Myalgia"   (case-insensitive)
        = 0   otherwise (including no RXD data)
```

**Notes:** Captures myalgia as a medication indication. Does not capture people with muscle pain who are not on relevant prescriptions. NHANES questionnaire contains some musculoskeletal pain questions but no dedicated myalgia column.
""")

new_code_myalgia = code_cell("""\
myalgia_raw = df['rxd_disease_list'].str.contains('Myalgia', case=False, na=False)
print(f'myalgia  ->  1: {int(df["myalgia"].sum()):,}   0: {int((df["myalgia"]==0).sum()):,}')
# Show sample disease lists for myalgia=1
print()
print('Sample rxd_disease_list entries for myalgia=1:')
print(df[df['myalgia']==1]['rxd_disease_list'].head(5).to_string())
""")

new_md_anxiety = md_cell("""\
---
## 22 · anxiety

**Definition:** Person takes medication prescribed for an anxiety disorder.

| Source | Column | Description |
|--------|--------|-------------|
| P_RXQ_RX RXDRSD1-3 | `rxd_disease_list` | Comma-separated medication disease indications |

**Formula:**
```
anxiety = 1   if  rxd_disease_list contains "Anxiety disorder"   (case-insensitive)
        = 0   otherwise (including no RXD data)
```

**Notes:** Matches the specific ICD-10 description "Anxiety disorder, unspecified" used in NHANES RXD coding. Broader anxiety-spectrum conditions (panic disorder, PTSD, OCD) are coded separately and are **not** captured by this label. People managing anxiety with non-prescription approaches are also not captured.
""")

new_code_anxiety = code_cell("""\
print(f'anxiety  ->  1: {int(df["anxiety"].sum()):,}   0: {int((df["anxiety"]==0).sum()):,}')
print()
print('Top RXD disease strings co-occurring with anxiety=1 (excluding "Anxiety disorder"):')
anx_lists = df[df['anxiety']==1]['rxd_disease_list'].dropna()
from collections import Counter
co = Counter()
for lst in anx_lists:
    for d in lst.split(', '):
        if 'Anxiety disorder' not in d:
            co[d] += 1
for disease, cnt in co.most_common(10):
    print(f'  {cnt:>4}  {disease}')
""")

new_md_depression = md_cell("""\
---
## 23 · depression

**Definition:** Person takes medication prescribed for a depressive disorder.

| Source | Column | Description |
|--------|--------|-------------|
| P_RXQ_RX RXDRSD1-3 | `rxd_disease_list` | Comma-separated medication disease indications |

**Formula:**
```
depression = 1   if  rxd_disease_list contains "depressive disorder"   (case-insensitive)
           = 0   otherwise (including no RXD data)
```

**Notes:** Matches any string containing "depressive disorder" — covers both
*"Major depressive disorder, single episode, unspecified"* (n≈695 in pivot) and
*"Major depressive disorder, recurrent, unspecified"* (n≈39).
People managing depression without medication are not captured. PHQ-9 questionnaire items (DPQ010–DPQ090) in the dataset offer an alternative continuous depression severity measure.
""")

new_code_depression = code_cell("""\
print(f'depression  ->  1: {int(df["depression"].sum()):,}   0: {int((df["depression"]==0).sum()):,}')
print()
# Break down by which depressive disorder subtype
dep_lists = df[df['depression']==1]['rxd_disease_list'].dropna()
from collections import Counter
subtypes = Counter()
for lst in dep_lists:
    for d in lst.split(', '):
        if 'depressive' in d.lower():
            subtypes[d] += 1
print('Depression subtypes found in rxd_disease_list:')
for subtype, cnt in subtypes.most_common():
    print(f'  {cnt:>4}  {subtype}')
""")

# ── Insert all new cells after cell index 41 ─────────────────────────────────
insert_at = 42  # right before old cell 42 (summary separator)
new_cells = [
    new_md_rxd, new_code_rxd,
    new_md_myalgia, new_code_myalgia,
    new_md_anxiety, new_code_anxiety,
    new_md_depression, new_code_depression,
]
for i, cell in enumerate(new_cells):
    cells.insert(insert_at + i, cell)

# Old cell 42 is now at index 42+8 = 50  (summary markdown)
# Old cell 43 is now at index 43+8 = 51  (summary code)
idx_summary_md   = 50
idx_summary_code = 51

# ── Update summary markdown ───────────────────────────────────────────────────
cells[idx_summary_md]['source'] = """\
---
## Summary — All 23 Disease Labels
"""

# ── Update summary code ───────────────────────────────────────────────────────
cells[idx_summary_code]['source'] = """\
summary = []
for col in ALL_23:
    n1  = int(df[col].sum())
    n0  = int((df[col] == 0).sum())
    pct = n1 / (n0 + n1) * 100
    if col in ['iron_deficiency','hepatic_insufficiency',
               'electrolyte_imbalance','infection_inflammation']:
        typ = 'Lab'
    elif col in ['kidney','CFS_suspect']:
        typ = 'Q+Lab'
    elif col in ['sleep_disorder']:
        typ = 'Q+RXD'
    elif col in ['myalgia','anxiety','depression']:
        typ = 'RXD'
    else:
        typ = 'Questionnaire'
    summary.append({'disease': col, 'type': typ, 'n_positive': n1,
                    'n_negative': n0, 'prevalence_%': round(pct, 1)})

summary_df = pd.DataFrame(summary).sort_values('n_positive', ascending=False).reset_index(drop=True)
summary_df.index += 1
print(summary_df.to_string())
"""

nb['cells'] = cells
print(f'Total cells after edit: {len(cells)}')

with open(NB, 'w') as f:
    json.dump(nb, f, indent=1)
print('Notebook saved.')
