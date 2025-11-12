import streamlit as st
import pandas as pd
import requests
import polyline
import matplotlib.pyplot as plt
import seaborn as sns
from utils.data_mappings import column_rename_map

# @st.cache_data(show_spinner=False)
def get_athlete(access_token):
    """
    Get request for athlete stats

    Parameters:
        access_token: string
    
    Returns:
        athlete: Dict
    """
    auth_url = "https://www.strava.com/api/v3/athlete"
    header = {'Authorization': 'Bearer ' + access_token}
    print("\nGetting Athlete...")
    res = requests.get(auth_url, headers=header, verify=False)
    athlete = res.json()
    return athlete

def get_activity_data(access_token):
    """
    Get request for Strava user activity data 

    Parameters:
        access_token: String
    
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
        all_activities_list.extend(get_activities)
        status_placeholder.write(f'\tActivities: {len(all_activities_list) - len(get_activities) + 1} to {len(all_activities_list)}')
        print(f'\n\t- Activities: {len(all_activities_list) - len(get_activities) + 1} to {len(all_activities_list)}')
        request_page_num += 1
    
    status_placeholder.empty() 
    print("\nFinished Getting Data")
    all_activities_df = pd.DataFrame(all_activities_list)
    return all_activities_df

def format_data(df):
    """
    Formats activity data into clean standardized form 

    Parameters:
        df: DataFrame
    
    Returns:
        df: DataFrame
    """
    # Change sport type for all commute rides
    df.loc[df['commute'] == True, 'sport_type'] = 'Commute'
    
    # Ensure all required columns exist
    for col in column_rename_map.keys():
        if col not in df.columns:
            df[col] = None
    
    columns_to_keep = column_rename_map.keys()
    df = df[list(columns_to_keep)]
    df = df.rename(columns=column_rename_map)

    # Convert units
    df['Distance (km)'] = df['Distance (km)'] / 1000
    df['Average Speed (km/h)'] = df['Average Speed (km/h)'] * 3.6
    df['Max Speed (km/h)'] = df['Max Speed (km/h)'] * 3.6
    df['Start Date'] = pd.to_datetime(df['Start Date']).dt.date

    return df

def get_polylines(df):
    """
    Decodes polylines and formats into DataFrame usable with PyDeck

    Parameters:
        df: DataFrame
    
    Returns:
        polylines_transformed: DataFrame
    """
    print('Getting polylines...')
    rows = []
    for index, row in df.iterrows():
        map_data = pd.DataFrame([row['map']])
        polylines = map_data["summary_polyline"].values
        coordinates = polyline.decode(polylines[0])
        activity_name = row["name"]
        distance = round(row["distance"] / 1000, 1)
        elevation = round(row["total_elevation_gain"])
        description = f"{activity_name}\n{distance} km\n{elevation} m"
        for coord in coordinates:
            rows.append({
                "description": description,
                "name": map_data["id"].values, 
                "latitude": coord[0], 
                "longitude": coord[1]
                })

    polylines_df = pd.DataFrame(rows)

    if polylines_df.empty:
        return None

    else:
        polylines_df["name"] = polylines_df["name"].apply(lambda x: x[0])

        polylines_transformed = (
            polylines_df.groupby("name")
            .apply(
                lambda group: pd.DataFrame({
                    "description": group["description"].iloc[:-1],
                    "name": group["name"].iloc[:-1], 
                    "start": group[["longitude", "latitude"]].values[:-1].tolist(),
                    "end": group[["longitude", "latitude"]].values[1:].tolist(), 
                })
            )
            .reset_index(drop=True)
        )
        return polylines_transformed

def plot_histogram(df, column_name, bins):
    """
    Plots user activity stats in a histogram 

    Parameters:
        df: DataFrame
        column_name: String
        bins: int
    
    Returns:
        none
    """
    plt.figure(figsize=(5, 3))
    sns.histplot(df[column_name], bins=bins, kde=True, color="blue")
    plt.xlabel(column_name)
    plt.ylabel("")
    plt.gca().axes.get_yaxis().set_visible(False)
    st.pyplot(plt.gcf()) 