import pandas as pd

# load Anna's questionnaire dataset
df = pd.read_csv("data/processed/merged_questionnaire.csv")

# rename the column to match the other datasets
df = df.rename(columns={"seqn___respondent_sequence_number": "SEQN"})

# convert SEQN to integer (remove .0)
df["SEQN"] = df["SEQN"].astype("Int64")

# save the corrected dataset
df.to_csv("data/processed/merged_questionnaire.csv", index=False)

print("SEQN column standardized.")
