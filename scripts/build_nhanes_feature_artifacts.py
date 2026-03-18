from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path("/Users/annaesakova/aipm/halfFull")
DATASET_PATH = ROOT / "data/processed/nhanes_merged_adults_final.csv"
QUESTION_DICT_PATH = Path("/Users/annaesakova/Downloads/Questionnaire-dictionary - dictionary.csv")
LAB_DICT_PATH = ROOT / "data/processed/laboratory_column_dictionary.csv"

CSV_OUT = ROOT / "data/processed/nhanes_feature_disease_map.csv"
JSON_OUT = ROOT / "assessment_quiz/nhanes_combined_question_flow.json"
RESEARCH_OUT = ROOT / "assessment_quiz/nhanes_signal_research.md"
QUESTIONS_OUT = ROOT / "assessment_quiz/priority_diagnostic_questions.md"


DISEASES = [
    ("menopause", "Menopause"),
    ("thyroid", "Thyroid problems"),
    ("kidney", "Kidney problems"),
    ("sleep_disorder", "Sleep disorder"),
    ("anemia", "Anemia"),
    ("liver", "Liver / hepatic insufficiency"),
    ("prediabetes", "Prediabetes"),
    ("hidden_inflammation", "Hidden inflammation"),
    ("electrolytes", "Electrolyte deficiency / imbalance"),
    ("hepatitis_bc", "Hepatitis B & C"),
]


RAW_FEATURES = {
    "menopause": [
        "age_years",
        "gender_female",
        "height_cm",
        "kiq042___leak_urine_during_physical_activities?",
        "kiq005___how_often_have_urinary_leakage?",
        "bpq020___ever_told_you_had_high_blood_pressure",
        "rhq131___ever_been_pregnant?",
        "mcq160a___ever_told_you_had_arthritis",
        "kiq044___urinated_before_reaching_the_toilet?",
        "mcq366b___doctor_told_to_increase_exercise",
        "mcq560___ever_had_gallbladder_surgery?",
        "paq650___vigorous_recreational_activities",
        "kiq450___how_frequently_does_this_occur?",
        "bpq040a___taking_prescription_for_hypertension",
    ],
    "thyroid": [
        "age_years",
        "gender",
        "med_count",
        "avg_drinks_per_day",
        "general_health_condition",
        "doctor_said_overweight",
        "told_dr_trouble_sleeping",
        "tried_to_lose_weight",
        "avg_cigarettes_per_day",
        "weight_kg",
        "pregnancy_status",
        "moderate_recreational",
        "times_urinate_in_night",
        "overall_work_schedule",
        "ever_told_high_cholesterol",
        "ever_told_diabetes",
        "taking_anemia_treatment",
        "sleep_hours_weekdays",
        "SLD012",
    ],
    "kidney": [
        "sbp_mean",
        "dbp_mean",
        "fasting_glucose",
        "hdl_cholesterol",
        "triglycerides",
        "age_years",
        "gender",
        "bmi",
        "ever_told_high_bp",
        "taking_bp_prescription",
        "told_high_cholesterol",
        "ever_told_heart_failure",
        "ever_told_heart_attack",
        "ever_told_stroke",
        "ever_told_diabetes",
        "taking_insulin",
        "taking_diabetic_pills",
        "times_urinate_in_night",
        "how_often_urinary_leakage",
        "urinated_before_toilet",
        "ever_had_kidney_stones",
        "taking_anemia_treatment",
        "ever_had_blood_transfusion",
        "ever_told_arthritis",
        "general_health_condition",
        "times_healthcare_past_year",
        "feeling_tired_little_energy",
        "med_count",
        "doctor_said_overweight",
        "moderate_recreational",
    ],
    "sleep_disorder": [
        "slq030___how_often_do_you_snore?",
        "dpq040___feeling_tired_or_having_little_energy",
        "sld012___sleep_hours___weekdays_or_workdays",
        "sld013___sleep_hours___weekends",
        "slq300___usual_sleep_time_on_weekdays_or_workdays",
        "slq310___usual_wake_time_on_weekdays_or_workdays",
        "slq320___usual_sleep_time_on_weekends",
        "slq330___usual_wake_time_on_weekends",
        "bpq020___ever_told_you_had_high_blood_pressure",
        "cdq010___shortness_of_breath_on_stairs/inclines",
        "mcq160p___ever_told_you_had_copd_emphysema",
        "mcq010___ever_been_told_you_have_asthma",
        "paq605___vigorous_work_activity",
        "alq170___past_30_days_#_times_4_5_drinks_on_an_oc",
    ],
    "anemia": [
        "LBXMC_mean_cell_hgb_conc_g_dl",
        "huq071___overnight_hospital_patient_in_last_year",
        "serum_albumin_g_dl",
        "LBXSAL_albumin_refrigerated_serum_g_dl",
        "LBDSALSI_albumin_refrigerated_serum_g_l",
        "height_cm",
        "iron_deficiency",
        "LBXBMN_blood_manganese_ug_l",
        "LBDBMNSI_blood_manganese_nmol_l",
        "LBDIRNSI_iron_frozen_serum_umol_l",
        "serum_iron_ug_dl",
        "LBXIRN_iron_frozen_serum_ug_dl",
        "LBXSIR_iron_refrigerated_serum_ug_dl",
        "LBDSIRSI_iron_refrigerated_serum_umol_l",
        "huq010___general_health_condition",
        "cdq010___shortness_of_breath_on_stairs/inclines",
        "LBDSGBSI_globulin_g_l",
        "LBXSGB_globulin_g_dl",
        "cdq001___sp_ever_had_pain_or_discomfort_in_chest",
        "LBXPLTSI_platelet_count_1000_cells_ul",
        "mcq520___abdominal_pain_during_past_12_months?",
        "fatigue_ordinal",
        "mcq092___ever_receive_blood_transfusion",
        "LBXBSE_blood_selenium_ug_l",
        "LBDBSESI_blood_selenium_umol_l",
        "LBXHSCRP_hs_c_reactive_protein_mg_l",
        "dpq040___feeling_tired_or_having_little_energy",
        "kiq005___how_often_have_urinary_leakage?",
        "ocd150___type_of_work_done_last_week",
        "LBDTIBSI_tot_iron_binding_capacity_tibc_umol_l",
        "LBDTIB_total_iron_binding_capacity_tibc_ug_dl",
        "tibc_ug_dl",
        "WTFOLPRP__p_folfms",
        "WTFOLPRP_folate_folate_form_weight_pre_pandemic",
        "rxduse___taken_prescription_medicine,_past_month",
    ],
    "liver": [
        "age_years",
        "huq010___general_health_condition",
        "mcq540___ever_seen_a_dr_about_this_pain",
        "kiq430___how_frequently_does_this_occur?",
        "SSLBDHD_hepatitis_d_antibody_anti_hdv_retesting",
        "rhq031___had_regular_periods_in_past_12_months",
        "mcd093___year_receive_blood_transfusion",
        "SSMEASQ_measles_igg_antibody_mba_quantitative",
        "insulin_uU_ml",
        "mcq080___doctor_ever_said_you_were_overweight",
        "cdq010___shortness_of_breath_on_stairs/inclines",
        "URDPMALC_phenylmercapturic_acid_comment_code",
        "alq151___ever_have_4/5_or_more_drinks_every_day?",
        "mcq520___abdominal_pain_during_past_12_months?",
        "ocd150___type_of_work_done_last_week",
        "waist_cm",
        "diq070___take_diabetic_pills_to_lower_blood_sugar",
        "cdq001___sp_ever_had_pain_or_discomfort_in_chest",
        "huq071___overnight_hospital_patient_in_last_year",
        "kiq450___how_frequently_does_this_occur?",
        "gender_female",
    ],
    "prediabetes": [
        "sleep_hours_weekend",
        "slq030___how_often_do_you_snore?",
        "mcq300c___close_relative_had_diabetes",
        "paq650___vigorous_recreational_activities",
        "whq040___like_to_weigh_more,_less_or_same",
        "kiq005___how_often_have_urinary_leakage?",
        "alq130___avg_#_alcoholic_drinks/day___past_12_mos",
        "paq625___number_of_days_moderate_work",
        "kiq480___how_many_times_urinate_in_night?",
        "cos_weekday_wake",
        "paq670___days_moderate_recreational_activities",
        "dpq040___feeling_tired_or_having_little_energy",
        "paq665___moderate_recreational_activities",
        "sleep_hours_weekday",
        "paq605___vigorous_work_activity",
        "social_jetlag",
        "kiq044___urinated_before_reaching_the_toilet?",
        "alq170___past_30_days_#_times_4_5_drinks_on_an_oc",
        "sin_weekday_bedtime",
        "sin_weekday_wake",
        "bpq020___ever_told_you_had_high_blood_pressure",
    ],
    "hidden_inflammation": [
        "total_cholesterol",
        "ldl_cholesterol",
        "hdl_cholesterol",
        "triglycerides",
        "serum_glucose",
        "fasting_glucose",
        "creatinine",
        "sbp_mean",
        "dbp_mean",
        "pulse_mean",
        "bmi",
        "calcium",
        "age_years",
        "smoking_now",
        "cigarettes_per_day",
        "avg_drinks_per_day",
        "ever_heavy_drinker",
        "sedentary_minutes",
        "vigorous_exercise",
        "moderate_exercise",
        "sleep_hours_weekdays",
        "told_dr_trouble_sleeping",
        "work_schedule",
        "hours_worked_per_week",
        "diabetes",
        "doctor_said_overweight",
        "liver_condition",
        "kidney_disease",
        "regular_periods",
        "general_health_condition",
        "waist_cm",
        "gender",
    ],
    "electrolytes": [
        "bpq020___ever_told_you_had_high_blood_pressure",
        "kiq480___how_many_times_urinate_in_night?",
        "paq650___vigorous_recreational_activities",
        "med_count",
        "dpq040___feeling_tired_or_having_little_energy",
        "kiq026___ever_had_kidney_stones?",
        "mcq160a___ever_told_you_had_arthritis",
        "kiq022___ever_told_you_had_weak/failing_kidneys?",
    ],
    "hepatitis_bc": [
        "alt",
        "ast",
        "ggt",
        "bilirubin",
        "albumin",
        "total_protein",
        "alp",
        "platelet",
        "wbc",
        "hemoglobin",
        "ferritin",
        "creatinine",
        "cholesterol",
        "triglycerides",
        "hdl",
        "glucose",
        "bun",
        "bmi",
        "waist_cm",
        "sbp_mean",
        "dbp_mean",
        "pulse_mean",
        "age_years",
        "gender",
        "ethnicity",
        "country_of_birth",
        "education",
        "income_poverty_ratio",
        "avg_drinks_per_day",
        "ever_heavy_drinker",
        "blood_transfusion",
        "smoked_100_cigs",
        "diabetes",
        "liver_condition",
        "general_health",
        "hospitalized_lastyear",
    ],
}


