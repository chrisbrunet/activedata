import streamlit as st
import utils.auth as auth

if "refresh_token" not in st.session_state:
    st.session_state.refresh_token = None
if "access_token" not in st.session_state:
    st.session_state.access_token = None

client_id = st.secrets.CLIENT_ID
client_secret = st.secrets.CLIENT_SECRET
app_url = st.secrets.APP_URL

auth_url = auth.get_authorization_url(app_url, client_id)

st.header("Welcome to the Strava Data Analyzer!")

st.write("This web app can connect to your Strava account and display all of you activity data.")

st.write("To use this app, please authorize Strava access by clicking the button below:")

link = f"""<a href="{auth_url}" onclick="window.location.href='{auth_url}'; return false;" class="button">👤 Login and Authenticate</a>"""
st.markdown(link, unsafe_allow_html=True)

try:
    st.session_state.refresh_token = st.query_params.code
    st.query_params.clear()
except:
    st.session_state.refresh_token = None

if st.session_state.refresh_token is not None:
    st.session_state.access_token = auth.request_access_token(client_id, client_secret, st.session_state.refresh_token)

    if st.session_state.access_token is not None:
        st.session_state.logged_in = True

        firstname = st.session_state.access_token['athlete']['firstname']
        lastname = st.session_state.access_token['athlete']['lastname']
        profile_photo = st.session_state.access_token['athlete']['profile']

        st.write(f"Welcome: {firstname} {lastname}!")
        st.image(profile_photo)

        st.button("Proceed to Site?")
