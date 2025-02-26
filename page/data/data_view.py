import streamlit as st
import pydeck as pdk
import pandas as pd
from utils import data_utils as dutil
from streamlit_geolocation import streamlit_geolocation

if 'data' not in st.session_state:
    st.session_state.data = None
if 'media_data' not in st.session_state:
    st.session_state.media_data = None

def logout():
    st.session_state.logged_in = False
    st.session_state.refresh_token = None
    st.session_state.access_token = None

athlete_id = st.session_state.access_token['athlete']['id']
athlete_link = f'https://www.strava.com/athletes/{athlete_id}'

if st.session_state.data is None:
    with st.spinner("Getting Data..."):
        access_code = st.session_state.access_token['access_token']
        st.session_state.data = dutil.get_activity_data(access_code)

if not st.session_state.data.empty:
    formatted_data = dutil.format_data(st.session_state.data)

    # PROFILE & FILTERS SIDEBAR
    with st.sidebar:

        col11, col12 = st.columns(2)
        firstname = st.session_state.access_token['athlete']['firstname']
        lastname = st.session_state.access_token['athlete']['lastname']
        profile_photo = st.session_state.access_token['athlete']['profile']

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
            if include_apline_skis:
                total_elevation = filtered_df["Elevation Gain (m)"].sum()
                avg_elevation = filtered_df["Elevation Gain (m)"].mean()
            else:
                total_elevation = filtered_df[filtered_df["Sport Type"] != "AlpineSki"]["Elevation Gain (m)"].sum()
                avg_elevation = filtered_df[filtered_df["Sport Type"] != "AlpineSki"]["Elevation Gain (m)"].mean()

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

    # MAP
    with st.expander("Map"):

        polylines = dutil.get_polylines(filtered_df)

        if polylines is not None:
            st.write("Click to use current location:")
            location = streamlit_geolocation()

            line_layer = pdk.Layer(
                "LineLayer",
                data=polylines,
                get_source_position="start",
                get_target_position="end",
                get_width=1, 
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

            chart = pdk.Deck(layers=line_layer, initial_view_state=view_state, map_style="light", tooltip={'text': '{description}'})
            event = st.pydeck_chart(chart)
        else:
            st.write("No Map Data For This Activity :(")  

    # ALL DATA TABLE
    with st.expander("Activities Info Table"):
        display_data = filtered_df
        columns_to_drop = ['Activity ID', 'Map', 'Photos']
        display_data = display_data.drop(columns=columns_to_drop)
        st.write(display_data)