ALIAS_MAP: dict[str, dict[str, Any]] = {
    "gender_female": {
        "canonical_key": "gender",
        "mapped_dataset_column": "gender",
        "nhanes_code": "RIAGENDR",
        "feature_type": "derived-demographic",
        "notes": "Binary encoding derived from gender == Female.",
    },
    "age_years": {
        "canonical_key": "age_years",
        "mapped_dataset_column": "age_years",
        "nhanes_code": "RIDAGEYR",
        "feature_type": "demographic",
        "notes": "Renamed NHANES age in years field.",
    },
    "gender": {
        "canonical_key": "gender",
        "mapped_dataset_column": "gender",
        "nhanes_code": "RIAGENDR",
        "feature_type": "demographic",
        "notes": "Renamed NHANES sex variable.",
    },
    "height_cm": {
        "canonical_key": "height_cm",
        "mapped_dataset_column": "height_cm",
        "nhanes_code": "BMXHT",
        "feature_type": "exam",
        "notes": "Renamed body measures height variable.",
    },
    "weight_kg": {
        "canonical_key": "weight_kg",
        "mapped_dataset_column": "weight_kg",
        "nhanes_code": "BMXWT",
        "feature_type": "exam",
        "notes": "Renamed body measures weight variable.",
    },
    "bmi": {
        "canonical_key": "bmi",
        "mapped_dataset_column": "bmi",
        "nhanes_code": "BMXBMI",
        "feature_type": "derived-exam",
        "notes": "Body mass index from NHANES body measures.",
    },
    "waist_cm": {
        "canonical_key": "waist_cm",
        "mapped_dataset_column": "waist_cm",
        "nhanes_code": "BMXWAIST",
        "feature_type": "exam",
        "notes": "Renamed waist circumference variable.",
    },
    "pregnancy_status": {
        "canonical_key": "pregnancy_status",
        "mapped_dataset_column": "pregnancy_status",
        "nhanes_code": "RIDEXPRG",
        "feature_type": "demographic",
        "notes": "Pregnancy status harmonized from demographics.",
    },
    "med_count": {
        "canonical_key": "med_count",
        "mapped_dataset_column": "med_count",
        "nhanes_code": "RXDCOUNT",
        "feature_type": "derived-medication",
        "notes": "Local count of prescription medicines; aligns with RXDCOUNT.",
    },
    "avg_drinks_per_day": {
        "canonical_key": "alq130___avg_#_alcoholic_drinks/day___past_12_mos",
        "mapped_dataset_column": "alq130___avg_#_alcoholic_drinks/day___past_12_mos",
        "nhanes_code": "ALQ130",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to NHANES alcohol quantity item.",
    },
    "general_health_condition": {
        "canonical_key": "huq010___general_health_condition",
        "mapped_dataset_column": "huq010___general_health_condition",
        "nhanes_code": "HUQ010",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to general health status item.",
    },
    "doctor_said_overweight": {
        "canonical_key": "mcq080___doctor_ever_said_you_were_overweight",
        "mapped_dataset_column": "mcq080___doctor_ever_said_you_were_overweight",
        "nhanes_code": "MCQ080",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to clinician-told overweight item.",
    },
    "told_dr_trouble_sleeping": {
        "canonical_key": "slq050___ever_told_doctor_had_trouble_sleeping?",
        "mapped_dataset_column": "slq050___ever_told_doctor_had_trouble_sleeping?",
        "nhanes_code": "SLQ050",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to NHANES sleep trouble item.",
    },
    "tried_to_lose_weight": {
        "canonical_key": "whq070___tried_to_lose_weight_in_past_year",
        "mapped_dataset_column": "whq070___tried_to_lose_weight_in_past_year",
        "nhanes_code": "WHQ070",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to weight-loss attempt item.",
    },
    "avg_cigarettes_per_day": {
        "canonical_key": "smd650___avg_#_cigarettes/day_during_past_30_days",
        "mapped_dataset_column": "smd650___avg_#_cigarettes/day_during_past_30_days",
        "nhanes_code": "SMD650",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to average cigarettes/day in past 30 days.",
    },
    "moderate_recreational": {
        "canonical_key": "paq665___moderate_recreational_activities",
        "mapped_dataset_column": "paq665___moderate_recreational_activities",
        "nhanes_code": "PAQ665",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to moderate recreational activity yes/no.",
    },
    "times_urinate_in_night": {
        "canonical_key": "kiq480___how_many_times_urinate_in_night?",
        "mapped_dataset_column": "kiq480___how_many_times_urinate_in_night?",
        "nhanes_code": "KIQ480",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to nocturia frequency item.",
    },
    "overall_work_schedule": {
        "canonical_key": "ocq670___overall_work_schedule_past_3_months",
        "mapped_dataset_column": "ocq670___overall_work_schedule_past_3_months",
        "nhanes_code": "OCQ670",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to work schedule item.",
    },
    "work_schedule": {
        "canonical_key": "ocq670___overall_work_schedule_past_3_months",
        "mapped_dataset_column": "ocq670___overall_work_schedule_past_3_months",
        "nhanes_code": "OCQ670",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to work schedule item.",
    },
    "hours_worked_per_week": {
        "canonical_key": "ocq180___hours_worked_last_week_in_total_all_jobs",
        "mapped_dataset_column": "ocq180___hours_worked_last_week_in_total_all_jobs",
        "nhanes_code": "OCQ180",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to weekly hours worked.",
    },
    "ever_told_high_cholesterol": {
        "canonical_key": "bpq080___doctor_told_you___high_cholesterol_level",
        "mapped_dataset_column": "bpq080___doctor_told_you___high_cholesterol_level",
        "nhanes_code": "BPQ080",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to high cholesterol diagnosis item.",
    },
    "told_high_cholesterol": {
        "canonical_key": "bpq080___doctor_told_you___high_cholesterol_level",
        "mapped_dataset_column": "bpq080___doctor_told_you___high_cholesterol_level",
        "nhanes_code": "BPQ080",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to high cholesterol diagnosis item.",
    },
    "ever_told_diabetes": {
        "canonical_key": "diq010___doctor_told_you_have_diabetes",
        "mapped_dataset_column": "diq010___doctor_told_you_have_diabetes",
        "nhanes_code": "DIQ010",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to diabetes diagnosis item.",
    },
    "diabetes": {
        "canonical_key": "diq010___doctor_told_you_have_diabetes",
        "mapped_dataset_column": "diq010___doctor_told_you_have_diabetes",
        "nhanes_code": "DIQ010",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to diabetes diagnosis item.",
    },
    "taking_anemia_treatment": {
        "canonical_key": "mcq053___taking_treatment_for_anemia/past_3_mos",
        "mapped_dataset_column": "mcq053___taking_treatment_for_anemia/past_3_mos",
        "nhanes_code": "MCQ053",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to anemia treatment item.",
    },
    "sleep_hours_weekdays": {
        "canonical_key": "sld012___sleep_hours___weekdays_or_workdays",
        "mapped_dataset_column": "sld012___sleep_hours___weekdays_or_workdays",
        "nhanes_code": "SLD012",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to weekday sleep duration.",
    },
    "SLD012": {
        "canonical_key": "sld012___sleep_hours___weekdays_or_workdays",
        "mapped_dataset_column": "sld012___sleep_hours___weekdays_or_workdays",
        "nhanes_code": "SLD012",
        "feature_type": "questionnaire",
        "notes": "Uppercase raw feature normalized to dataset naming.",
    },
    "sleep_hours_weekday": {
        "canonical_key": "sld012___sleep_hours___weekdays_or_workdays",
        "mapped_dataset_column": "sld012___sleep_hours___weekdays_or_workdays",
        "nhanes_code": "SLD012",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to weekday sleep duration.",
    },
    "sleep_hours_weekend": {
        "canonical_key": "sld013___sleep_hours___weekends",
        "mapped_dataset_column": "sld013___sleep_hours___weekends",
        "nhanes_code": "SLD013",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to weekend sleep duration.",
    },
    "ever_told_high_bp": {
        "canonical_key": "bpq020___ever_told_you_had_high_blood_pressure",
        "mapped_dataset_column": "bpq020___ever_told_you_had_high_blood_pressure",
        "nhanes_code": "BPQ020",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to hypertension diagnosis item.",
    },
    "taking_bp_prescription": {
        "canonical_key": "bpq040a___taking_prescription_for_hypertension",
        "mapped_dataset_column": "bpq040a___taking_prescription_for_hypertension",
        "nhanes_code": "BPQ040A",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to antihypertensive medication item.",
    },
    "ever_told_heart_failure": {
        "canonical_key": "mcq160b___ever_told_you_had_congestive_heart_failure",
        "mapped_dataset_column": "mcq160b___ever_told_you_had_congestive_heart_failure",
        "nhanes_code": "MCQ160B",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to CHF diagnosis item.",
    },
    "ever_told_heart_attack": {
        "canonical_key": "mcq160e___ever_told_you_had_heart_attack",
        "mapped_dataset_column": "mcq160e___ever_told_you_had_heart_attack",
        "nhanes_code": "MCQ160E",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to heart attack diagnosis item.",
    },
    "ever_told_stroke": {
        "canonical_key": "mcq160f___ever_told_you_had_stroke",
        "mapped_dataset_column": "mcq160f___ever_told_you_had_stroke",
        "nhanes_code": "MCQ160F",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to stroke diagnosis item.",
    },
    "taking_insulin": {
        "canonical_key": "diq050___taking_insulin_now",
        "mapped_dataset_column": "diq050___taking_insulin_now",
        "nhanes_code": "DIQ050",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to insulin use item.",
    },
    "taking_diabetic_pills": {
        "canonical_key": "diq070___take_diabetic_pills_to_lower_blood_sugar",
        "mapped_dataset_column": "diq070___take_diabetic_pills_to_lower_blood_sugar",
        "nhanes_code": "DIQ070",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to oral diabetes medication item.",
    },
    "how_often_urinary_leakage": {
        "canonical_key": "kiq005___how_often_have_urinary_leakage?",
        "mapped_dataset_column": "kiq005___how_often_have_urinary_leakage?",
        "nhanes_code": "KIQ005",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to incontinence frequency item.",
    },
    "urinated_before_toilet": {
        "canonical_key": "kiq044___urinated_before_reaching_the_toilet?",
        "mapped_dataset_column": "kiq044___urinated_before_reaching_the_toilet?",
        "nhanes_code": "KIQ044",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to urgency incontinence item.",
    },
    "ever_had_kidney_stones": {
        "canonical_key": "kiq026___ever_had_kidney_stones?",
        "mapped_dataset_column": "kiq026___ever_had_kidney_stones?",
        "nhanes_code": "KIQ026",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to kidney stones item.",
    },
    "ever_had_blood_transfusion": {
        "canonical_key": "mcq092___ever_receive_blood_transfusion",
        "mapped_dataset_column": "mcq092___ever_receive_blood_transfusion",
        "nhanes_code": "MCQ092",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to blood transfusion history item.",
    },
    "blood_transfusion": {
        "canonical_key": "mcq092___ever_receive_blood_transfusion",
        "mapped_dataset_column": "mcq092___ever_receive_blood_transfusion",
        "nhanes_code": "MCQ092",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to blood transfusion history item.",
    },
    "ever_told_arthritis": {
        "canonical_key": "mcq160a___ever_told_you_had_arthritis",
        "mapped_dataset_column": "mcq160a___ever_told_you_had_arthritis",
        "nhanes_code": "MCQ160A",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to arthritis diagnosis item.",
    },
    "times_healthcare_past_year": {
        "canonical_key": "huq051___#times_receive_healthcare_over_past_year",
        "mapped_dataset_column": "huq051___#times_receive_healthcare_over_past_year",
        "nhanes_code": "HUQ051",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to healthcare utilization frequency.",
    },
    "feeling_tired_little_energy": {
        "canonical_key": "dpq040___feeling_tired_or_having_little_energy",
        "mapped_dataset_column": "dpq040___feeling_tired_or_having_little_energy",
        "nhanes_code": "DPQ040",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to PHQ energy/fatigue item.",
    },
    "fasting_glucose": {
        "canonical_key": "fasting_glucose_mg_dl",
        "mapped_dataset_column": "fasting_glucose_mg_dl",
        "nhanes_code": "LBXGLU",
        "feature_type": "lab",
        "notes": "Alias normalized to fasting plasma glucose.",
    },
    "hdl_cholesterol": {
        "canonical_key": "hdl_cholesterol_mg_dl",
        "mapped_dataset_column": "hdl_cholesterol_mg_dl",
        "nhanes_code": "LBDHDD",
        "feature_type": "lab",
        "notes": "Alias normalized to direct HDL cholesterol.",
    },
    "triglycerides": {
        "canonical_key": "triglycerides_mg_dl",
        "mapped_dataset_column": "triglycerides_mg_dl",
        "nhanes_code": "LBXTR",
        "feature_type": "lab",
        "notes": "Alias normalized to triglycerides.",
    },
    "sbp_mean": {
        "canonical_key": "sbp_mean",
        "mapped_dataset_column": "sbp_mean",
        "nhanes_code": "BPXSY1-3",
        "feature_type": "derived-vitals",
        "notes": "Mean systolic blood pressure derived from repeated BP readings.",
    },
    "dbp_mean": {
        "canonical_key": "dbp_mean",
        "mapped_dataset_column": "dbp_mean",
        "nhanes_code": "BPXDI1-3",
        "feature_type": "derived-vitals",
        "notes": "Mean diastolic blood pressure derived from repeated BP readings.",
    },
    "pulse_mean": {
        "canonical_key": "pulse_mean",
        "mapped_dataset_column": "pulse_mean",
        "nhanes_code": "pulse_1-3",
        "feature_type": "derived-vitals",
        "notes": "Mean pulse derived from repeated pulse readings in merged dataset.",
    },
    "iron_deficiency": {
        "canonical_key": "iron_deficiency",
        "mapped_dataset_column": "iron_deficiency",
        "nhanes_code": "",
        "feature_type": "derived-target",
        "notes": "Derived study variable, not a native NHANES field.",
    },
    "fatigue_ordinal": {
        "canonical_key": "fatigue_ordinal",
        "mapped_dataset_column": "fatigue_ordinal",
        "nhanes_code": "DPQ040-derived",
        "feature_type": "derived-questionnaire",
        "notes": "Ordinal encoding derived from DPQ040 fatigue responses.",
    },
    "tibc_ug_dl": {
        "canonical_key": "tibc_ug_dl",
        "mapped_dataset_column": "tibc_ug_dl",
        "nhanes_code": "LBDTIB",
        "feature_type": "lab",
        "notes": "Renamed total iron binding capacity variable.",
    },
    "insulin_uU_ml": {
        "canonical_key": "insulin_uU_ml",
        "mapped_dataset_column": "insulin_uU_ml",
        "nhanes_code": "LBXIN",
        "feature_type": "lab",
        "notes": "Renamed insulin field in merged dataset.",
    },
    "sleeping_disorders": {
        "canonical_key": "slq050___ever_told_doctor_had_trouble_sleeping?",
        "mapped_dataset_column": "slq050___ever_told_doctor_had_trouble_sleeping?",
        "nhanes_code": "SLQ050",
        "feature_type": "questionnaire",
        "notes": "Fallback alias for sleep problems.",
    },
    "cos_weekday_wake": {
        "canonical_key": "cos_weekday_wake",
        "mapped_dataset_column": "cos_weekday_wake",
        "nhanes_code": "SLQ310-derived",
        "feature_type": "engineered-time",
        "notes": "Cosine encoding derived from weekday wake time.",
    },
    "sin_weekday_wake": {
        "canonical_key": "sin_weekday_wake",
        "mapped_dataset_column": "sin_weekday_wake",
        "nhanes_code": "SLQ310-derived",
        "feature_type": "engineered-time",
        "notes": "Sine encoding derived from weekday wake time.",
    },
    "sin_weekday_bedtime": {
        "canonical_key": "sin_weekday_bedtime",
        "mapped_dataset_column": "sin_weekday_bedtime",
        "nhanes_code": "SLQ300-derived",
        "feature_type": "engineered-time",
        "notes": "Sine encoding derived from weekday sleep time.",
    },
    "social_jetlag": {
        "canonical_key": "social_jetlag",
        "mapped_dataset_column": "social_jetlag",
        "nhanes_code": "SLQ300/310/320/330-derived",
        "feature_type": "engineered-time",
        "notes": "Derived mismatch between workday and weekend sleep timing.",
    },
    "total_cholesterol": {
        "canonical_key": "total_cholesterol_mg_dl",
        "mapped_dataset_column": "total_cholesterol_mg_dl",
        "nhanes_code": "LBXTC",
        "feature_type": "lab",
        "notes": "Alias normalized to total cholesterol.",
    },
    "ldl_cholesterol": {
        "canonical_key": "LBDLDL_ldl_cholesterol_friedewald_mg_dl",
        "mapped_dataset_column": "LBDLDL_ldl_cholesterol_friedewald_mg_dl",
        "nhanes_code": "LBDLDL",
        "feature_type": "lab",
        "notes": "Alias normalized to calculated LDL cholesterol.",
    },
    "serum_glucose": {
        "canonical_key": "LBXSGL_glucose_refrigerated_serum_mg_dl",
        "mapped_dataset_column": "LBXSGL_glucose_refrigerated_serum_mg_dl",
        "nhanes_code": "LBXSGL",
        "feature_type": "lab",
        "notes": "Alias normalized to refrigerated serum glucose.",
    },
    "creatinine": {
        "canonical_key": "serum_creatinine_mg_dl",
        "mapped_dataset_column": "serum_creatinine_mg_dl",
        "nhanes_code": "LBXSCR",
        "feature_type": "lab",
        "notes": "Alias normalized to serum creatinine.",
    },
    "calcium": {
        "canonical_key": "LBXSCA_total_calcium_mg_dl",
        "mapped_dataset_column": "LBXSCA_total_calcium_mg_dl",
        "nhanes_code": "LBXSCA",
        "feature_type": "lab",
        "notes": "Alias normalized to total calcium.",
    },
    "smoking_now": {
        "canonical_key": "smq040___do_you_now_smoke_cigarettes?",
        "mapped_dataset_column": "smq040___do_you_now_smoke_cigarettes?",
        "nhanes_code": "SMQ040",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to current smoking item.",
    },
    "cigarettes_per_day": {
        "canonical_key": "smd650___avg_#_cigarettes/day_during_past_30_days",
        "mapped_dataset_column": "smd650___avg_#_cigarettes/day_during_past_30_days",
        "nhanes_code": "SMD650",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to cigarettes/day item.",
    },
    "ever_heavy_drinker": {
        "canonical_key": "ever_heavy_drinker",
        "mapped_dataset_column": "ever_heavy_drinker",
        "nhanes_code": "ALQ151 / ALQ170-derived",
        "feature_type": "derived-questionnaire",
        "notes": "Study-level heavy drinking indicator derived from alcohol use fields.",
    },
    "sedentary_minutes": {
        "canonical_key": "pad680___minutes_sedentary_activity",
        "mapped_dataset_column": "pad680___minutes_sedentary_activity",
        "nhanes_code": "PAD680",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to sedentary minutes.",
    },
    "vigorous_exercise": {
        "canonical_key": "vigorous_exercise",
        "mapped_dataset_column": "vigorous_exercise",
        "nhanes_code": "PAQ605 / PAQ650-derived",
        "feature_type": "derived-questionnaire",
        "notes": "Generic vigorous activity flag derived from work/recreation items.",
    },
    "moderate_exercise": {
        "canonical_key": "moderate_exercise",
        "mapped_dataset_column": "moderate_exercise",
        "nhanes_code": "PAQ620 / PAQ665-derived",
        "feature_type": "derived-questionnaire",
        "notes": "Generic moderate activity flag derived from work/recreation items.",
    },
    "kidney_disease": {
        "canonical_key": "kiq022___ever_told_you_had_weak/failing_kidneys?",
        "mapped_dataset_column": "kiq022___ever_told_you_had_weak/failing_kidneys?",
        "nhanes_code": "KIQ022",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to weak/failing kidneys diagnosis item.",
    },
    "liver_condition": {
        "canonical_key": "mcq160l___ever_told_you_had_any_liver_condition",
        "mapped_dataset_column": "mcq160l___ever_told_you_had_any_liver_condition",
        "nhanes_code": "MCQ160L",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to liver condition history item.",
    },
    "regular_periods": {
        "canonical_key": "rhq031___had_regular_periods_in_past_12_months",
        "mapped_dataset_column": "rhq031___had_regular_periods_in_past_12_months",
        "nhanes_code": "RHQ031",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to regular periods item.",
    },
    "alt": {
        "canonical_key": "alt_u_l",
        "mapped_dataset_column": "alt_u_l",
        "nhanes_code": "LBXSATSI",
        "feature_type": "lab",
        "notes": "Alias normalized to ALT.",
    },
    "ast": {
        "canonical_key": "ast_u_l",
        "mapped_dataset_column": "ast_u_l",
        "nhanes_code": "LBXSASSI",
        "feature_type": "lab",
        "notes": "Alias normalized to AST.",
    },
    "ggt": {
        "canonical_key": "ggt_u_l",
        "mapped_dataset_column": "ggt_u_l",
        "nhanes_code": "LBXSGTSI",
        "feature_type": "lab",
        "notes": "Alias normalized to GGT.",
    },
    "bilirubin": {
        "canonical_key": "total_bilirubin_mg_dl",
        "mapped_dataset_column": "total_bilirubin_mg_dl",
        "nhanes_code": "LBXSTB",
        "feature_type": "lab",
        "notes": "Alias normalized to total bilirubin.",
    },
    "albumin": {
        "canonical_key": "serum_albumin_g_dl",
        "mapped_dataset_column": "serum_albumin_g_dl",
        "nhanes_code": "LBXSAL",
        "feature_type": "lab",
        "notes": "Alias normalized to serum albumin.",
    },
    "total_protein": {
        "canonical_key": "LBXSTP_total_protein_g_dl",
        "mapped_dataset_column": "LBXSTP_total_protein_g_dl",
        "nhanes_code": "LBXSTP",
        "feature_type": "lab",
        "notes": "Alias normalized to total protein.",
    },
    "alp": {
        "canonical_key": "alp_u_l",
        "mapped_dataset_column": "alp_u_l",
        "nhanes_code": "LBXSAPSI",
        "feature_type": "lab",
        "notes": "Alias normalized to alkaline phosphatase.",
    },
    "platelet": {
        "canonical_key": "LBXPLTSI_platelet_count_1000_cells_ul",
        "mapped_dataset_column": "LBXPLTSI_platelet_count_1000_cells_ul",
        "nhanes_code": "LBXPLTSI",
        "feature_type": "lab",
        "notes": "Alias normalized to platelet count.",
    },
    "wbc": {
        "canonical_key": "LBXWBCSI_white_blood_cell_count_1000_cells_ul",
        "mapped_dataset_column": "LBXWBCSI_white_blood_cell_count_1000_cells_ul",
        "nhanes_code": "LBXWBCSI",
        "feature_type": "lab",
        "notes": "Alias normalized to white blood cell count.",
    },
    "hemoglobin": {
        "canonical_key": "LBXHGB_hemoglobin_g_dl",
        "mapped_dataset_column": "LBXHGB_hemoglobin_g_dl",
        "nhanes_code": "LBXHGB",
        "feature_type": "lab",
        "notes": "Alias normalized to hemoglobin.",
    },
    "ferritin": {
        "canonical_key": "ferritin_ng_ml",
        "mapped_dataset_column": "ferritin_ng_ml",
        "nhanes_code": "LBXFER",
        "feature_type": "lab",
        "notes": "Alias normalized to ferritin.",
    },
    "cholesterol": {
        "canonical_key": "total_cholesterol_mg_dl",
        "mapped_dataset_column": "total_cholesterol_mg_dl",
        "nhanes_code": "LBXTC",
        "feature_type": "lab",
        "notes": "Alias normalized to total cholesterol.",
    },
    "hdl": {
        "canonical_key": "hdl_cholesterol_mg_dl",
        "mapped_dataset_column": "hdl_cholesterol_mg_dl",
        "nhanes_code": "LBDHDD",
        "feature_type": "lab",
        "notes": "Alias normalized to HDL cholesterol.",
    },
    "glucose": {
        "canonical_key": "fasting_glucose_mg_dl",
        "mapped_dataset_column": "fasting_glucose_mg_dl",
        "nhanes_code": "LBXGLU",
        "feature_type": "lab",
        "notes": "Alias normalized to fasting glucose in merged dataset.",
    },
    "bun": {
        "canonical_key": "bun_mg_dl",
        "mapped_dataset_column": "bun_mg_dl",
        "nhanes_code": "LBXSBU",
        "feature_type": "lab",
        "notes": "Alias normalized to blood urea nitrogen.",
    },
    "ethnicity": {
        "canonical_key": "ethnicity",
        "mapped_dataset_column": "ethnicity",
        "nhanes_code": "RIDRETH3",
        "feature_type": "demographic",
        "notes": "Renamed race/ethnicity field.",
    },
    "country_of_birth": {
        "canonical_key": "country_of_birth",
        "mapped_dataset_column": "country_of_birth",
        "nhanes_code": "DMDBORN4",
        "feature_type": "demographic",
        "notes": "Renamed country-of-birth field.",
    },
    "education": {
        "canonical_key": "education",
        "mapped_dataset_column": "education",
        "nhanes_code": "DMDEDUC2",
        "feature_type": "demographic",
        "notes": "Adult education field; harmonized in merged dataset.",
    },
    "income_poverty_ratio": {
        "canonical_key": "income_poverty_ratio",
        "mapped_dataset_column": "income_poverty_ratio",
        "nhanes_code": "INDFMPIR",
        "feature_type": "demographic",
        "notes": "Income-to-poverty ratio.",
    },
    "smoked_100_cigs": {
        "canonical_key": "smq020___smoked_at_least_100_cigarettes_in_life",
        "mapped_dataset_column": "smq020___smoked_at_least_100_cigarettes_in_life",
        "nhanes_code": "SMQ020",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to ever-smoked-100-cigarettes item.",
    },
    "general_health": {
        "canonical_key": "huq010___general_health_condition",
        "mapped_dataset_column": "huq010___general_health_condition",
        "nhanes_code": "HUQ010",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to general health status item.",
    },
    "hospitalized_lastyear": {
        "canonical_key": "huq071___overnight_hospital_patient_in_last_year",
        "mapped_dataset_column": "huq071___overnight_hospital_patient_in_last_year",
        "nhanes_code": "HUQ071",
        "feature_type": "questionnaire",
        "notes": "Alias normalized to overnight hospitalization item.",
    },
}


