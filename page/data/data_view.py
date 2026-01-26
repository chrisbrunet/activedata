import streamlit as st
import pymongo
import datetime
import pydeck as pdk
from utils import data_utils as dutil
from streamlit_geolocation import streamlit_geolocation

if 'data' not in st.session_state:
    st.session_state.data = None
if 'polylines' not in st.session_state:
    st.session_state.polylines = None

def logout():
    print('Logging out...')
    st.session_state.logged_in = False
    st.session_state.access_token = None

st.image("assets/logo.png", width=250)

access_token = st.session_state.access_token['access_token']
athlete = st.session_state.athlete
athlete_id = athlete['id']
athlete_link = f'https://www.strava.com/athletes/{athlete_id}'

if st.session_state.data is None:
    with st.spinner("Getting Data..."):
        access_code = st.session_state.access_token['access_token']
        st.session_state.data = dutil.get_activity_data(access_code)
        st.session_state.polylines = dutil.get_polylines(st.session_state.data)

        CONNECTION_STRING = st.secrets["MONGODB_CONNECTION_STRING"]
        client = pymongo.MongoClient(CONNECTION_STRING)
        signins_collection = dutil.connect_to_db(client, collection_name="signins")

        now = datetime.datetime.now()
        login_details = st.session_state.athlete.copy()
        login_details['login_time'] = now
        login_details['athlete_id'] = login_details.pop('id')

        dutil.add_to_db(signins_collection, login_details)

if not st.session_state.data.empty:
    formatted_data = dutil.format_data(st.session_state.data)

    # PROFILE & FILTERS SIDEBAR
    with st.sidebar:

        col11, col12 = st.columns(2)
        firstname = athlete['firstname']
        lastname = athlete['lastname']
        profile_photo = athlete['profile']

        with col11:
            st.header(f"{firstname} {lastname}")

            if not profile_photo == "avatar/athlete/large.png":
                st.image(profile_photo)

            link = f"""
                <a href="{athlete_link}" style="color: #FC4C02; font-weight: bold; text-decoration: underline;">
                    View on Strava
                </a>
            """
            st.markdown(link, unsafe_allow_html=True)

        st.divider()

        sport_types = formatted_data['Sport Type'].unique().tolist()
        sport_type = st.multiselect("Sport Type", sport_types)

        if not sport_type:
            filtered_df = formatted_data
        else:
            filtered_df = formatted_data[formatted_data['Sport Type'].isin(sport_type)]

        start_date_default = filtered_df['Start Date'].min()
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", start_date_default)
        with col2:
            end_date = st.date_input("End Date")
        
        filtered_df = filtered_df[(filtered_df['Start Date'] >= start_date) & (filtered_df['Start Date'] <= end_date)]

        if "AlpineSki" in sport_types:
            include_apline_skis = st.checkbox("Include Alpine Skis in Elevation")

        st.divider()
        col3, col4 = st.columns(2)
        with col3:
            logout_button = st.button("Log Out", on_click=logout)

        with col4:
            st.image("assets/api_logo_pwrdBy_strava_stack_light.png", use_container_width="always")

        github_html = f"""
        [![Created by chrisbrunet](https://img.shields.io/badge/Created_by-chrisbrunet-a1abb3?logo=github)](https://github.com/chrisbrunet/ActiveData)
        """
        st.markdown(github_html, unsafe_allow_html=True)

    # TOTALS CONTAINER
    with st.container(border=True):

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_activities = filtered_df["Name"].count()
            total_time = filtered_df["Moving Time (s)"].sum()

            st.metric("Total Activities", f"{total_activities:,}")
            st.metric("Total Time (hrs)", f"{round(total_time/60/60, 1):,}")

        with col2:
            total_dist = filtered_df["Distance (km)"].sum()
            avg_dist = filtered_df["Distance (km)"].mean()

            st.metric("Total Distance (km)", f"{round(total_dist, 1):,}")
            st.metric("Average Distance (km)", f"{round(avg_dist, 1):,}")

        with col3:
            try:
                if include_apline_skis:
                    total_elevation = filtered_df["Elevation Gain (m)"].sum()
                    avg_elevation = filtered_df["Elevation Gain (m)"].mean()
                else:
                    total_elevation = filtered_df[filtered_df["Sport Type"] != "AlpineSki"]["Elevation Gain (m)"].sum()
                    avg_elevation = filtered_df[filtered_df["Sport Type"] != "AlpineSki"]["Elevation Gain (m)"].mean()
            except: 
                total_elevation = filtered_df["Elevation Gain (m)"].sum()
                avg_elevation = filtered_df["Elevation Gain (m)"].mean()

            st.metric("Total Elevation (m)", f"{round(total_elevation, 1):,}")
            st.metric("Average Elevation (m)", f"{round(avg_elevation, 1):,}")

        with col4:
            max_speed = filtered_df["Max Speed (km/h)"].max()
            avg_speed = filtered_df["Average Speed (km/h)"].mean()

            st.metric("Max Speed (km/h)", f"{round(max_speed, 1):,}")
            st.metric("Average Speed (km/h)", f"{round(avg_speed, 1):,}")

    # GRAPHS
    with st.expander("Graphs"):
        if total_activities < 3:
            st.write("Not Enough Data :(")
        else:
            bins = total_activities // 3
            col1, col2, col3 = st.columns(3)

            with col1:
                dutil.plot_histogram(filtered_df, "Distance (km)", bins)

            with col2:
                dutil.plot_histogram(filtered_df, "Elevation Gain (m)", bins)

            with col3: 
                dutil.plot_histogram(filtered_df, "Average Speed (km/h)", bins)
            
            selectbox_years = sorted({d.year for d in filtered_df['Start Date'].unique()}, reverse=True)
            selected_year = st.selectbox("Select Year for Calendar Heatmap", selectbox_years)
            dutil.plot_calendar_heatmap(filtered_df, selected_year)

    # MAP
    with st.expander("Map"):

        id_list = filtered_df['Map'].apply(lambda x: x['id']).tolist()
        filtered_polylines = st.session_state.polylines[st.session_state.polylines['name'].isin(id_list)]

        if filtered_polylines is not None:
            st.write("Click to use current location:")
            location = streamlit_geolocation()

            path_layer = pdk.Layer(
                "PathLayer",
                data=filtered_polylines,
                get_path="path",
                get_width=5,
                # width_scale=10,
                width_min_pixels=1,
                get_color=[255, 0, 0],
                highlight_color=[255, 255, 0],
                picking_radius=15,
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

            chart = pdk.Deck(layers=path_layer, initial_view_state=view_state, map_style="light", tooltip={'text': '{description}'})
            event = st.pydeck_chart(chart)
        else:
            st.write("No Map Data For This Activity :(")  

    # ALL DATA TABLE
    with st.expander("Activities Info Table"):
        display_data = filtered_df
        columns_to_drop = ['Activity ID', 'Map', 'Photos']
        display_data = display_data.drop(columns=columns_to_drop)
        st.write(display_data)