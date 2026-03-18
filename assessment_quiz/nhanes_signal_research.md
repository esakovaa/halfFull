# NHANES disease-signal research

This note summarizes how the supplied NHANES-based models can flag risk or pre-diagnostic signals using questionnaire and history features, plus where symptom-only screening is intrinsically weak.

This is not diagnostic advice. Several targets here, especially hidden inflammation, electrolyte imbalance, kidney disease, liver disease, and hepatitis B/C, are often silent or only weakly symptomatic until disease is established.

## NHANES fit

- Your merged dataset supports the target conditions mainly through the NHANES Medical Conditions (`MCQ`), Kidney Conditions / Urology (`KIQ`), Sleep (`SLQ` / `SLD`), Reproductive Health (`RHQ`), Hepatitis (`HEQ`), Blood Pressure / Cholesterol (`BPQ`), Diabetes (`DIQ`), alcohol (`ALQ`), smoking (`SMQ` / `SMD`), weight history (`WHQ`), occupation (`OCQ` / `OCD`), and broad laboratory components.
- For menopause, sleep disorder, kidney, prediabetes, and hepatitis/liver risk, NHANES has good questionnaire coverage.
- For anemia, hidden inflammation, electrolyte imbalance, and hepatic insufficiency, NHANES symptoms help, but laboratory variables remain the stronger signal source.

## Menopause

- Research take: Best questionnaire flags are age 45 to 55, irregular or absent periods, urinary symptoms, sleep disruption, and prior pregnancy / reproductive history context.
- NHANES coverage: Strong NHANES fit through RHQ menstrual history, KIQ urinary items, blood pressure history, and activity / clinician-advice questions.
- Useful non-lab flags:
  - Irregular or absent menstrual periods over the last 12 months.
  - Hot flashes or night sweats are high-yield net-new questions not present in the supplied model features.
  - Trouble sleeping and urinary urgency / leakage raise probability in perimenopausal patients.
  - Age under 40 with menopausal symptoms should be treated as premature ovarian insufficiency / early menopause workup, not routine menopause.
- Questionnaire/history features already in your models: age_years, bpq020___ever_told_you_had_high_blood_pressure, bpq040a___taking_prescription_for_hypertension, gender, kiq005___how_often_have_urinary_leakage?, kiq042___leak_urine_during_physical_activities?, kiq044___urinated_before_reaching_the_toilet?, kiq450___how_frequently_does_this_occur?, mcq160a___ever_told_you_had_arthritis, mcq366b___doctor_told_to_increase_exercise, mcq560___ever_had_gallbladder_surgery?, paq650___vigorous_recreational_activities, rhq131___ever_been_pregnant?
- Sources:
  - https://medlineplus.gov/menopause.html
  - https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_RHQ.htm
  - https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_KIQ_U.htm

## Thyroid problems

- Research take: Questionnaire-only screening should separate hypo- from hyperthyroid patterns: weight gain and cold intolerance versus weight loss, heat intolerance, palpitations, tremor, and insomnia.
- NHANES coverage: Your thyroid model mostly uses general health, sleep, weight, smoking, alcohol, nocturia, medications, and pregnancy context rather than direct thyroid symptom questions.
- Useful non-lab flags:
  - Weight change without intentional dieting is high value.
  - Cold intolerance, constipation, heavy periods, and depression fit hypothyroid patterns.
  - Heat intolerance, palpitations, tremor, frequent stools, and trouble sleeping fit hyperthyroid patterns.
  - Family history and visible neck swelling/goiter are valuable net-new non-lab questions.