SOURCE_URLS = {
    "nhanes_mcq": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_MCQ.htm",
    "nhanes_kiq": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_KIQ_U.htm",
    "nhanes_slq": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_SLQ.htm",
    "nhanes_rhq": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_RHQ.htm",
    "nhanes_heq": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_HEQ.htm",
    "menopause": "https://medlineplus.gov/menopause.html",
    "thyroid_general": "https://medlineplus.gov/thyroiddiseases.html",
    "thyroid_hypo": "https://medlineplus.gov/hypothyroidism.html",
    "thyroid_hyper": "https://medlineplus.gov/hyperthyroidism.html",
    "kidney": "https://medlineplus.gov/kidneydiseases.html",
    "kidney_failure": "https://www.niddk.nih.gov/health-information/kidney-disease/kidney-failure/what-is-kidney-failure",
    "sleep_apnea": "https://medlineplus.gov/sleepapnea.html",
    "anemia": "https://medlineplus.gov/anemia.html",
    "anemia_symptoms": "https://www.nhlbi.nih.gov/health/anemia/symptoms",
    "liver": "https://medlineplus.gov/liverdiseases.html",
    "prediabetes": "https://medlineplus.gov/prediabetes.html",
    "electrolytes": "https://medlineplus.gov/fluidandelectrolytebalance.html",
    "crp": "https://medlineplus.gov/lab-tests/c-reactive-protein-crp-test/",
    "hepatitis_b": "https://medlineplus.gov/hepatitisb.html",
    "hepatitis_c": "https://medlineplus.gov/hepatitisc.html",
}


