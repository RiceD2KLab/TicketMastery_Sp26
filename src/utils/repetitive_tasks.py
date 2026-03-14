import numpy as np
import pandas as pd

"""
Docstring
Detects repetitive tasks based on the object defined by the grouping in group_cols.

A task is defined as 'repetitive' if there is a single other subsequent task in the same
'object' grouping that occurs between num_days and min_days days.
"""

def detect_repetitive_objects(df_tickets_assets, group_cols, num_days, min_days=3, buildings=None, verbose=False):
    df_merged_assets_sorted = df_tickets_assets.sort_values(by=['SERVICE_CLASS', 'REQUEST_CLASS', 'BUILDING', 'CREATE_DATE_LTZ']).reset_index(drop=True)
    repeated_tasks_by_object_list = []
    object_repetitive_dict = {} # Maps object_id -> number of repetitive tickets for that object
    all_objects_dict = {}  # Maps object_id -> total ticket count
    num_days = pd.Timedelta(days=num_days)
    min_days = pd.Timedelta(days=min_days)

    if verbose:
        print(num_days)
        print(f"Number of columns pre-corrective: {len(df_merged_assets_sorted)}")

    df_corrective = df_merged_assets_sorted[
        df_merged_assets_sorted['TASK_TYPE'] == 'Corrective'
    ]

    if buildings:
        df_corrective = df_merged_assets_sorted[
            df_merged_assets_sorted['BUILDING'].isin(buildings)
        ]

    if verbose:
        print(f"Number of corrective tasks: {len(df_corrective)}")
        print(f"Number of unique objects (groups): {df_corrective.groupby(group_cols).ngroups}")

    for group_key, group in df_corrective.groupby(group_cols):
        object_id = tuple(group_key) if isinstance(group_key, (list, tuple)) else (group_key,)
        object_id_str = ' | '.join(str(k) for k in object_id)
        all_objects_dict[object_id_str] = len(group)  # Track total tickets for every object

        for i in range(len(group)):
            current_task = group.iloc[i]
            current_task_time = current_task['CREATE_DATE_LTZ']
            current_task_index = group.index[i]
            subsequent_tasks = group.iloc[i+1:]

            for j in range(len(subsequent_tasks)):
                other_task = subsequent_tasks.iloc[j]
                other_task_time = other_task['CREATE_DATE_LTZ']
                time_difference = other_task_time - current_task_time

                if pd.isna(time_difference):
                    continue
                if time_difference <= num_days and time_difference >= min_days:
                    repeated_tasks_by_object_list.append(current_task.to_dict())
                    if object_id_str not in object_repetitive_dict:
                        object_repetitive_dict[object_id_str] = []
                    object_repetitive_dict[object_id_str].append(current_task_index)
                    break
                elif time_difference > num_days:
                    break

    df_tickets_filtered_by_object = pd.DataFrame(repeated_tasks_by_object_list)

    if verbose:
        print(f"Found {len(df_tickets_filtered_by_object)} repetitive tasks by object within {num_days.days} days.")

    return df_tickets_filtered_by_object, object_repetitive_dict, all_objects_dict



# Here, we check for assets that have been repaired for corrective work more than once in a span of 90 days.
# The 'Number of Recurrences' is the number of these 90-day intervals present for that specific asset in the data.

def create_repetitive_assets_html(df_tickets_assets, output_html_filename):
    asset_recurrence_counts = df_tickets_assets['ASSET_NAME'].value_counts()
    print("Recurrence counts of ASSET_NAME calculated:")
    print(asset_recurrence_counts.head())

    # Create a temporary DataFrame from the asset_recurrence_counts Series
    df_plot_asset_recurrence = pd.DataFrame({
        'ASSET_NAME': asset_recurrence_counts.index,
        'Recurrence Count': asset_recurrence_counts.values
    })

    # Get a mapping of ASSET_NAME to ASSET_PRIMARY_LOCATION from the original filtered data
    # Since an ASSET_NAME might appear multiple times but always with the same primary location
    # (or we want to show a representative one), we'll take the first unique location.
    asset_location_mapping = df_tickets_assets.groupby('ASSET_NAME')['ASSET_PRIMARY_LOCATION'].apply(lambda x: ', '.join(x.dropna().astype(str).unique())).reset_index()

    # Merge the location information into the plot DataFrame
    df_plot_asset_recurrence = pd.merge(df_plot_asset_recurrence, asset_location_mapping, on='ASSET_NAME', how='left')

    # Create an interactive bar chart using Plotly Express
    fig = px.bar(
        df_plot_asset_recurrence,
        x='ASSET_NAME',
        y='Recurrence Count',
        title='Recurrence Counts of Repetitive Tasks by Asset Name (Interactive)',
        color='Recurrence Count',
        color_continuous_scale=px.colors.sequential.Viridis,
        labels={'ASSET_NAME': 'Asset Name', 'Recurrence Count': 'Number of Recurrences', 'ASSET_PRIMARY_LOCATION': 'Primary Location'},
        hover_data=['ASSET_PRIMARY_LOCATION'] 
    )

    # Update layout for better readability
    fig.update_layout(
        xaxis_tickangle=-90,
        xaxis_title_standoff=25,
        height=700
    )

    # Save the interactive chart as an HTML file
    fig.write_html(output_html_filename)

    print(f"Interactive chart saved as '{output_html_filename}'")