- Questionnaire/history features already in your models: age_years, alq130___avg_#_alcoholic_drinks/day___past_12_mos, bpq080___doctor_told_you___high_cholesterol_level, diq010___doctor_told_you_have_diabetes, gender, huq010___general_health_condition, kiq480___how_many_times_urinate_in_night?, mcq053___taking_treatment_for_anemia/past_3_mos, mcq080___doctor_ever_said_you_were_overweight, ocq670___overall_work_schedule_past_3_months, paq665___moderate_recreational_activities, pregnancy_status, sld012___sleep_hours___weekdays_or_workdays, slq050___ever_told_doctor_had_trouble_sleeping?, smd650___avg_#_cigarettes/day_during_past_30_days, whq070___tried_to_lose_weight_in_past_year
- Sources:
  - https://medlineplus.gov/thyroiddiseases.html
  - https://medlineplus.gov/hypothyroidism.html
  - https://medlineplus.gov/hyperthyroidism.html

## Kidney problems

- Research take: In NHANES, kidney risk is often better flagged by diabetes, hypertension, nocturia, kidney-stone history, fatigue, and poor general health than by symptoms alone.
- NHANES coverage: Very strong NHANES fit via KIQ weak/failing kidneys, kidney stones, nocturia, urinary leakage, plus diabetes / BP / cardiometabolic history.
- Useful non-lab flags:
  - Known diabetes or hypertension meaningfully raises prior probability.
  - Nocturia, swelling, fatigue, weakness, and declining urine output are important signals.
  - Stone history adds value because recurrent stones often coexist with renal / electrolyte problems.
  - Pure questionnaire-only detection is limited because CKD can be silent until late disease.
- Questionnaire/history features already in your models: age_years, bpq020___ever_told_you_had_high_blood_pressure, bpq040a___taking_prescription_for_hypertension, bpq080___doctor_told_you___high_cholesterol_level, diq010___doctor_told_you_have_diabetes, diq050___taking_insulin_now, diq070___take_diabetic_pills_to_lower_blood_sugar, dpq040___feeling_tired_or_having_little_energy, gender, huq010___general_health_condition, huq051___#times_receive_healthcare_over_past_year, kiq005___how_often_have_urinary_leakage?, kiq026___ever_had_kidney_stones?, kiq044___urinated_before_reaching_the_toilet?, kiq480___how_many_times_urinate_in_night?, mcq053___taking_treatment_for_anemia/past_3_mos, mcq080___doctor_ever_said_you_were_overweight, mcq092___ever_receive_blood_transfusion, mcq160a___ever_told_you_had_arthritis, mcq160b___ever_told_you_had_congestive_heart_failure, mcq160e___ever_told_you_had_heart_attack, mcq160f___ever_told_you_had_stroke, paq665___moderate_recreational_activities
- Sources:
  - https://medlineplus.gov/kidneydiseases.html
  - https://www.niddk.nih.gov/health-information/kidney-disease/kidney-failure/what-is-kidney-failure
  - https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_KIQ_U.htm

## Sleep disorder

- Research take: The strongest symptom cluster is loud snoring, witnessed apneas or snorting/choking, unrefreshing sleep, and daytime fatigue/somnolence.
- NHANES coverage: Strong NHANES fit through SLQ snoring and sleep timing items plus fatigue, respiratory disease, alcohol, and blood pressure history.
- Useful non-lab flags:
  - Snoring is necessary but not sufficient; combine it with daytime tiredness and sleep schedule disruption.
  - Waking choking or gasping is more specific than snoring alone and would be a strong net-new question.
  - Hypertension, obesity, male sex, and COPD/asthma comorbidity raise risk.
  - Shift-work style schedules can explain symptoms and should be modeled separately from obstructive sleep apnea risk.
- Questionnaire/history features already in your models: alq170___past_30_days_#_times_4_5_drinks_on_an_oc, bpq020___ever_told_you_had_high_blood_pressure, cdq010___shortness_of_breath_on_stairs/inclines, dpq040___feeling_tired_or_having_little_energy, mcq010___ever_been_told_you_have_asthma, mcq160p___ever_told_you_had_copd_emphysema, paq605___vigorous_work_activity, sld012___sleep_hours___weekdays_or_workdays, sld013___sleep_hours___weekends, slq030___how_often_do_you_snore?, slq300___usual_sleep_time_on_weekdays_or_workdays, slq310___usual_wake_time_on_weekdays_or_workdays, slq320___usual_sleep_time_on_weekends, slq330___usual_wake_time_on_weekends
- Sources:
  - https://medlineplus.gov/sleepapnea.html
  - https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_SLQ.htm
  - https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_MCQ.htm

