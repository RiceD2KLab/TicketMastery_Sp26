# %%
import pandas as pd
import pydeck as pdk
import streamlit as st
import datetime as dt

# %%
#cache data set 
@st.cache_data
def load_data(csv):
    """
    Loads CSV file into dataframe for computation

    Arguments:
        csv: file path to CSV file

    Returns:
        dataframe: converted dataframe

    """
    df_1 = pd.read_csv(csv)
    df_1 = df_1.dropna(subset=['FEP_BUILDING_X_COORDINATE', 'FEP_BUILDING_Y_COORDINATE'])
    #conversion for streamlit sidebar
    df_1['ASSIGNED_DATE_LTZ'] = pd.to_datetime(df_1['ASSIGNED_DATE_LTZ'])
    return df_1

raw = load_data(r'C:\Users\EC712\OneDrive\Documents\school\DSCI_435\data_sheets\TICKETS_WITH_COORDS.csv')

df_1 = raw.copy()


# %%
#streamlit page initialization
st.set_page_config(page_title="Interactive Map", layout="wide")

min_date = dt.date(year=2021, month=1, day=1)
max_date = dt.date.today()

#streamlit filter options for map
st.sidebar.header("Map Settings")
search_option = st.sidebar.text_input("Key Word Search", value="")
time_option = st.sidebar.slider("Date Range", min_value=min_date, max_value=max_date, value=(min_date, max_date), format="MM-YYYY")
service_option = st.sidebar.pills("Service Class", ['Access Control', 'Building Automation Systems', 'Building Exterior', 'Building Interior', 
                            'Capital Projects', 'Carpentry', 'Cores', 'Custodial', 'Electrical', 'Event Support', 'Facilities', 
                            'Grounds', 'HVAC', 'Instrumentation', 'Lab Equipment', 'Life Safety', 'Lifts', 'Mechanical', 
                            'Moving Equipment', 'Networking', 'Plumbing'], selection_mode="multi", 
                            default=['Access Control', 'Building Automation Systems', 'Building Exterior', 'Building Interior', 
                            'Capital Projects', 'Carpentry', 'Cores', 'Custodial', 'Electrical', 'Event Support', 'Facilities', 
                            'Grounds', 'HVAC', 'Instrumentation', 'Lab Equipment', 'Life Safety', 'Lifts', 'Mechanical', 
                            'Moving Equipment', 'Networking', 'Plumbing'])
building_option = st.sidebar.pills("Building Class", ['Academic', 'Administrative', 'Athletic', 'Infrastructure', 'Residence Hall', 
                            'Sci. Research', 'Student Life', 'Support'], selection_mode="multi", default=[])
task_option = st.sidebar.pills("Task Type", ['Corrective', 'Inspection', 'Preventive'], selection_mode="multi", default=[])
priority_option = st.sidebar.pills("Task Priority", ['1 - Emergency', '2 - Urgent', '3 - Routine', '4 - Customer Requested',
                            '6 - Weather Emergency', '7 - Estimate', '9 - Preventive Maintenance',
                            'R1 - Emergency', 'R2 - Routine'], selection_mode="multi", default=[])

#streamlit filter application
if time_option:
  start_date = pd.to_datetime(time_option[0])
  end_date = pd.to_datetime(time_option[1])
  mask = (df_1['ASSIGNED_DATE_LTZ'] >= start_date) & (df_1['ASSIGNED_DATE_LTZ'] <= end_date)
  df_1 = df_1.loc[mask]
if search_option:
  df_1 = df_1[df_1['DESCRIPTION'].str.contains(search_option, na=False)]
if service_option:
  df_1 = df_1[df_1['SERVICE_CLASS'].isin(service_option)]
if building_option:
  df_1 = df_1[df_1['FEP_BUILDING_CLASS'].isin(building_option)]
if task_option:
  df_1 = df_1[df_1['TASK_TYPE'].isin(task_option)]
if priority_option:
  df_1 = df_1[df_1['TASK_PRIORITY'].isin(priority_option)]

#export filtered data as CSV
if st.sidebar.button(label="Save As CSV"):
  st.sidebar.download_button(label="Download", data=df_1.to_csv(), file_name="data.csv", mime="text/csv", icon=":material/download:")

# %%
#grouping tickets by location for pydeck layer
df_filter = df_1.groupby(['FEP_BUILDING_Y_COORDINATE', 'FEP_BUILDING_X_COORDINATE',  'FEP_BUILDING_DESC', 'FEP_BUILDING_CLASS']).size().reset_index(name='COUNT')
colors = {0: [0, 0, 255], 1: [0, 255, 0], 2: [255, 255, 0], 3: [255, 127, 0], 4: [255, 0, 0]}

if df_filter.size != 0:
  #bin ticket counts with even intervals for coloring
  df_filter['COLOR'] = pd.cut(df_filter['COUNT'], bins=5, labels=False)
  df_filter['COLOR'] = df_filter['COLOR'].map(colors)

records = df_filter.to_dict('records')

#pydeck layer initialization
layer = pdk.Layer(
  'ColumnLayer',
  data=records,
  diskResolution= 12,
  extruded=True,
  radius=10,
  #dynamic elevations for ticket filters
  elevationScale= 500 / df_filter['COUNT'].max(),
  get_position=['FEP_BUILDING_Y_COORDINATE', 'FEP_BUILDING_X_COORDINATE'],
  get_fill_color='COLOR',
  getElevation = 'COUNT',
  pickable=True
)

#set map location
view_state = pdk.ViewState(
    longitude=-95.404182,
    latitude=29.717154,
    zoom=14.7,
    min_zoom=14,
    max_zoom=20,
    pitch=45)

st.pydeck_chart(pdk.Deck(
    layers=[layer], 
    initial_view_state=view_state, 
    tooltip={"text": "Building: {FEP_BUILDING_DESC}\n Type: {FEP_BUILDING_CLASS}\n Tickets: {COUNT} "}
    ), height=700)



