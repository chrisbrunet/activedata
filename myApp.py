import streamlit as st
import pandas as pd 
import requests
import matplotlib.pyplot as plt
import seaborn as sns
import pydeck as pdk
import polyline
from streamlit_geolocation import streamlit_geolocation

st.set_page_config(layout="wide")

column_rename_map = {
        "name": "Name",
        "distance": "Distance (km)",
        "moving_time": "Moving Time (s)",
        "elapsed_time": "Elapsed Time (s)",
        "total_elevation_gain": "Elevation Gain (m)",
        "sport_type": "Sport Type",
        "start_date_local": "Start Date",
        "average_speed": "Average Speed (km/h)",
        "max_speed": "Max Speed (km/h)",
        "average_cadence": "Average Cadence (rpm)",
        "average_watts": "Average Watts",
        "max_watts": "Max Watts",
        "kilojoules": "Energy (kJ)",
        "average_heartrate": "Average Heart Rate (bpm)",
        "max_heartrate": "Max Heart Rate (bpm)",
        "elev_high": "Max Elevation (m)",
        "elev_low": "Min Elevation (m)",
        "map": "Map",
    }

if 'data' not in st.session_state:
    st.session_state.data = None

def request_access_token(client_id, client_secret, refresh_token):
    """
    Post request to refresh and get new API access token

    Parameters:
        client_id: string
        client_secret: string
        refresh_token: string
    
    Returns:
        access_token: string
    """
    auth_url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
        'f': 'json'
    }
    print("\nRequesting Access Token...")
    res = requests.post(auth_url, data=payload, verify=False)
    access_token = res.json()['access_token']
    print(f"\nAccess Token = {access_token}")
    return access_token

def get_activity_data(access_token):
    """
    Get request for Strava user activity data 

    Parameters:
        client_id: string
        client_secret: string
        refresh_token: string
    
    Returns:
        all_activities_df: DataFrame
        all_activities_list: list
    """
    print("\nGetting Activity Data...")
    activities_url = "https://www.strava.com/api/v3/athlete/activities"
    header = {'Authorization': 'Bearer ' + access_token}
    request_page_num = 1
    all_activities_list = []
    
    while True: # since max 200 activities can be accessed per request, while loop runs until all activities are loaded
        param = {'per_page': 200, 'page': request_page_num}
        get_activities = requests.get(activities_url, headers=header,params=param).json()
        if len(get_activities) == 0: # exit condition
            break
        all_activities_list.extend(get_activities)
        print(f'\t- Activities: {len(all_activities_list) - len(get_activities)} to {len(all_activities_list)}')
        request_page_num += 1
    
    all_activities_df = pd.DataFrame(all_activities_list)
    return all_activities_df

def format_data(df):
    # Change sport type for all commute rides
    df.loc[df['commute'] == True, 'sport_type'] = 'Commute'

    columns_to_keep = column_rename_map.keys()
    df = df[columns_to_keep]
    df = df.rename(columns=column_rename_map)

    df['Distance (km)'] = df['Distance (km)']/1000
    df['Average Speed (km/h)'] = df['Average Speed (km/h)']*3.6
    df['Max Speed (km/h)'] = df['Max Speed (km/h)']*3.
    df['Start Date'] = pd.to_datetime(df['Start Date']).dt.date

    return df

def get_polylines(df):
    rows = []
    for index, row in df.iterrows():
        map_data = pd.DataFrame([row['Map']])
        polylines = map_data["summary_polyline"].values
        coordinates = polyline.decode(polylines[0])
        for coord in coordinates:
            rows.append({"name": map_data["id"].values, "latitude": coord[0], "longitude": coord[1]})

    polylines_df = pd.DataFrame(rows)

    polylines_df["name"] = polylines_df["name"].apply(lambda x: x[0])

    polylines_transformed = (
        polylines_df.groupby("name")
        .apply(
            lambda group: pd.DataFrame({
                "name": group["name"].iloc[:-1], 
                "start": group[["longitude", "latitude"]].values[:-1].tolist(),
                "end": group[["longitude", "latitude"]].values[1:].tolist(), 
            })
        )
        .reset_index(drop=True)
    )
    return polylines_transformed