## Anemia

- Research take: Non-lab clues are fatigue, shortness of breath on exertion, dizziness, pallor, heavy periods, and blood-loss history; your current model is still lab-dominant.
- NHANES coverage: Moderate NHANES fit for symptoms and transfusion history; very strong fit for laboratory confirmation.
- Useful non-lab flags:
  - Fatigue and exertional dyspnea are the most useful general symptom questions.
  - Heavy menstrual bleeding, GI bleeding symptoms, and pica / ice craving are high-value net-new questions.
  - Recent hospitalization or transfusion can indicate active blood-loss / severe chronic disease context.
  - Symptom-only prediction is weak for mild anemia; labs remain central.
- Questionnaire/history features already in your models: cdq001___sp_ever_had_pain_or_discomfort_in_chest, cdq010___shortness_of_breath_on_stairs/inclines, dpq040___feeling_tired_or_having_little_energy, fatigue_ordinal, huq010___general_health_condition, huq071___overnight_hospital_patient_in_last_year, kiq005___how_often_have_urinary_leakage?, mcq092___ever_receive_blood_transfusion, mcq520___abdominal_pain_during_past_12_months?, ocd150___type_of_work_done_last_week, rxduse___taken_prescription_medicine,_past_month
- Sources:
  - https://medlineplus.gov/anemia.html
  - https://www.nhlbi.nih.gov/health/anemia/symptoms
  - https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_MCQ.htm

## Liver / hepatic insufficiency

- Research take: Abdominal pain, jaundice, dark urine, pale stools, swelling, easy bruising, alcohol exposure, and transfusion history are the highest-yield non-lab flags.
- NHANES coverage: Good NHANES fit through liver-condition history, alcohol questions, abdominal pain, transfusion history, hospitalization, and hepatitis serologies.
- Useful non-lab flags:
  - Abdominal pain is nonspecific; jaundice and dark urine are higher-yield symptom questions.
  - Heavy alcohol use and prior transfusion matter as exposure questions.
  - Many chronic liver diseases stay silent until damage is advanced, so symptom-only screening misses early disease.
  - Your current liver model mixes symptom, exposure, and serology fields; consider separating detection from etiology.
- Questionnaire/history features already in your models: age_years, alq151___ever_have_4/5_or_more_drinks_every_day?, cdq001___sp_ever_had_pain_or_discomfort_in_chest, cdq010___shortness_of_breath_on_stairs/inclines, diq070___take_diabetic_pills_to_lower_blood_sugar, gender, huq010___general_health_condition, huq071___overnight_hospital_patient_in_last_year, kiq430___how_frequently_does_this_occur?, kiq450___how_frequently_does_this_occur?, mcd093___year_receive_blood_transfusion, mcq080___doctor_ever_said_you_were_overweight, mcq520___abdominal_pain_during_past_12_months?, mcq540___ever_seen_a_dr_about_this_pain, ocd150___type_of_work_done_last_week, rhq031___had_regular_periods_in_past_12_months
- Sources:
  - https://medlineplus.gov/liverdiseases.html
  - https://medlineplus.gov/hepatitisb.html
  - https://medlineplus.gov/hepatitisc.html

## Prediabetes