RESEARCH_SUMMARY = {
    "Menopause": {
        "focus": "Best questionnaire flags are age 45 to 55, irregular or absent periods, urinary symptoms, sleep disruption, and prior pregnancy / reproductive history context.",
        "nhanes_fit": "Strong NHANES fit through RHQ menstrual history, KIQ urinary items, blood pressure history, and activity / clinician-advice questions.",
        "signals": [
            "Irregular or absent menstrual periods over the last 12 months.",
            "Hot flashes or night sweats are high-yield net-new questions not present in the supplied model features.",
            "Trouble sleeping and urinary urgency / leakage raise probability in perimenopausal patients.",
            "Age under 40 with menopausal symptoms should be treated as premature ovarian insufficiency / early menopause workup, not routine menopause.",
        ],
        "sources": [SOURCE_URLS["menopause"], SOURCE_URLS["nhanes_rhq"], SOURCE_URLS["nhanes_kiq"]],
    },
    "Thyroid problems": {
        "focus": "Questionnaire-only screening should separate hypo- from hyperthyroid patterns: weight gain and cold intolerance versus weight loss, heat intolerance, palpitations, tremor, and insomnia.",
        "nhanes_fit": "Your thyroid model mostly uses general health, sleep, weight, smoking, alcohol, nocturia, medications, and pregnancy context rather than direct thyroid symptom questions.",
        "signals": [
            "Weight change without intentional dieting is high value.",
            "Cold intolerance, constipation, heavy periods, and depression fit hypothyroid patterns.",
            "Heat intolerance, palpitations, tremor, frequent stools, and trouble sleeping fit hyperthyroid patterns.",
            "Family history and visible neck swelling/goiter are valuable net-new non-lab questions.",
        ],
        "sources": [SOURCE_URLS["thyroid_general"], SOURCE_URLS["thyroid_hypo"], SOURCE_URLS["thyroid_hyper"]],
    },
    "Kidney problems": {
        "focus": "In NHANES, kidney risk is often better flagged by diabetes, hypertension, nocturia, kidney-stone history, fatigue, and poor general health than by symptoms alone.",
        "nhanes_fit": "Very strong NHANES fit via KIQ weak/failing kidneys, kidney stones, nocturia, urinary leakage, plus diabetes / BP / cardiometabolic history.",
        "signals": [
            "Known diabetes or hypertension meaningfully raises prior probability.",
            "Nocturia, swelling, fatigue, weakness, and declining urine output are important signals.",
            "Stone history adds value because recurrent stones often coexist with renal / electrolyte problems.",
            "Pure questionnaire-only detection is limited because CKD can be silent until late disease.",
        ],
        "sources": [SOURCE_URLS["kidney"], SOURCE_URLS["kidney_failure"], SOURCE_URLS["nhanes_kiq"]],
    },
    "Sleep disorder": {
        "focus": "The strongest symptom cluster is loud snoring, witnessed apneas or snorting/choking, unrefreshing sleep, and daytime fatigue/somnolence.",
        "nhanes_fit": "Strong NHANES fit through SLQ snoring and sleep timing items plus fatigue, respiratory disease, alcohol, and blood pressure history.",
        "signals": [
            "Snoring is necessary but not sufficient; combine it with daytime tiredness and sleep schedule disruption.",
            "Waking choking or gasping is more specific than snoring alone and would be a strong net-new question.",
            "Hypertension, obesity, male sex, and COPD/asthma comorbidity raise risk.",
            "Shift-work style schedules can explain symptoms and should be modeled separately from obstructive sleep apnea risk.",
        ],
        "sources": [SOURCE_URLS["sleep_apnea"], SOURCE_URLS["nhanes_slq"], SOURCE_URLS["nhanes_mcq"]],
    },
    "Anemia": {
        "focus": "Non-lab clues are fatigue, shortness of breath on exertion, dizziness, pallor, heavy periods, and blood-loss history; your current model is still lab-dominant.",
        "nhanes_fit": "Moderate NHANES fit for symptoms and transfusion history; very strong fit for laboratory confirmation.",
        "signals": [
            "Fatigue and exertional dyspnea are the most useful general symptom questions.",
            "Heavy menstrual bleeding, GI bleeding symptoms, and pica / ice craving are high-value net-new questions.",
            "Recent hospitalization or transfusion can indicate active blood-loss / severe chronic disease context.",
            "Symptom-only prediction is weak for mild anemia; labs remain central.",
        ],
        "sources": [SOURCE_URLS["anemia"], SOURCE_URLS["anemia_symptoms"], SOURCE_URLS["nhanes_mcq"]],
    },
    "Liver / hepatic insufficiency": {
        "focus": "Abdominal pain, jaundice, dark urine, pale stools, swelling, easy bruising, alcohol exposure, and transfusion history are the highest-yield non-lab flags.",
        "nhanes_fit": "Good NHANES fit through liver-condition history, alcohol questions, abdominal pain, transfusion history, hospitalization, and hepatitis serologies.",
        "signals": [
            "Abdominal pain is nonspecific; jaundice and dark urine are higher-yield symptom questions.",
            "Heavy alcohol use and prior transfusion matter as exposure questions.",
            "Many chronic liver diseases stay silent until damage is advanced, so symptom-only screening misses early disease.",
            "Your current liver model mixes symptom, exposure, and serology fields; consider separating detection from etiology.",
        ],
        "sources": [SOURCE_URLS["liver"], SOURCE_URLS["hepatitis_b"], SOURCE_URLS["hepatitis_c"]],
    },
    "Prediabetes": {
        "focus": "Prediabetes is usually asymptomatic, so the best non-lab signals are age, overweight status, family history, low activity, hypertension, sleep-disordered breathing, and gestational-diabetes history.",
        "nhanes_fit": "Strong NHANES fit for risk-based screening using family history, weight perception, sleep timing, nocturia, fatigue, blood pressure, and activity items.",
        "signals": [
            "Most people have no symptoms, so risk-factor questions outperform symptom questions.",
            "Family history, overweight/obesity, hypertension, inactivity, and poor sleep are the most defensible questionnaire flags.",
            "Nocturia and fatigue can appear but are not specific enough to stand alone.",
            "Acanthosis nigricans and prior gestational diabetes are valuable net-new non-lab questions.",
        ],
        "sources": [SOURCE_URLS["prediabetes"], SOURCE_URLS["nhanes_slq"], SOURCE_URLS["nhanes_mcq"]],
    },
    "Hidden inflammation": {
        "focus": "Questionnaire-only prediagnosis is weak because chronic low-grade inflammation is usually nonspecific; the strongest NHANES support comes from hs-CRP and comorbidity / lifestyle context.",
        "nhanes_fit": "Best treated as a latent state combining hs-CRP, lipids, glucose, adiposity, smoking, sleep, alcohol, and poor self-rated health.",
        "signals": [
            "Persistent fatigue, poor sleep, poor general health, obesity, smoking, and chronic disease history can raise suspicion but are low-specificity.",
            "Hidden inflammation should be framed as a risk state rather than a diagnosis.",
            "If symptom-only flow is required, ask about chronic pain, morning stiffness, recurrent fevers, and unexplained malaise as net-new questions.",
            "Model governance should make explicit that hs-CRP is the main confirmatory signal here.",
        ],
        "sources": [SOURCE_URLS["crp"], SOURCE_URLS["nhanes_mcq"], SOURCE_URLS["nhanes_slq"]],
    },
    "Electrolyte deficiency / imbalance": {
        "focus": "The strongest non-lab flags are dehydration losses, heavy sweating, vomiting/diarrhea, muscle cramps, weakness, palpitations, kidney disease, and medication burden.",
        "nhanes_fit": "Your current model is questionnaire-heavy and can flag risk, but true diagnosis still depends on serum electrolyte testing.",
        "signals": [
            "Nocturia, kidney disease, kidney stones, fatigue, and intense exercise / sweating increase plausibility.",
            "Medication burden matters because diuretics and laxatives commonly drive imbalance.",
            "Symptom-only screening should prioritize cramps, weakness, dizziness, confusion, palpitations, vomiting, and diarrhea as net-new items.",
            "This target should be labeled risk-of-imbalance rather than confirmed deficiency if labs are absent.",
        ],
        "sources": [SOURCE_URLS["electrolytes"], SOURCE_URLS["kidney"], SOURCE_URLS["nhanes_kiq"]],
    },
    "Hepatitis B & C": {
        "focus": "For HBV/HCV, risk-factor questions matter more than symptoms because chronic infection is often silent for years.",
        "nhanes_fit": "Excellent NHANES fit through HEQ diagnosis items, country of birth, transfusion history, alcohol, smoking, liver history, and extensive hepatitis serologies / liver labs.",
        "signals": [
            "Transfusion history, prior dialysis, injection drug use, tattoos/piercings, incarceration exposure, and birthplace are high-value risk questions.",
            "Symptoms like fatigue, abdominal pain, jaundice, dark urine, pale stools, and nausea help only after disease is active.",
            "Because HBV/HCV may be asymptomatic, screening-risk logic should outrank symptom logic.",
            "Model outputs should distinguish viral hepatitis risk from general liver injury.",
        ],
        "sources": [SOURCE_URLS["hepatitis_b"], SOURCE_URLS["hepatitis_c"], SOURCE_URLS["nhanes_heq"]],
    },
}


