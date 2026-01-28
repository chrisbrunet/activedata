import base64
import streamlit as st
import pandas as pd
import requests
import polyline
import matplotlib.pyplot as plt
import seaborn as sns
import concurrent.futures
from utils.data_mappings import column_rename_map

def connect_to_db(client, database_name="activedata", collection_name="signins"):
    """
    Connects to a MongoDB database and collection
    
    Parameters:
        client: pymongo MongoClient
        database_name: string
        collection_name: string 
    Returns:
        collection: pymongo Collection
    """
    try:
        db = client.get_database(database_name)
        collection = db.get_collection(collection_name)
        print(f"\nConnected to {db.name} database.")
    except Exception as e:
        print(f"\nError connecting to database: {e}")
        collection = None

    return collection

def add_to_db(collection, data):
    """
    Adds a document to the specified MongoDB collection

    Parameters:
        collection: pymongo Collection
        data: Dict
    
    Returns:
        result: InsertOneResult
    """
    try:
        result = collection.insert_one(data)
        print(f"\nDocument inserted with id: {result.inserted_id}")
    except Exception as e:
        print(f"\nError inserting document: {e}")

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

@st.cache_data(show_spinner=False)
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

    df['Activity Link'] = "https://www.strava.com/activities/" + df['Activity ID'].astype(str)

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

@st.cache_data(show_spinner=False)
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

@st.cache_data(show_spinner=False)
def plot_calendar_heatmap(df, year):
    """
    Plots a calendar heatmap of activities over time

    Parameters:
        df: DataFrame
        year: int
    
    Returns:
        none
    """
    # Group by date and sum distances
    df['Start Date'] = pd.to_datetime(df['Start Date'])
    activity_counts = df.groupby(df['Start Date'].dt.date)['Distance (km)'].sum().reset_index(name='Total Distance')
    
    # Create full date range for the year
    start_date = pd.Timestamp(year, 1, 1)
    end_date = pd.Timestamp(year, 12, 31)
    full_dates = pd.date_range(start_date, end_date, freq='D')
    full_df = pd.DataFrame({'Start Date': full_dates, 'Total Distance': 0.0})
    full_df['Start Date'] = full_df['Start Date'].dt.date
    
    # Merge with actual sums
    merged = pd.merge(full_df, activity_counts, on='Start Date', how='left', suffixes=('', '_actual'))
    merged['Total Distance'] = merged['Total Distance_actual'].fillna(0.0)
    merged = merged[['Start Date', 'Total Distance']]
    
    # Create pivot table for heatmap
    merged['Start Date'] = pd.to_datetime(merged['Start Date'])
    merged['Year'] = merged['Start Date'].dt.year
    merged['Month'] = merged['Start Date'].dt.month
    merged['Day'] = merged['Start Date'].dt.day
    
    pivot_table = merged.pivot_table(index='Month', columns='Day', values='Total Distance', aggfunc='sum', fill_value=0)
    
    plt.figure(figsize=(12, 4))
    sns.heatmap(
        pivot_table, 
        cmap="Oranges", 
        linewidths=5, 
        annot=False, 
        cbar=True, 
        cbar_kws={'label': 'Total Distance (km)'},
        yticklabels=[ 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
    plt.xlabel("")
    plt.ylabel("")
    st.pyplot(plt.gcf()) 

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()