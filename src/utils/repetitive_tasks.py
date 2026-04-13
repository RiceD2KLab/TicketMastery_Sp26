import numpy as np
import pandas as pd



def detect_repetitive_objects(df_tickets_assets, group_cols, num_days, min_days=3, buildings=None, verbose=False):
    """
    Detect repetitive maintenance tasks by object within a specified time window.

    This function identifies corrective tasks that recur on the same object (grouped
    by specified columns) within a target time interval. A task is flagged as repetitive
    if a subsequent task occurs between min_days and num_days after it.

    Parameters
    ----------
    df_tickets_assets : pd.DataFrame
        Merged dataframe of tickets and assets with columns: SERVICE_CLASS,
        REQUEST_CLASS, BUILDING, CREATE_DATE_LTZ, TASK_TYPE, and the grouping columns
        specified by group_cols. Must have ASSET_ID or similar identifier columns.
    group_cols : list of str
        Column names to group by (e.g., ['SERVICE_CLASS', 'REQUEST_CLASS', 'BUILDING']).
        Defines what constitutes a "unique object" for repetition detection.
    num_days : int
        Maximum days between tasks for them to be considered repetitive. Tasks occurring
        more than num_days apart are not flagged as repetitive.
    min_days : int, default 3
        Minimum days between tasks for them to be considered repetitive. Tasks occurring
        fewer than min_days apart are not flagged (e.g., to exclude same-day corrections).
    buildings : list of str, optional
        If provided, filter to only these buildings. If None, all buildings are included.
    verbose : bool, default False
        If True, print diagnostic information including task counts and number of groups.

    Returns
    -------
    tuple of (pd.DataFrame, dict, dict)
        df_tickets_filtered_by_object : pd.DataFrame
            DataFrame of only the repetitive tasks (first task in each repetitive pair).
        object_repetitive_dict : dict
            Maps object_id (str) -> list of row indices of repetitive tasks for that object.
        all_objects_dict : dict
            Maps object_id (str) -> total count of corrective tasks for that object.

    Notes
    -----
    - Only TASK_TYPE='Corrective' tasks are considered for repetition detection.
    """
    df_merged_assets_sorted = df_tickets_assets.sort_values(by=['SERVICE_CLASS', 'REQUEST_CLASS', 'BUILDING', 'CREATE_DATE_LTZ']).reset_index(drop=True)
    repeated_tasks_by_object_list = []
    object_repetitive_dict = {} # Maps object_id -> number of repetitive tickets for that object
    all_objects_dict = {}  # Maps object_id -> total ticket count
    num_days = pd.Timedelta(days=num_days)
    min_days = pd.Timedelta(days=min_days)

    if verbose:
        print(num_days)
        print(f"Number of rows pre-corrective: {len(df_merged_assets_sorted)}")

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


def create_repetitive_assets_html(df_tickets_assets, output_html_filename):
    """
    Create interactive bar chart of asset recurrence counts and save as HTML.

    This function generates an interactive Plotly bar chart showing how many times each
    asset appears in a repetitive tasks dataset. The chart is colored by recurrence count
    and includes asset location information on hover.

    Parameters
    ----------
    df_tickets_assets : pd.DataFrame
        Dataframe of repetitive tasks containing columns: ASSET_NAME and 
        ASSET_PRIMARY_LOCATION. Typically the output of detect_repetitive_objects.
    output_html_filename : str
        Full file path (including filename) where the HTML chart will be saved.
        File extension should be .html.

    Returns
    -------
    None
        Saves interactive HTML file to disk and prints confirmation message.
    """
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




