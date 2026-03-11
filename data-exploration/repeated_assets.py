import plotly.express as px
import pandas as pd

# Create Chart of Assets that are repeated

# Here, we check for assets that have been repaired for corrective work more than once in a span of 90 days.
# The 'Number of Recurrences' is the number of these 90-day intervals present for that specific asset in the data.

def create_repetitive_assets_html(df_tickets_assets_surveys):
    asset_recurrence_counts = df_tickets_assets_surveys['ASSET_NAME'].value_counts()
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
    asset_location_mapping = df_tickets_assets_surveys.groupby('ASSET_NAME')['ASSET_PRIMARY_LOCATION'].apply(lambda x: ', '.join(x.dropna().astype(str).unique())).reset_index()

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
        hover_data=['ASSET_PRIMARY_LOCATION'] # Add ASSET_PRIMARY_LOCATION to hover_data
    )

    # Update layout for better readability
    fig.update_layout(
        xaxis_tickangle=-90,
        xaxis_title_standoff=25,
        height=700
    )

    # Save the interactive chart as an HTML file
    output_html_filename = 'repetitive_tasks_by_asset_interactive_new.html'
    fig.write_html(output_html_filename)

    print(f"Interactive chart saved as '{output_html_filename}'")




