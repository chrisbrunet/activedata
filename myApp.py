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
if 'all_data_page' not in st.session_state:
    st.session_state.all_data_page = None

login = st.Page("page/account/login.py", title="Log In", icon=":material/login:")
st.session_state.all_data_page = st.Page("page/data/data_view.py", title="All Data", icon=":material/analytics:", default=True)

if st.session_state.logged_in:
    
    pg = st.navigation(
            {
                "Data": [st.session_state.all_data_page],
            }
        )
else:
    pg = st.navigation([login])

pg.run()