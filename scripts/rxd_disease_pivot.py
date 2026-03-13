import pandas as pd

df = pd.read_sas('data/processed/P_RXQ_RX.xpt', format='xport', encoding='utf-8')

# ── Long format: stack RXDRSD1/2/3 into one column ───────────────────────────
long = df[['SEQN','RXDRSD1','RXDRSD2','RXDRSD3']].melt(
    id_vars='SEQN', value_name='disease'
).drop(columns='variable')

long['disease'] = long['disease'].str.strip()
long = long[long['disease'].notna() & (long['disease'] != '')]

print(f"Total disease-medication mentions: {len(long):,}")
print(f"Unique disease strings: {long['disease'].nunique():,}")
print(f"Unique SEQNs with any disease listed: {long['SEQN'].nunique():,}")
print()

# ── Per-SEQN deduplicated disease list ───────────────────────────────────────
seqn_diseases = (
    long.groupby('SEQN')['disease']
    .agg(lambda x: sorted(set(x)))
    .reset_index()
    .rename(columns={'disease': 'disease_list'})
)
seqn_diseases['n_unique_diseases'] = seqn_diseases['disease_list'].str.len()

print("=== Per-SEQN disease list (first 15 rows) ===")
print(seqn_diseases.head(15).to_string(index=False))
print()

# ── Pivot: count unique people per disease ────────────────────────────────────
seqn_disease_unique = long.drop_duplicates(subset=['SEQN', 'disease'])
n_people_total = seqn_diseases['SEQN'].nunique()

pivot = (
    seqn_disease_unique['disease']
    .value_counts()
    .reset_index()
    .rename(columns={'disease': 'disease_name', 'count': 'n_people'})
)
pivot['pct_of_med_users'] = (pivot['n_people'] / n_people_total * 100).round(1)
pivot.index = range(1, len(pivot) + 1)

print(f"=== PIVOT TABLE: Unique person-level disease mentions ===")
print(f"(Universe: {n_people_total:,} people with at least one RXDRSD entry)\n")
pd.set_option('display.max_rows', 300)
pd.set_option('display.max_colwidth', 70)
pd.set_option('display.width', 120)
print(pivot.to_string())

# ── Save both outputs ─────────────────────────────────────────────────────────
seqn_diseases.to_csv('data/processed/rxd_seqn_disease_list.csv', index=False)
pivot.to_csv('data/processed/rxd_disease_pivot.csv')
print(f"\nSaved:\n  data/processed/rxd_seqn_disease_list.csv  ({len(seqn_diseases):,} rows)")
print(f"  data/processed/rxd_disease_pivot.csv  ({len(pivot)} diseases)")
