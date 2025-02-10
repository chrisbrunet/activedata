import streamlit as st

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

login = st.Page("page/account/login.py", title="Log In", icon=":material/login:")

# setting up page navigation
if st.session_state.logged_in:

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