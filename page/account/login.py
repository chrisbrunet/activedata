import streamlit as st
import utils.auth as auth
import utils.data_utils as dutil

strava_login_button = dutil.get_base64_image("assets/btn_strava_connectwith_orange@2x.png")

client_id = st.secrets["CLIENT_ID"]
client_secret = st.secrets["CLIENT_SECRET"]
app_url = st.secrets["APP_URL"]
    
auth_url = auth.get_authorization_url(app_url, client_id)

st.header("Welcome to ActiveData!")

st.write("This web app can connect to your Strava account and display your activity data through various visualizations. To use this app, please authorize Strava access by clicking the button below:")

strava_html = f"""
<a href="{auth_url}">
    <img src="data:image/png;base64,{strava_login_button}" width="200">
</a>
"""
st.markdown(strava_html, unsafe_allow_html=True)

try:
    st.session_state.auth_code = st.query_params.code
    st.query_params.clear()
except:
    st.session_state.auth_code = None

if st.session_state.auth_code is not None:
    print(f"\n\n***** NEW LOGIN *****")
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
                st.switch_page(st.session_state.all_data_page)

st.container(height=200, border=False)
st.image("assets/api_logo_pwrdBy_strava_stack_light.png", width=130)

github_html = f"""
[![Created by chrisbrunet](https://img.shields.io/badge/Created_by-chrisbrunet-a1abb3?logo=github)](https://github.com/chrisbrunet/ActiveData)
"""
st.markdown(github_html, unsafe_allow_html=True)