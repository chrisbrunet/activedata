import datetime
import time
import utils.auth as auth
import utils.data_utils as dutil
import streamlit as st
from streamlit_cookies_controller import CookieController

controller = CookieController()
time.sleep(10)

try:
    st.set_page_config(layout='wide')
except BaseException as e:
    print(e)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "logged_out" not in st.session_state:
    st.session_state.logged_out = False
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "athlete" not in st.session_state:
    st.session_state.athlete = None

if st.session_state.logged_out:
    controller.remove('access_token')
    st.session_state.logged_out = False

# Check for existing access token cookie and refresh if valid
try:
    access_token_cookie = controller.get('access_token')
    refresh_token = access_token_cookie['refresh_token']
    expiry_date = access_token_cookie['expires_at']
    datetime_expiry_date = datetime.datetime.fromtimestamp(expiry_date)
    print('\nPrevious Access Token Found')
    if datetime_expiry_date > datetime.datetime.now():
        print('Logging in with Refresh Token...')
        client_id = st.secrets["CLIENT_ID"]
        client_secret = st.secrets["CLIENT_SECRET"]
        st.session_state.access_token = auth.refresh_access_token(client_id, client_secret, refresh_token) 
        if st.session_state.access_token is not None:
            st.session_state.athlete = dutil.get_athlete(st.session_state.access_token['access_token'])
            try:
                athlete_id = st.session_state.athlete['id']
                st.session_state.logged_in = True
                print('Successfully logged in with refresh token')
            except:
                st.warning("Something went wrong! This happens from time to time. Try refreshing the page and logging in again.")
        else:
            print('Failed to refresh token')
    else:
        print('Refresh Code Expired')
except:
    print('\nNo Previous Access Token')

login = st.Page("page/account/login.py", title="Log In", icon=":material/login:")

# setting up page navigation
if st.session_state.logged_in:

    controller.set('access_token', st.session_state.access_token)
    
    # linking pages to .py files
    allData = st.Page("page/data/data_view.py", title="All Data", icon=":material/analytics:", default=True)

    pg = st.navigation(
            {
                "Data": [allData],
            }
        )
else:
    pg = st.navigation([login])

pg.run()