- Research take: Prediabetes is usually asymptomatic, so the best non-lab signals are age, overweight status, family history, low activity, hypertension, sleep-disordered breathing, and gestational-diabetes history.
- NHANES coverage: Strong NHANES fit for risk-based screening using family history, weight perception, sleep timing, nocturia, fatigue, blood pressure, and activity items.
- Useful non-lab flags:
  - Most people have no symptoms, so risk-factor questions outperform symptom questions.
  - Family history, overweight/obesity, hypertension, inactivity, and poor sleep are the most defensible questionnaire flags.
  - Nocturia and fatigue can appear but are not specific enough to stand alone.
  - Acanthosis nigricans and prior gestational diabetes are valuable net-new non-lab questions.
- Questionnaire/history features already in your models: alq130___avg_#_alcoholic_drinks/day___past_12_mos, alq170___past_30_days_#_times_4_5_drinks_on_an_oc, bpq020___ever_told_you_had_high_blood_pressure, cos_weekday_wake, dpq040___feeling_tired_or_having_little_energy, kiq005___how_often_have_urinary_leakage?, kiq044___urinated_before_reaching_the_toilet?, kiq480___how_many_times_urinate_in_night?, mcq300c___close_relative_had_diabetes, paq605___vigorous_work_activity, paq625___number_of_days_moderate_work, paq650___vigorous_recreational_activities, paq665___moderate_recreational_activities, paq670___days_moderate_recreational_activities, sin_weekday_bedtime, sin_weekday_wake, sld012___sleep_hours___weekdays_or_workdays, sld013___sleep_hours___weekends, slq030___how_often_do_you_snore?, social_jetlag, whq040___like_to_weigh_more,_less_or_same
- Sources:
  - https://medlineplus.gov/prediabetes.html
  - https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_SLQ.htm
  - https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_MCQ.htm

## Hidden inflammation

- Research take: Questionnaire-only prediagnosis is weak because chronic low-grade inflammation is usually nonspecific; the strongest NHANES support comes from hs-CRP and comorbidity / lifestyle context.
- NHANES coverage: Best treated as a latent state combining hs-CRP, lipids, glucose, adiposity, smoking, sleep, alcohol, and poor self-rated health.
- Useful non-lab flags:
  - Persistent fatigue, poor sleep, poor general health, obesity, smoking, and chronic disease history can raise suspicion but are low-specificity.
  - Hidden inflammation should be framed as a risk state rather than a diagnosis.
  - If symptom-only flow is required, ask about chronic pain, morning stiffness, recurrent fevers, and unexplained malaise as net-new questions.
  - Model governance should make explicit that hs-CRP is the main confirmatory signal here.
- Questionnaire/history features already in your models: age_years, alq130___avg_#_alcoholic_drinks/day___past_12_mos, diq010___doctor_told_you_have_diabetes, ever_heavy_drinker, gender, huq010___general_health_condition, kiq022___ever_told_you_had_weak/failing_kidneys?, mcq080___doctor_ever_said_you_were_overweight, mcq160l___ever_told_you_had_any_liver_condition, moderate_exercise, ocq180___hours_worked_last_week_in_total_all_jobs, ocq670___overall_work_schedule_past_3_months, pad680___minutes_sedentary_activity, rhq031___had_regular_periods_in_past_12_months, sld012___sleep_hours___weekdays_or_workdays, slq050___ever_told_doctor_had_trouble_sleeping?, smd650___avg_#_cigarettes/day_during_past_30_days, smq040___do_you_now_smoke_cigarettes?, vigorous_exercise
- Sources:
  - https://medlineplus.gov/lab-tests/c-reactive-protein-crp-test/
  - https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_MCQ.htm
  - https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_SLQ.htm

## Electrolyte deficiency / imbalance

- Research take: The strongest non-lab flags are dehydration losses, heavy sweating, vomiting/diarrhea, muscle cramps, weakness, palpitations, kidney disease, and medication burden.
- NHANES coverage: Your current model is questionnaire-heavy and can flag risk, but true diagnosis still depends on serum electrolyte testing.
- Useful non-lab flags:
  - Nocturia, kidney disease, kidney stones, fatigue, and intense exercise / sweating increase plausibility.
  - Medication burden matters because diuretics and laxatives commonly drive imbalance.
  - Symptom-only screening should prioritize cramps, weakness, dizziness, confusion, palpitations, vomiting, and diarrhea as net-new items.
  - This target should be labeled risk-of-imbalance rather than confirmed deficiency if labs are absent.
