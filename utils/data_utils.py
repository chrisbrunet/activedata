import streamlit as st
import pandas as pd
import requests
import polyline
import pymongo
import matplotlib.pyplot as plt
import seaborn as sns
from utils.data_mappings import column_rename_map

@st.cache_data(ttl=600, show_spinner=False)
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

@st.cache_data(ttl=600, show_spinner=False)
def get_activity_data(access_token):
    """
    Get request for Strava user activity data 

    Parameters:
        client_id: string
        client_secret: string
        refresh_token: string
    
    Returns:
        all_activities_df: DataFrame
    """
    print("\nGetting Activity Data...")
    activities_url = "https://www.strava.com/api/v3/athlete/activities"
    header = {'Authorization': 'Bearer ' + access_token}
    request_page_num = 1
    all_activities_list = []

    status_placeholder = st.empty()
    
    while True: # since max 200 activities can be accessed per request, while loop runs until all activities are loaded
        param = {'per_page': 200, 'page': request_page_num}
        get_activities = requests.get(activities_url, headers=header,params=param).json()
        if len(get_activities) == 0: # exit condition
            break
        elif len(get_activities) == 2:
            st.write("Something went wrong!")
            st.write(get_activities["message"])
            break
        all_activities_list.extend(get_activities)
        status_placeholder.write(f'\tActivities: {len(all_activities_list) - len(get_activities) + 1} to {len(all_activities_list)}')
        print(f'\t- Activities: {len(all_activities_list) - len(get_activities) + 1} to {len(all_activities_list)}')
        request_page_num += 1
    
    status_placeholder.empty() 
    print("\nFinished Getting Data")
    all_activities_df = pd.DataFrame(all_activities_list)
    return all_activities_df

def get_activity_media(new_media_rows, access_token):
    """
    Get request for Strava activity media

    Parameters:
        new_media_rows: DataFrame
        access_token: string

    Returns:
        new_media_rows: DataFrame
    """

    print('\t- Getting New Media')
    for index, row in new_media_rows.iterrows(): 
        id = row['Activity ID']
        activity_url = "https://www.strava.com/api/v3/activities/" + str(id)
        header = {'Authorization': 'Bearer ' + access_token}
        recent_act = requests.get(activity_url, headers=header).json()
        
        name = recent_act['name']
        photo = recent_act['photos']['primary']['urls']['600']
        print(f"\t\t{name} - {photo}")

        new_media_rows.loc[index, 'Photo URL'] = photo
    print("\t- Finished Getting Media")        
    return new_media_rows

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

    if polylines_df.empty:
        return None

    else:
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

def plot_histogram(df, column_name, bins):
    plt.figure(figsize=(5, 3))
    sns.histplot(df[column_name], bins=bins, kde=True, color="blue")
    plt.xlabel(column_name)
    plt.ylabel("")
    plt.gca().axes.get_yaxis().set_visible(False)
    st.pyplot(plt.gcf()) 

def init_db_connection(connection_string):
    """
    Initializes connection to MongoDB cluster

    Parameters:
    None

    Returns:
    client (MongoClient): Client for a MongoDB instance

    """
    client = pymongo.MongoClient(connection_string, tls=True)
    return client

def get_collection(connection_string, collection_name):
    """
    Retrieves a collection from the spectra database

    Parameters:
    collection_name (str): name of collection 

    Returns:
    collection: (Collection): specified collection

    """
    client = init_db_connection(connection_string)
    db = client.strava
    collection = db[collection_name]
    return collection

def save_media_to_db(new_strava_media, media_collection):
    print("Saving New Media to DB")
    data_to_insert = new_strava_media.to_dict(orient='records')
    try:
        media_collection.insert_many(data_to_insert)
        print("Data successfully inserted into media_collection.")
    except Exception as e:
        print(f"An error occurred while inserting data: {e}")