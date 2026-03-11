import pandas as pd


def display_tickets_without_space(df_tickets):
    # 1. Create a new DataFrame `df_tickets_no_space` by filtering `df_tickets` to include only rows where the 'SPACE' column is null or empty
    df_tickets_no_space = df_tickets[df_tickets['SPACE'].isnull() | (df_tickets['SPACE'] == '')].copy()

    # 2. Print the shape of this new DataFrame
    print(f"Shape of df_tickets_no_space: {df_tickets_no_space.shape}")

    # 3. Calculate the distribution of these tickets by 'BUILDING' (tickets without space)
    building_counts = df_tickets_no_space['BUILDING'].value_counts().reset_index()
    building_counts.columns = ['BUILDING', 'Tickets Without Space']

    # 4. Calculate the total number of tickets for each building from the original df_tickets
    total_building_counts = df_tickets['BUILDING'].value_counts().reset_index()
    total_building_counts.columns = ['BUILDING', 'Total Tickets (Original)']

    # 5. Merge the two count DataFrames
    building_counts_merged = pd.merge(building_counts, total_building_counts, on='BUILDING', how='left')

    # Fill any NaN values in 'Total Tickets (Original)' with 0 (for buildings that might appear in no-space but not original, though unlikely here)
    building_counts_merged['Total Tickets (Original)'] = building_counts_merged['Total Tickets (Original)'].fillna(0).astype(int)

    # Display the merged distribution tabularly
    print("\nDistribution of Tickets without Space Information by Building (with Total Original Tickets):")
    display(building_counts_merged)