def plot_histogram(column_name, bins):
    plt.figure(figsize=(5, 3))
    sns.histplot(filtered_df[column_name], bins=bins, kde=True, color="blue")
    plt.xlabel(column_name)
    plt.ylabel("")  # Remove the y-axis label
    plt.gca().axes.get_yaxis().set_visible(False)  # Hide the y-axis
    st.pyplot(plt.gcf()) 

client_id = st.secrets.CLIENT_ID
client_secret = st.secrets.CLIENT_SECRET
refresh_token = st.secrets.REFRESH_TOKEN

st.header("Strava Data Analyzer")

if st.session_state.data is None:
    with st.spinner("Getting Data..."):
        access_token = request_access_token(client_id, client_secret, refresh_token)
        st.session_state.data = get_activity_data(access_token)

# st.write(st.session_state.data)
formatted_data = format_data(st.session_state.data)

with st.form("filters"):
    sport_types = formatted_data['Sport Type'].unique().tolist()
    sport_types.insert(0, "All")
    sport_type = st.selectbox("Sport Type", sport_types)

    if sport_type == "All":
        filtered_df = formatted_data
    else:
        filtered_df = formatted_data[formatted_data['Sport Type'] == sport_type]

    start_date_default = filtered_df['Start Date'].min()
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", start_date_default)
    with col2:
        end_date = st.date_input("End Date")
        
    filtered_df = filtered_df[(filtered_df['Start Date'] >= start_date) & (filtered_df['Start Date'] <= end_date)]

    st.form_submit_button("Submit")

# TOTALS CONTAINER
with st.container(border=True):

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_activities = filtered_df["Name"].count()
        total_time = filtered_df["Moving Time (s)"].sum()

        st.metric("Total Activities", total_activities)
        st.metric("Total Time (hrs)", round(total_time/60, 1))

    with col2:
        total_dist = filtered_df["Distance (km)"].sum()
        avg_dist = filtered_df["Distance (km)"].mean()

        st.metric("Total Distance (km)", round(total_dist, 2))
        st.metric("Average Distance", round(avg_dist, 2))

    with col3:
        total_elevation = filtered_df["Elevation Gain (m)"].sum()
        avg_elevation = filtered_df["Elevation Gain (m)"].mean()

        st.metric("Total Elevation (m)", round(total_elevation, 2))
        st.metric("Average Elevation (m)", round(avg_elevation, 2))

    with col4:
        max_speed = filtered_df["Max Speed (km/h)"].max()
        avg_speed = filtered_df["Average Speed (km/h)"].mean()

        st.metric("Max Speed (km/h)", round(max_speed, 2))
        st.metric("Average Speed (km/h)", round(avg_speed))

# GRAPHS
with st.expander("Graphs"):

    bins = total_activities // 3
    col1, col2, col3 = st.columns(3)

    with col1:
        plot_histogram("Distance (km)", bins)

    with col2:
        plot_histogram("Elevation Gain (m)", bins)

    with col3: 
        plot_histogram("Average Speed (km/h)", bins)

# MAP
with st.expander("Map"):

    st.write("Click to use current location:")
    location = streamlit_geolocation()
    polylines = get_polylines(filtered_df)

    line_layer = pdk.Layer(
        "LineLayer",
        data=polylines,
        get_source_position="start",
        get_target_position="end",
        get_width=5, 
        get_color=[255, 0, 0], 
        highlight_color=[255, 255, 0],
        picking_radius=10,
        auto_highlight=True,
        pickable=True,
    )

    if location["latitude"] is None:
         view_state = pdk.ViewState(
            latitude=0, longitude=0, controller=True, zoom=2,
        )
    else:
        view_state = pdk.ViewState(
            latitude=location["latitude"], longitude=location["longitude"], controller=True, zoom=9,
        )

    chart = pdk.Deck(layers=line_layer, initial_view_state=view_state)

    event = st.pydeck_chart(chart)  

# MEDIA
with st.expander("Media"):
    st.write("Coming soon...")

# ALL DATA TABLE
with st.expander("Activities Info"):
    st.write(filtered_df)


