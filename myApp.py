import streamlit as st
import pandas as pd 
import requests
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(layout="wide")

column_rename_map = {
        "name": "Name",
        "distance": "Distance (km)",
        "moving_time": "Moving Time (s)",
        "elapsed_time": "Elapsed Time (s)",
        "total_elevation_gain": "Elevation Gain (m)",
        "sport_type": "Sport Type",
        "start_date_local": "Start Date",
        "average_speed": "Average Speed (m/s)",
        "max_speed": "Max Speed (m/s)",
        "average_cadence": "Average Cadence (rpm)",
        "average_watts": "Average Watts",
        "max_watts": "Max Watts",
        "kilojoules": "Energy (kJ)",
        "average_heartrate": "Average Heart Rate (bpm)",
        "max_heartrate": "Max Heart Rate (bpm)",
        "elev_high": "Max Elevation (m)",
        "elev_low": "Min Elevation (m)",
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
    columns_to_keep = column_rename_map.keys()
    df = df[columns_to_keep]
    df = df.rename(columns=column_rename_map)
    return df

def plot_histogram(column_name):
    plt.figure(figsize=(10, 6))
    sns.histplot(filtered_df[column_name], bins=30, kde=True, color="blue")
    plt.xlabel(column_name)
    plt.ylabel("")  # Remove the y-axis label
    plt.gca().axes.get_yaxis().set_visible(False)  # Hide the y-axis
    st.pyplot(plt.gcf()) 

client_id = st.secrets.CLIENT_ID
client_secret = st.secrets.CLIENT_SECRET
refresh_token = st.secrets.REFRESH_TOKEN

if st.session_state.data is None:
    with st.spinner("Getting Data..."):
        access_token = request_access_token(client_id, client_secret, refresh_token)
        st.session_state.data = get_activity_data(access_token)

formatted_data = format_data(st.session_state.data)


with st.form("filters"):
    sport_types = formatted_data['Sport Type'].unique()
    sport_type = st.selectbox("Sport Type", sport_types)

    filtered_df = formatted_data[formatted_data['Sport Type'] == sport_type]
    st.form_submit_button("Submit")

col1, col2, col3 = st.columns(3)

with col1:
    plot_histogram("Distance (km)")

with col2:
    plot_histogram("Average Speed (m/s)")

with col3: 
    plot_histogram("Elevation Gain (m)")

if filtered_df is not None:
    st.write(filtered_df)
else:
    st.write(formatted_data)


