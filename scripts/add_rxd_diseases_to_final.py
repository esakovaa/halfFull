import pandas as pd

print("Loading data...")
df = pd.read_csv('data/processed/nhanes_merged_adults_final.csv', low_memory=False)
rxd = pd.read_sas('data/processed/P_RXQ_RX.xpt', format='xport', encoding='utf-8')

print(f"Final dataset shape: {df.shape}")
print(f"RXD raw shape: {rxd.shape}")

# ── 1. Build per-SEQN comma-separated disease list ─────────────────────────
long = rxd[['SEQN', 'RXDRSD1', 'RXDRSD2', 'RXDRSD3']].melt(
    id_vars='SEQN', value_name='disease'
).drop(columns='variable')

long['disease'] = long['disease'].str.strip()
long = long[long['disease'].notna() & (long['disease'] != '')]

# Deduplicate per person, then join into comma-separated string
seqn_diseases = (
    long.drop_duplicates(subset=['SEQN', 'disease'])
    .groupby('SEQN')['disease']
    .agg(lambda x: ', '.join(sorted(set(x))))
    .reset_index()
    .rename(columns={'disease': 'rxd_disease_list'})
)

print(f"SEQNs with disease list: {len(seqn_diseases):,}")

# ── 2. Merge into final dataset ─────────────────────────────────────────────
df['SEQN'] = df['SEQN'].astype(float)
seqn_diseases['SEQN'] = seqn_diseases['SEQN'].astype(float)

df = df.merge(seqn_diseases, on='SEQN', how='left')
print(f"After merge — shape: {df.shape}")
print(f"rxd_disease_list non-null: {df['rxd_disease_list'].notna().sum():,}")

# ── 3. Helper: check if substring appears in rxd_disease_list ────────────────
def has_disease(series, keyword):
    """Case-insensitive substring match in rxd_disease_list."""
    return series.str.contains(keyword, case=False, na=False)

# ── 4. Update sleep_disorder ──────────────────────────────────────────────────
# Set to 1 if originally 0 but Insomnia or Sleep disorder mentioned
sleep_via_rxd = has_disease(df['rxd_disease_list'], 'Insomnia') | \
                has_disease(df['rxd_disease_list'], 'Sleep disorder')

was_zero = df['sleep_disorder'] == 0
n_flipped = (was_zero & sleep_via_rxd).sum()
df['sleep_disorder'] = ((df['sleep_disorder'] == 1) | sleep_via_rxd).astype(int)
print(f"\nsleep_disorder: {n_flipped} additional positives from rxd_disease_list")
print(f"  New total positives: {df['sleep_disorder'].sum():,}")

# ── 5. Add myalgia ────────────────────────────────────────────────────────────
df['myalgia'] = has_disease(df['rxd_disease_list'], 'Myalgia').astype(int)
print(f"\nmyalgia positives: {df['myalgia'].sum():,}")

# ── 6. Add anxiety ────────────────────────────────────────────────────────────
df['anxiety'] = has_disease(df['rxd_disease_list'], 'Anxiety disorder').astype(int)
print(f"anxiety positives: {df['anxiety'].sum():,}")

# ── 7. Add depression ─────────────────────────────────────────────────────────
df['depression'] = has_disease(df['rxd_disease_list'], 'depressive disorder').astype(int)
print(f"depression positives: {df['depression'].sum():,}")

# ── 8. Verify disease columns are all at the end ─────────────────────────────
disease_cols = [
    # original 15
    'anemia', 'diabetes', 'thyroid', 'sleep_disorder', 'kidney',
    'hepatitis_bc', 'liver', 'heart_failure', 'coronary_heart',
    'emphysema_lungs', 'high_blood_pressure', 'high_cholesterol',
    'menopause', 'overweight', 'alcohol',
    # lab-derived 5
    'iron_deficiency', 'hepatic_insufficiency', 'electrolyte_imbalance',
    'infection_inflammation', 'CFS_suspect',
    # new from rxd
    'myalgia', 'anxiety', 'depression',
]

# Reorder: move rxd_disease_list + new disease cols to end
other_cols = [c for c in df.columns if c not in disease_cols + ['rxd_disease_list']]
df = df[other_cols + ['rxd_disease_list'] + disease_cols]

print(f"\nFinal dataset shape: {df.shape}")
print(f"Last 10 columns: {list(df.columns[-10:])}")

# ── 9. Save ───────────────────────────────────────────────────────────────────
out = 'data/processed/nhanes_merged_adults_final.csv'
df.to_csv(out, index=False)
print(f"\nSaved to {out}")

# ── 10. Summary table for all 23 disease cols ─────────────────────────────────
print("\n=== Updated disease prevalence (all 23 diseases) ===")
rows = []
for col in disease_cols:
    n_pos = int(df[col].sum())
    n_neg = int((df[col] == 0).sum())
    prev = round(n_pos / len(df) * 100, 1)
    rows.append({'disease': col, 'n_positive': n_pos, 'n_negative': n_neg, 'prevalence_%': prev})

summary = pd.DataFrame(rows).sort_values('n_positive', ascending=False).reset_index(drop=True)
summary.index += 1
print(summary.to_string())
