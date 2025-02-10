import streamlit as st
import utils.auth as auth
import base64

if "refresh_token" not in st.session_state:
    st.session_state.refresh_token = None
if "access_token" not in st.session_state:
    st.session_state.access_token = None

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

image_base64 = get_base64_image("assets/strava_icon.png")

client_id = st.secrets.CLIENT_ID
client_secret = st.secrets.CLIENT_SECRET
app_url = st.secrets.APP_URL

auth_url = auth.get_authorization_url(app_url, client_id)

st.header("Welcome to the Strava Data Analyzer!")

st.write("This web app can connect to your Strava account and display all of you activity data. To use this app, please authorize Strava access by clicking the button below:")

# st.link_button("Login with Strava 🏃", auth_url)
html = f"""
<a href="{auth_url}">
    <img src="data:image/png;base64,{image_base64}" width="200">
</a>
"""
st.markdown(html, unsafe_allow_html=True)

try:
    st.session_state.refresh_token = st.query_params.code
    st.query_params.clear()
except:
    st.session_state.refresh_token = None

if st.session_state.refresh_token is not None:
    st.session_state.access_token = auth.request_access_token(client_id, client_secret, st.session_state.refresh_token)

    if st.session_state.access_token is not None:
        st.session_state.logged_in = True
        st.rerun()
