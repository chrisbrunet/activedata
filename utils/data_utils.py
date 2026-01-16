import streamlit as st
import pandas as pd
import requests
import polyline
import matplotlib.pyplot as plt
import seaborn as sns
import concurrent.futures
from utils.data_mappings import column_rename_map

@st.cache_data(show_spinner=False)
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

def fetch_page(page_num, activities_url, header):
    """
    Fetch a single page of activities
    """
    param = {'per_page': 200, 'page': page_num}
    response = requests.get(activities_url, headers=header, params=param)
    return response.json()

@st.cache_data(show_spinner=False)
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
    all_activities_list = []

    status_placeholder = st.empty()

    # Fetch up to 10 pages in parallel (assuming max ~2000 activities)
    max_pages = 10
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_page, page_num, activities_url, header) for page_num in range(1, max_pages + 1)]
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            result = future.result()
            if len(result) > 0:
                all_activities_list.extend(result)
                status_placeholder.write(f'Fetched {len(all_activities_list)} activities so far...')
                print(f'\n\t- Fetched page {i+1}, total activities: {len(all_activities_list)}')
            else:
                # If a page is empty, we can stop, but since concurrent, we continue
                pass

    # Sort activities by start_date_local descending (most recent first)
    all_activities_list.sort(key=lambda x: x.get('start_date_local', ''), reverse=True)

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
    Decodes polylines and formats into DataFrame usable with PyDeck PathLayer

    Parameters:
        df: DataFrame
    
    Returns:
        polylines_df: DataFrame with 'name', 'description', 'path'
    """
    print('Getting polylines...')
    rows = []
    for index, row in df.iterrows():
        map_data = pd.DataFrame([row['map']])
        polylines = map_data["summary_polyline"].values
        if pd.isna(polylines[0]) or polylines[0] == '':
            continue  # Skip if no polyline
        coordinates = polyline.decode(polylines[0])
        activity_name = row["name"]
        distance = round(row["distance"] / 1000, 1)
        elevation = round(row["total_elevation_gain"])
        description = f"{activity_name}\n{distance} km\n{elevation} m"
        
        # Path as list of [lon, lat]
        path = [[coord[1], coord[0]] for coord in coordinates] 
        rows.append({
            "name": map_data["id"].values[0],
            "description": description,
            "path": path
        })

    polylines_df = pd.DataFrame(rows)
    return polylines_df if not polylines_df.empty else None

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