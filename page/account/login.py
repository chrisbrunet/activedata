import streamlit as st
import utils.auth as auth
import base64
import datetime
import os

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

image_base64 = get_base64_image("assets/btn_strava_connectwith_orange@2x.png")

client_id = st.secrets["CLIENT_ID"]
client_secret = st.secrets["CLIENT_SECRET"]
app_url = st.secrets["APP_URL"]
    
auth_url = auth.get_authorization_url(app_url, client_id)

st.header("Welcome to ActiveData!")

st.write("This web app can connect to your Strava account and display your activity data through various visualizations. To use this app, please authorize Strava access by clicking the button below:")

html = f"""
<a href="{auth_url}">
    <img src="data:image/png;base64,{image_base64}" width="200">
</a>
"""
st.markdown(html, unsafe_allow_html=True)

try:
    st.session_state.auth_code = st.query_params.code
    st.query_params.clear()
except:
    st.session_state.auth_code = None

if st.session_state.auth_code is not None:
    print(f"\n\n***** NEW LOGIN *****")
    now = datetime.datetime.now()
    print(f"\nCurrent time: {now}")
    print(f"\nauth_code: {st.session_state.auth_code}")
    st.session_state.access_token = auth.request_access_token(client_id, client_secret, st.session_state.auth_code)
    print(f"\naccess_token: {st.session_state.access_token}")

    if st.session_state.access_token is not None:
            try: 
                st.session_state.athlete = st.session_state.access_token['athlete']
            except:
                st.warning("Something went wrong! This happens from time to time. Try refreshing the page and logging in again.")
            else:
                st.session_state.logged_in = True
                st.rerun()

st.container(height=200, border=False)
st.image("assets/api_logo_pwrdBy_strava_stack_light.png", width=130)