PRIORITY_QUESTIONS = [
    {
        "question": "Have you been having hot flashes or night sweats?",
        "conditions": ["Menopause"],
        "why": "High-yield menopausal vasomotor symptom that materially increases pretest probability in midlife women, especially with irregular periods.",
        "in_current_models": "No",
        "sources": [SOURCE_URLS["menopause"]],
    },
    {
        "question": "Have your periods become irregular, lighter, heavier, or stopped for 12 months?",
        "conditions": ["Menopause"],
        "why": "Best non-lab discriminator for menopausal transition and menopause timing.",
        "in_current_models": "Partly",
        "sources": [SOURCE_URLS["menopause"], SOURCE_URLS["nhanes_rhq"]],
    },
    {
        "question": "Do you feel unusually sensitive to cold, constipated, and gaining weight without trying?",
        "conditions": ["Thyroid problems"],
        "why": "Classic hypothyroid cluster; much stronger than generic poor-health questions.",
        "in_current_models": "No",
        "sources": [SOURCE_URLS["thyroid_hypo"]],
    },
    {
        "question": "Do you get heat intolerance, palpitations, tremor, or trouble sleeping while losing weight?",
        "conditions": ["Thyroid problems"],
        "why": "Classic hyperthyroid pattern and useful counterpart to hypothyroid screening.",
        "in_current_models": "Partly",
        "sources": [SOURCE_URLS["thyroid_hyper"]],
    },
    {
        "question": "Have you noticed swelling in your legs, less urine than usual, or foamy urine?",
        "conditions": ["Kidney problems"],
        "why": "More kidney-specific than general fatigue; useful when combined with diabetes or hypertension history.",
        "in_current_models": "No",
        "sources": [SOURCE_URLS["kidney_failure"]],
    },
    {
        "question": "Has anyone told you that you stop breathing, gasp, or choke in your sleep?",
        "conditions": ["Sleep disorder"],
        "why": "More specific for obstructive sleep apnea than snoring alone.",
        "in_current_models": "No",
        "sources": [SOURCE_URLS["sleep_apnea"]],
    },
    {
        "question": "Are you excessively sleepy or struggling to stay awake during the day?",
        "conditions": ["Sleep disorder"],
        "why": "Separates clinically meaningful sleep-disordered breathing from simple short sleep.",
        "in_current_models": "Partly",
        "sources": [SOURCE_URLS["sleep_apnea"]],
    },
    {
        "question": "Do you get short of breath on stairs, feel dizzy, or crave ice?",
        "conditions": ["Anemia"],
        "why": "Exertional dyspnea and dizziness are strong symptom signals; pica or ice craving improves specificity for iron deficiency.",
        "in_current_models": "Partly",
        "sources": [SOURCE_URLS["anemia_symptoms"]],
    },
    {
        "question": "Do you have heavy menstrual bleeding or black/bloody stools?",
        "conditions": ["Anemia"],
        "why": "Directly targets likely blood-loss causes of anemia and helps route workup.",
        "in_current_models": "No",
        "sources": [SOURCE_URLS["anemia"]],
    },
    {
        "question": "Have you had yellowing of the eyes/skin, dark urine, pale stools, or easy bruising?",
        "conditions": ["Liver / hepatic insufficiency", "Hepatitis B & C"],
        "why": "Much more informative for hepatic dysfunction than abdominal pain alone.",
        "in_current_models": "No",
        "sources": [SOURCE_URLS["liver"], SOURCE_URLS["hepatitis_b"], SOURCE_URLS["hepatitis_c"]],
    },
    {
        "question": "Has a doctor ever told you that you had gestational diabetes, or do you have darkened skin on your neck/armpits?",
        "conditions": ["Prediabetes"],
        "why": "Gestational diabetes and acanthosis nigricans are strong non-lab risk clues missed by generic lifestyle questions.",
        "in_current_models": "No",
        "sources": [SOURCE_URLS["prediabetes"]],
    },
    {
        "question": "Have you had ongoing fevers, morning stiffness, widespread pain, or persistent malaise for weeks?",
        "conditions": ["Hidden inflammation"],
        "why": "Still nonspecific, but better symptom capture than relying only on sleep and lifestyle proxies.",
        "in_current_models": "No",
        "sources": [SOURCE_URLS["crp"]],
    },
    {
        "question": "Have you had vomiting, diarrhea, heavy sweating, muscle cramps, weakness, or palpitations recently?",
        "conditions": ["Electrolyte deficiency / imbalance"],
        "why": "Higher-yield for acute electrolyte problems than chronic disease history alone.",
        "in_current_models": "No",
        "sources": [SOURCE_URLS["electrolytes"]],
    },
    {
        "question": "Have you ever had a blood transfusion, injected drugs, dialysis, or tattoos/piercings in non-sterile settings?",
        "conditions": ["Hepatitis B & C"],
        "why": "Risk-factor screening is more useful than symptoms because chronic HBV/HCV is often silent.",
        "in_current_models": "Partly",
        "sources": [SOURCE_URLS["hepatitis_b"], SOURCE_URLS["hepatitis_c"]],
    },
]


