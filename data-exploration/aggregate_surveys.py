import pandas as pd
import numpy as np

# --------------------------------
#  ------------ NEW --------------
# --------------------------------


# ----------------------------------------------------------------
# If the surveys csv ever gets corrupted, redownload V_OM_WORK_TASK_SURVEYS.csv 
# from the box and run the code below.
# ----------------------------------------------------------------


df_surveys = pd.read_csv("/content/V_OM_WORK_TASK_SURVEY.csv")


# Define aggregation dictionary
# Drop SURVEY_QUESTION_ID, SURVEY_QUESTION, SURVEY_TYPE, SURVEY_STATUS
# Aggregate RESPONSE_COMMENTS into a single column
aggregation_rules = {
    'AVERAGE_SURVEY_SCORE': ('SURVEY_SCORES', 'mean'), # Renamed key to match output column name directly
    'WORK_TASK_NAME': ('WORK_TASK_NAME', 'first'),
    'WORK_TASK_STATUS': ('WORK_TASK_STATUS', 'first'),
    'RESPONSIBLE_ORGANIZATION': ('RESPONSIBLE_ORGANIZATION', 'first'),
    'RESPONSIBLE_PERSON': ('RESPONSIBLE_PERSON', 'first'),
    'SERVICE_REQUEST_ID': ('SERVICE_REQUEST_ID', 'first'),
    'SURVEY_SENT_DATE': ('SURVEY_SENT_DATE', 'first'),
    'SURVEY_COMMENTS': ('SURVEY_COMMENTS', 'first'), # Keep original SURVEY_COMMENTS
    'SURVEY_RESPONSE': ('SURVEY_RESPONSE', 'first'),
    'RESPONSE_COMMENTS': ('RESPONSE_COMMENTS', lambda x: '. '.join(x.dropna().astype(str).unique()) if x.dropna().any() else np.nan),
    'SURVEY_QUESTION_DESC': ('SURVEY_QUESTION_DESC', 'first'),
    'BUILDING': ('BUILDING', 'first'),
    'FLOOR': ('FLOOR', 'first'),
    'REQUEST_CLASS': ('REQUEST_CLASS', 'first')
}

# Group by 'WORK_TASK_ID' and apply the aggregation rules
df_surveys_cleaned_v2 = df_surveys.groupby('WORK_TASK_ID').agg(**aggregation_rules).reset_index()

# The AVERAGE_SURVEY_SCORE column is already named correctly by using named aggregation

print(f"Shape of df_surveys_cleaned: {df_surveys_cleaned_v2.shape}")
print("First 5 rows of df_surveys_cleaned:")
print(f"Shape of df_surveys_cleaned: {df_surveys_cleaned_v2.shape}")
display(df_surveys_cleaned_v2.head())

output_csv_filename = 'df_surveys_cleaned.csv'
df_surveys_cleaned_v2.to_csv(output_csv_filename, index=False)

print(f"'df_surveys_cleaned_v2' has been successfully saved to '{output_csv_filename}'")




# --------------------------------
#  ------------ OLD --------------
# --------------------------------

# Define aggregation dictionary to take the mean of 'SURVEY_SCORES' and the first value of other columns
aggregation_rules = {
    'SURVEY_SCORES': 'mean',
    'WORK_TASK_ID': 'first',
    'WORK_TASK_NAME': 'first',
    'WORK_TASK_STATUS': 'first',
    'SURVEY_STATUS': 'first',
    'SURVEY_TYPE': 'first',
    'RESPONSIBLE_ORGANIZATION': 'first',
    'RESPONSIBLE_PERSON': 'first',
    'SERVICE_REQUEST_ID': 'first',
    'SURVEY_SENT_DATE': 'first',
    'SURVEY_COMMENTS': 'first',
    'SURVEY_QUESTION_ID': 'first',
    'SURVEY_QUESTION': 'first',
    'SURVEY_RESPONSE': 'first',
    'RESPONSE_COMMENTS': 'first',
    'SURVEY_QUESTION_DESC': 'first',
    'BUILDING': 'first',
    'FLOOR': 'first',
    'REQUEST_CLASS': 'first'
}

# Group by 'SURVEY_ID' and apply the aggregation rules
df_surveys_cleaned = df_surveys.groupby('SURVEY_ID').agg(aggregation_rules).reset_index()

# Rename the aggregated 'SURVEY_SCORES' column to 'AVERAGE_SURVEY_SCORE'
df_surveys_cleaned = df_surveys_cleaned.rename(columns={'SURVEY_SCORES': 'AVERAGE_SURVEY_SCORE'})

print(f"Shape of df_surveys_cleaned: {df_surveys_cleaned.shape}")
print(f"Number of unique SURVEY_ID entries in df_surveys_cleaned: {df_surveys_cleaned['SURVEY_ID'].nunique()}")
print("First 5 rows of df_surveys_cleaned:")
print(f"Shape of df_surveys_cleaned: {df_surveys_cleaned.shape}")
display(df_surveys_cleaned.head())

# Show most frequent WORK_TASK_ID entries and their counts (some survey IDs have 9 different entries!):
print("Most frequent WORK_TASK_ID entries and their counts:")
display(df_surveys['WORK_TASK_ID'].value_counts())

# Save the cleaned (averaged survey scores) file to csv
output_csv_filename = 'df_surveys_cleaned.csv'
df_surveys_cleaned.to_csv(output_csv_filename, index=False)

print(f"'df_surveys_cleaned' has been successfully saved to '{output_csv_filename}'")