- Questionnaire/history features already in your models: bpq020___ever_told_you_had_high_blood_pressure, dpq040___feeling_tired_or_having_little_energy, kiq022___ever_told_you_had_weak/failing_kidneys?, kiq026___ever_had_kidney_stones?, kiq480___how_many_times_urinate_in_night?, mcq160a___ever_told_you_had_arthritis, paq650___vigorous_recreational_activities
- Sources:
  - https://medlineplus.gov/fluidandelectrolytebalance.html
  - https://medlineplus.gov/kidneydiseases.html
  - https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_KIQ_U.htm

## Hepatitis B & C

- Research take: For HBV/HCV, risk-factor questions matter more than symptoms because chronic infection is often silent for years.
- NHANES coverage: Excellent NHANES fit through HEQ diagnosis items, country of birth, transfusion history, alcohol, smoking, liver history, and extensive hepatitis serologies / liver labs.
- Useful non-lab flags:
  - Transfusion history, prior dialysis, injection drug use, tattoos/piercings, incarceration exposure, and birthplace are high-value risk questions.
  - Symptoms like fatigue, abdominal pain, jaundice, dark urine, pale stools, and nausea help only after disease is active.
  - Because HBV/HCV may be asymptomatic, screening-risk logic should outrank symptom logic.
  - Model outputs should distinguish viral hepatitis risk from general liver injury.
- Questionnaire/history features already in your models: age_years, alq130___avg_#_alcoholic_drinks/day___past_12_mos, country_of_birth, diq010___doctor_told_you_have_diabetes, education, ethnicity, ever_heavy_drinker, gender, huq010___general_health_condition, huq071___overnight_hospital_patient_in_last_year, income_poverty_ratio, mcq092___ever_receive_blood_transfusion, mcq160l___ever_told_you_had_any_liver_condition, smq020___smoked_at_least_100_cigarettes_in_life
- Sources:
  - https://medlineplus.gov/hepatitisb.html
  - https://medlineplus.gov/hepatitisc.html
  - https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_HEQ.htm

## Cross-condition design implications

- Symptoms like fatigue, poor sleep, nocturia, and poor general health recur across thyroid, kidney, anemia, prediabetes, hidden inflammation, and electrolyte imbalance, so they should be modeled as shared upstream questions rather than repeated disease-specific questions.
- Risk-factor logic should outrank symptom logic for prediabetes and hepatitis B/C because both can be asymptomatic.
- Menopause and thyroid benefit the most from adding targeted net-new symptom questions, because the supplied models currently lean on indirect proxies.
- Hidden inflammation should be positioned as an inflammatory-risk state rather than a disease label unless supported by lab markers such as hs-CRP.

## Core sources

- https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_MCQ.htm
- https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_KIQ_U.htm
- https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_SLQ.htm
- https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_RHQ.htm
- https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_HEQ.htm
- https://medlineplus.gov/menopause.html
- https://medlineplus.gov/hypothyroidism.html
- https://medlineplus.gov/hyperthyroidism.html
- https://www.niddk.nih.gov/health-information/kidney-disease/kidney-failure/what-is-kidney-failure
- https://medlineplus.gov/sleepapnea.html
- https://www.nhlbi.nih.gov/health/anemia/symptoms
- https://medlineplus.gov/liverdiseases.html
- https://medlineplus.gov/prediabetes.html
- https://medlineplus.gov/fluidandelectrolytebalance.html
- https://medlineplus.gov/lab-tests/c-reactive-protein-crp-test/
- https://medlineplus.gov/hepatitisb.html
- https://medlineplus.gov/hepatitisc.html