def load_dataset_columns() -> set[str]:
    df = pd.read_csv(DATASET_PATH, nrows=1)
    return set(df.columns.tolist())


def load_question_labels() -> dict[str, str]:
    df = pd.read_csv(QUESTION_DICT_PATH)
    mapping: dict[str, str] = {}
    if "code" in df.columns and "code and name" in df.columns:
        for _, row in df[["code", "code and name"]].dropna().iterrows():
            code = str(row["code"]).strip().upper()
            label = str(row["code and name"]).strip()
            if code and label:
                mapping[code] = label
    return mapping


def load_lab_names() -> dict[str, str]:
    df = pd.read_csv(LAB_DICT_PATH)
    mapping: dict[str, str] = {}
    for _, row in df.iterrows():
        col = str(row["original_column"]).strip()
        label = str(row.get("label", "")).strip()
        if col and label:
            mapping[col.upper()] = label
    return mapping


def infer_direct_code(feature_name: str) -> str:
    if "___" in feature_name:
        return feature_name.split("___", 1)[0].upper()
    first_token = feature_name.split("_", 1)[0]
    if first_token.isupper() and len(first_token) >= 4:
        return first_token
    return ""


def prettify_feature_name(name: str) -> str:
    if "___" in name:
        return name.split("___", 1)[1].replace("_", " ")
    return name.replace("_", " ")


def resolve_feature(
    raw_feature: str,
    dataset_columns: set[str],
    question_labels: dict[str, str],
    lab_labels: dict[str, str],
) -> dict[str, Any]:
    if raw_feature in ALIAS_MAP:
        resolved = dict(ALIAS_MAP[raw_feature])
    elif raw_feature in dataset_columns:
        code = infer_direct_code(raw_feature)
        resolved = {
            "canonical_key": raw_feature,
            "mapped_dataset_column": raw_feature,
            "nhanes_code": code,
            "feature_type": "questionnaire" if "___" in raw_feature else "lab",
            "notes": "",
        }
    else:
        code = infer_direct_code(raw_feature)
        resolved = {
            "canonical_key": raw_feature,
            "mapped_dataset_column": raw_feature,
            "nhanes_code": code,
            "feature_type": "unresolved-alias",
            "notes": "Raw feature not found directly in merged dataset; retained as supplied.",
        }

    code = resolved.get("nhanes_code", "")
    label = ""
    if code in question_labels:
        label = question_labels[code]
    elif code in lab_labels:
        label = lab_labels[code]
    elif resolved["mapped_dataset_column"] in dataset_columns:
        label = prettify_feature_name(resolved["mapped_dataset_column"])
    else:
        label = prettify_feature_name(raw_feature)

    resolved["display_label"] = label
    resolved["present_in_dataset"] = resolved["mapped_dataset_column"] in dataset_columns or raw_feature in dataset_columns
    return resolved


def build_feature_rows() -> list[dict[str, Any]]:
    dataset_columns = load_dataset_columns()
    question_labels = load_question_labels()
    lab_labels = load_lab_names()

    rows: dict[str, dict[str, Any]] = {}
    for disease_key, _disease_label in DISEASES:
        for raw_feature in RAW_FEATURES[disease_key]:
            resolved = resolve_feature(raw_feature, dataset_columns, question_labels, lab_labels)
            key = resolved["canonical_key"]
            if key not in rows:
                rows[key] = {
                    "canonical_feature": key,
                    "display_label": resolved["display_label"],
                    "mapped_dataset_column": resolved["mapped_dataset_column"],
                    "nhanes_code_match": resolved["nhanes_code"],
                    "feature_type": resolved["feature_type"],
                    "present_in_dataset": int(bool(resolved["present_in_dataset"])),
                    "source_feature_names": set(),
                    "notes": resolved["notes"],
                }
                for disease_col, _ in DISEASES:
                    rows[key][disease_col] = 0
            rows[key]["source_feature_names"].add(raw_feature)
            rows[key][disease_key] = 1

    final_rows: list[dict[str, Any]] = []
    for row in rows.values():
        row["source_feature_names"] = " | ".join(sorted(row["source_feature_names"]))
        final_rows.append(row)

    final_rows.sort(key=lambda item: (item["feature_type"], item["canonical_feature"]))
    return final_rows


