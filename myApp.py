import streamlit as st

try:
    st.set_page_config(layout='wide')
except BaseException as e:
    print(e)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "athlete" not in st.session_state:
    st.session_state.athlete = None

login = st.Page("page/account/login.py", title="Log In", icon=":material/login:")
allData = st.Page("page/data/data_view.py", title="All Data", icon=":material/analytics:", default=True)

if st.session_state.logged_in:
    
    pg = st.navigation(
            {
                "Data": [allData],
            }
        )
else:
    pg = st.navigation([login])

pg.run()