def write_csv(rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "canonical_feature",
        "display_label",
        "mapped_dataset_column",
        "nhanes_code_match",
        "feature_type",
        "present_in_dataset",
        "source_feature_names",
        "notes",
        *[disease_key for disease_key, _ in DISEASES],
    ]
    with CSV_OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_combined_flow() -> dict[str, Any]:
    return {
        "metadata": {
            "name": "NHANES Combined Disease Question Flow",
            "version": "1.0.0",
            "generated_on": str(date.today()),
            "source_dataset": str(DATASET_PATH),
            "purpose": "Merged non-lab question flow covering the model features supplied by the user, with shared prompts combined wherever practical.",
            "conditions_covered": [label for _, label in DISEASES],
        },
        "design_notes": [
            "This flow intentionally focuses on questionnaire, demographic, and history items. Lab-only features are excluded from user prompts and listed separately under derived_or_lab_features.",
            "Grouped multi-select questions are used where several binary clinician-diagnosed conditions can be asked once and then split back to NHANES-coded features.",
            "Engineered time features such as sin/cos sleep encodings and social jetlag are derived downstream from bedtime and wake-time questions.",
        ],
        "derived_or_lab_features": [
            "sbp_mean",
            "dbp_mean",
            "pulse_mean",
            "med_count",
            "iron_deficiency",
            "fatigue_ordinal",
            "cos_weekday_wake",
            "sin_weekday_wake",
            "sin_weekday_bedtime",
            "social_jetlag",
            "fasting_glucose_mg_dl",
            "hdl_cholesterol_mg_dl",
            "triglycerides_mg_dl",
            "serum_creatinine_mg_dl",
            "alt_u_l",
            "ast_u_l",
            "ggt_u_l",
            "alp_u_l",
            "total_bilirubin_mg_dl",
            "serum_albumin_g_dl",
            "ferritin_ng_ml",
            "LBXHSCRP_hs_c_reactive_protein_mg_l",
        ],
        "question_groups": [
            {
                "id": "demographics",
                "title": "Core profile",
                "questions": [
                    {
                        "id": "q_age",
                        "text": "What is your age?",
                        "type": "number",
                        "maps_to": ["age_years"],
                        "conditions": ["all"],
                    },
                     {
                         "id": "q_gender",
                         "text": "What sex were you assigned at birth?",
                         "type": "single_select",
                         "options": ["Female", "Male"],
                        "maps_to": ["gender"],
                         "conditions": ["all"],
                     },
                    {
                        "id": "q_body_size",
                        "text": "Enter your current height, weight, and waist size if known.",
                        "type": "grouped_numeric",
                        "maps_to": ["height_cm", "weight_kg", "bmi", "waist_cm"],
                        "conditions": ["menopause", "thyroid", "kidney", "liver", "hidden_inflammation", "hepatitis_bc"],
                    },
                    {
                        "id": "q_demographics_context",
                        "text": "What is your race/ethnicity, education level, country of birth, and household income-to-poverty ratio if known?",
                        "type": "grouped_demographic",
                        "maps_to": ["ethnicity", "education", "country_of_birth", "income_poverty_ratio"],
                        "conditions": ["hepatitis_bc"],
                    },
                ],
            },
            {
                "id": "known_conditions",
                "title": "Known clinician-diagnosed conditions",
                "questions": [
                    {
                        "id": "q_known_dx",
                        "text": "Which of these have you ever been told by a doctor or health professional that you have or had?",
                        "type": "multi_select",
                        "options": [
                            {"label": "High blood pressure", "maps_to": "bpq020___ever_told_you_had_high_blood_pressure"},
                            {"label": "High cholesterol", "maps_to": "bpq080___doctor_told_you___high_cholesterol_level"},
                            {"label": "Diabetes", "maps_to": "diq010___doctor_told_you_have_diabetes"},
                            {"label": "Weak or failing kidneys", "maps_to": "kiq022___ever_told_you_had_weak/failing_kidneys?"},
                            {"label": "Kidney stones", "maps_to": "kiq026___ever_had_kidney_stones?"},
                            {"label": "Arthritis", "maps_to": "mcq160a___ever_told_you_had_arthritis"},
                            {"label": "Heart failure", "maps_to": "mcq160b___ever_told_you_had_congestive_heart_failure"},
                            {"label": "Heart attack", "maps_to": "mcq160e___ever_told_you_had_heart_attack"},
                            {"label": "Stroke", "maps_to": "mcq160f___ever_told_you_had_stroke"},
                            {"label": "Asthma", "maps_to": "mcq010___ever_been_told_you_have_asthma"},
                            {"label": "COPD / emphysema / chronic bronchitis", "maps_to": "mcq160p___ever_told_you_had_copd_emphysema"},
                            {"label": "Liver condition", "maps_to": "mcq160l___ever_told_you_had_any_liver_condition"},
                        ],
                        "conditions": ["thyroid", "kidney", "sleep_disorder", "liver", "prediabetes", "hidden_inflammation", "electrolytes", "hepatitis_bc"],
                    },
                    {
                        "id": "q_medications",
                        "text": "Are you currently taking medicines for high blood pressure, diabetes, anemia, hepatitis, or any prescription medicines at all?",
                        "type": "multi_select_with_count",
                        "options": [
                            {"label": "Blood pressure prescription", "maps_to": "bpq040a___taking_prescription_for_hypertension"},
                            {"label": "Insulin", "maps_to": "diq050___taking_insulin_now"},
                            {"label": "Diabetes pills", "maps_to": "diq070___take_diabetic_pills_to_lower_blood_sugar"},
                            {"label": "Anemia treatment", "maps_to": "mcq053___taking_treatment_for_anemia/past_3_mos"},
                            {"label": "Any prescription medicine in past month", "maps_to": "rxduse___taken_prescription_medicine,_past_month"},
                        ],
                        "derives": ["med_count"],
                        "conditions": ["menopause", "thyroid", "kidney", "anemia", "liver", "electrolytes"],
                    },
                    {
                        "id": "q_general_health",
                        "text": "How would you rate your general health, and were you hospitalized overnight in the last year?",
                        "type": "grouped_single_select",
                        "maps_to": ["huq010___general_health_condition", "huq071___overnight_hospital_patient_in_last_year"],
                        "conditions": ["thyroid", "kidney", "anemia", "liver", "hidden_inflammation", "hepatitis_bc"],
                    },
                ],
            },
            {
                "id": "sleep_fatigue",
                "title": "Sleep and fatigue",
                "questions": [
                    {
                        "id": "q_sleep_quality",
                        "text": "How often do you snore, and has a doctor ever told you that you had trouble sleeping?",
                        "type": "grouped_single_select",
                        "maps_to": ["slq030___how_often_do_you_snore?", "slq050___ever_told_doctor_had_trouble_sleeping?"],
                        "conditions": ["thyroid", "sleep_disorder", "prediabetes", "hidden_inflammation"],
                    },
                    {
                        "id": "q_fatigue",
                        "text": "Over the last two weeks, how often have you felt tired or had little energy?",
                        "type": "single_select",
                        "maps_to": ["dpq040___feeling_tired_or_having_little_energy", "fatigue_ordinal"],
                        "conditions": ["kidney", "sleep_disorder", "anemia", "prediabetes", "electrolytes"],
                    },
                    {
                        "id": "q_sleep_schedule",
                        "text": "What time do you usually go to sleep and wake up on workdays and on weekends, and how many hours do you usually sleep?",
                        "type": "grouped_time_and_duration",
                        "maps_to": [
                            "slq300___usual_sleep_time_on_weekdays_or_workdays",
                            "slq310___usual_wake_time_on_weekdays_or_workdays",
                            "sld012___sleep_hours___weekdays_or_workdays",
                            "slq320___usual_sleep_time_on_weekends",
                            "slq330___usual_wake_time_on_weekends",
                            "sld013___sleep_hours___weekends",
                        ],
                        "derives": ["cos_weekday_wake", "sin_weekday_wake", "sin_weekday_bedtime", "social_jetlag"],
                        "conditions": ["thyroid", "sleep_disorder", "prediabetes", "hidden_inflammation"],
                    },
                ],
            },
            {
                "id": "urinary_kidney",
                "title": "Urinary and kidney symptoms",
                "questions": [
                    {
                        "id": "q_urinary_leakage",
                        "text": "Do you have urinary leakage, and if yes does it happen with physical activity or before reaching the toilet?",
                        "type": "grouped_branching",
                        "maps_to": [
                            "kiq005___how_often_have_urinary_leakage?",
                            "kiq042___leak_urine_during_physical_activities?",
                            "kiq430___how_frequently_does_this_occur?",
                            "kiq044___urinated_before_reaching_the_toilet?",
                            "kiq450___how_frequently_does_this_occur?",
                        ],
                        "conditions": ["menopause", "kidney", "anemia", "prediabetes"],
                    },
                    {
                        "id": "q_nocturia",
                        "text": "How many times do you usually urinate during the night?",
                        "type": "number",
                        "maps_to": ["kiq480___how_many_times_urinate_in_night?"],
                        "conditions": ["thyroid", "kidney", "prediabetes", "electrolytes"],
                    },
                    {
                        "id": "q_kidney_history",
                        "text": "Have you ever been told you had weak or failing kidneys, received dialysis, or had kidney stones?",
                        "type": "multi_select",
                        "options": [
                            {"label": "Weak or failing kidneys", "maps_to": "kiq022___ever_told_you_had_weak/failing_kidneys?"},
                            {"label": "Kidney stones", "maps_to": "kiq026___ever_had_kidney_stones?"},
                        ],
                        "conditions": ["kidney", "electrolytes", "hepatitis_bc"],
                    },
                ],
            },
            {
                "id": "cardiorespiratory_pain",
                "title": "Breathing and pain symptoms",
                "questions": [
                    {
                        "id": "q_breathing",
                        "text": "Do you get shortness of breath when walking up stairs or inclines?",
                        "type": "single_select",
                        "maps_to": ["cdq010___shortness_of_breath_on_stairs/inclines"],
                        "conditions": ["sleep_disorder", "anemia", "liver"],
                    },
                    {
                        "id": "q_pain",
                        "text": "Have you had chest pain or abdominal pain in the past year, and have you seen a doctor about it?",
                        "type": "grouped_branching",
                        "maps_to": [
                            "cdq001___sp_ever_had_pain_or_discomfort_in_chest",
                            "mcq520___abdominal_pain_during_past_12_months?",
                            "mcq540___ever_seen_a_dr_about_this_pain",
                        ],
                        "conditions": ["anemia", "liver"],
                    },
                ],
            },
            {
                "id": "female_reproductive",
                "title": "Female reproductive and menopause context",
                "questions": [
                    {
                        "id": "q_repro_status",
                        "text": "Are you currently pregnant or have you ever been pregnant?",
                        "type": "grouped_single_select",
                        "maps_to": ["pregnancy_status", "rhq131___ever_been_pregnant?"],
                        "conditions": ["menopause", "thyroid"],
                        "show_if": {"gender": ["Female"]},
                    },
                    {
                        "id": "q_periods",
                        "text": "Have you had regular menstrual periods in the past 12 months?",
                        "type": "single_select",
                        "maps_to": ["rhq031___had_regular_periods_in_past_12_months"],
                        "conditions": ["liver", "hidden_inflammation"],
                        "show_if": {"gender": ["Female"]},
                    },
                ],
            },
            {
                "id": "lifestyle",
                "title": "Lifestyle and activity",
                "questions": [
                    {
                        "id": "q_activity",
                        "text": "Which of these do you do: vigorous work activity, vigorous recreational activity, moderate recreational activity, or moderate work activity? How many days per week?",
                        "type": "grouped_activity",
                        "maps_to": [
                            "paq605___vigorous_work_activity",
                            "paq625___number_of_days_moderate_work",
                            "paq650___vigorous_recreational_activities",
                            "paq665___moderate_recreational_activities",
                            "paq670___days_moderate_recreational_activities",
                        ],
                        "conditions": ["menopause", "thyroid", "kidney", "sleep_disorder", "prediabetes", "hidden_inflammation", "electrolytes"],
                    },
                    {
                        "id": "q_alcohol",
                        "text": "How many alcoholic drinks do you usually have per day, and how often do you have 4 or 5 or more drinks on one occasion?",
                        "type": "grouped_numeric",
                        "maps_to": [
                            "alq130___avg_#_alcoholic_drinks/day___past_12_mos",
                            "alq151___ever_have_4/5_or_more_drinks_every_day?",
                            "alq170___past_30_days_#_times_4_5_drinks_on_an_oc",
                        ],
                        "derives": ["ever_heavy_drinker"],
                        "conditions": ["thyroid", "sleep_disorder", "prediabetes", "hidden_inflammation", "liver", "hepatitis_bc"],
                    },
                    {
                        "id": "q_smoking",
                        "text": "Do you smoke now, have you smoked at least 100 cigarettes in your life, and how many cigarettes per day do you smoke?",
                        "type": "grouped_numeric",
                        "maps_to": [
                            "smq020___smoked_at_least_100_cigarettes_in_life",
                            "smq040___do_you_now_smoke_cigarettes?",
                            "smd650___avg_#_cigarettes/day_during_past_30_days",
                        ],
                        "conditions": ["thyroid", "hidden_inflammation", "hepatitis_bc"],
                    },
                    {
                        "id": "q_work_schedule",
                        "text": "What is your overall work schedule, what kind of work did you do last week, and how many hours did you work?",
                        "type": "grouped_work",
                        "maps_to": [
                            "ocq670___overall_work_schedule_past_3_months",
                            "ocd150___type_of_work_done_last_week",
                            "ocq180___hours_worked_last_week_in_total_all_jobs",
                        ],
                        "conditions": ["thyroid", "anemia", "liver", "hidden_inflammation"],
                    },
                ],
            },
            {
                "id": "weight_family_history",
                "title": "Weight and family history",
                "questions": [
                    {
                        "id": "q_weight_context",
                        "text": "Has a doctor ever told you that you were overweight, would you like to weigh more or less, and have you tried to lose weight in the past year?",
                        "type": "grouped_single_select",
                        "maps_to": [
                            "mcq080___doctor_ever_said_you_were_overweight",
                            "whq040___like_to_weigh_more,_less_or_same",
                            "whq070___tried_to_lose_weight_in_past_year",
                        ],
                        "conditions": ["thyroid", "kidney", "liver", "prediabetes", "hidden_inflammation"],
                    },
                    {
                        "id": "q_family_history",
                        "text": "Do you have a close relative with diabetes?",
                        "type": "single_select",
                        "maps_to": ["mcq300c___close_relative_had_diabetes"],
                        "conditions": ["prediabetes"],
                    },
                ],
            },
            {
                "id": "exposures",
                "title": "Exposure and treatment history",
                "questions": [
                    {
                        "id": "q_transfusion",
                        "text": "Have you ever received a blood transfusion, and if yes what year was it?",
                        "type": "grouped_branching",
                        "maps_to": ["mcq092___ever_receive_blood_transfusion", "mcd093___year_receive_blood_transfusion"],
                        "conditions": ["kidney", "anemia", "liver", "hepatitis_bc"],
                    }
                ],
            },
        ],
    }


def write_json() -> None:
    with JSON_OUT.open("w") as f:
        json.dump(build_combined_flow(), f, indent=2)


def write_research_md(rows: list[dict[str, Any]]) -> None:
    by_condition = defaultdict(list)
    for row in rows:
        for disease_key, disease_label in DISEASES:
            if row[disease_key]:
                if row["feature_type"].startswith("questionnaire") or row["feature_type"].startswith("demographic") or row["feature_type"].startswith("derived-questionnaire") or row["feature_type"].startswith("engineered-time") or row["feature_type"].startswith("derived-demographic"):
                    by_condition[disease_label].append(row["canonical_feature"])

    lines: list[str] = []
    lines.append("# NHANES disease-signal research")
    lines.append("")
    lines.append("This note summarizes how the supplied NHANES-based models can flag risk or pre-diagnostic signals using questionnaire and history features, plus where symptom-only screening is intrinsically weak.")
    lines.append("")
    lines.append("This is not diagnostic advice. Several targets here, especially hidden inflammation, electrolyte imbalance, kidney disease, liver disease, and hepatitis B/C, are often silent or only weakly symptomatic until disease is established.")
    lines.append("")
    lines.append("## NHANES fit")
    lines.append("")
    lines.append("- Your merged dataset supports the target conditions mainly through the NHANES Medical Conditions (`MCQ`), Kidney Conditions / Urology (`KIQ`), Sleep (`SLQ` / `SLD`), Reproductive Health (`RHQ`), Hepatitis (`HEQ`), Blood Pressure / Cholesterol (`BPQ`), Diabetes (`DIQ`), alcohol (`ALQ`), smoking (`SMQ` / `SMD`), weight history (`WHQ`), occupation (`OCQ` / `OCD`), and broad laboratory components.")
    lines.append("- For menopause, sleep disorder, kidney, prediabetes, and hepatitis/liver risk, NHANES has good questionnaire coverage.")
    lines.append("- For anemia, hidden inflammation, electrolyte imbalance, and hepatic insufficiency, NHANES symptoms help, but laboratory variables remain the stronger signal source.")
    lines.append("")

    for disease_label, summary in RESEARCH_SUMMARY.items():
        lines.append(f"## {disease_label}")
        lines.append("")
        lines.append(f"- Research take: {summary['focus']}")
        lines.append(f"- NHANES coverage: {summary['nhanes_fit']}")
        lines.append("- Useful non-lab flags:")
        for signal in summary["signals"]:
            lines.append(f"  - {signal}")
        available = sorted(set(by_condition.get(disease_label, [])))
        if available:
            lines.append(f"- Questionnaire/history features already in your models: {', '.join(available)}")
        lines.append("- Sources:")
        for src in summary["sources"]:
            lines.append(f"  - {src}")
        lines.append("")

    lines.append("## Cross-condition design implications")
    lines.append("")
    lines.append("- Symptoms like fatigue, poor sleep, nocturia, and poor general health recur across thyroid, kidney, anemia, prediabetes, hidden inflammation, and electrolyte imbalance, so they should be modeled as shared upstream questions rather than repeated disease-specific questions.")
    lines.append("- Risk-factor logic should outrank symptom logic for prediabetes and hepatitis B/C because both can be asymptomatic.")
    lines.append("- Menopause and thyroid benefit the most from adding targeted net-new symptom questions, because the supplied models currently lean on indirect proxies.")
    lines.append("- Hidden inflammation should be positioned as an inflammatory-risk state rather than a disease label unless supported by lab markers such as hs-CRP.")
    lines.append("")
    lines.append("## Core sources")
    lines.append("")
    for key in ["nhanes_mcq", "nhanes_kiq", "nhanes_slq", "nhanes_rhq", "nhanes_heq", "menopause", "thyroid_hypo", "thyroid_hyper", "kidney_failure", "sleep_apnea", "anemia_symptoms", "liver", "prediabetes", "electrolytes", "crp", "hepatitis_b", "hepatitis_c"]:
        lines.append(f"- {SOURCE_URLS[key]}")
    lines.append("")

    RESEARCH_OUT.write_text("\n".join(lines))


def write_priority_questions_md() -> None:
    lines = [
        "# Priority diagnostic questions (non-lab)",
        "",
        "These are the highest-value non-lab questions to add on top of the existing model features. Several are not present in the supplied model inputs and are therefore recommended as new questions.",
        "",
        "| Question | Best for | Why it matters | Already in model set? | Sources |",
        "|---|---|---|---|---|",
    ]
    for item in PRIORITY_QUESTIONS:
        conditions = ", ".join(item["conditions"])
        sources = "<br>".join(item["sources"])
        lines.append(
            f"| {item['question']} | {conditions} | {item['why']} | {item['in_current_models']} | {sources} |"
        )
    lines.append("")
    lines.append("## Ordering suggestion")
    lines.append("")
    lines.append("1. Ask the high-specificity symptom questions first: night sweats/hot flashes, witnessed apneas, jaundice/dark urine, gestational diabetes history, transfusion / injection-drug / tattoo exposure.")
    lines.append("2. Ask shared symptom clusters next: fatigue, shortness of breath on exertion, nocturia, muscle cramps, weight change, cold/heat intolerance.")
    lines.append("3. Ask broad lifestyle questions after that: smoking, alcohol, activity, and work schedule.")
    lines.append("")
    QUESTIONS_OUT.write_text("\n".join(lines))


def main() -> None:
    rows = build_feature_rows()
    write_csv(rows)
    write_json()
    write_research_md(rows)
    write_priority_questions_md()
    print(f"Wrote {CSV_OUT}")
    print(f"Wrote {JSON_OUT}")
    print(f"Wrote {RESEARCH_OUT}")
    print(f"Wrote {QUESTIONS_OUT}")


if __name__ == "__main__":
    main()
