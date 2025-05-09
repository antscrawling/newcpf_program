import streamlit as st

def authenticate(st):
    """
    Handles user authentication and returns whether the user is authenticated.
    :param st: Streamlit module passed from the main script.
    """
    USER = st.secrets["credentials"]["username"]
    PASS = st.secrets["credentials"]["password"]

    if "authenticated" not in st.session_state:
        with st.sidebar:
            st.markdown("<h2 style='color:green;'>🔐 <b>Login</b></h2>", unsafe_allow_html=True)
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login = st.button("Login")

        if login:
            if username == USER and password == PASS:
                st.session_state["authenticated"] = True
            else:
                st.error("Invalid login")

    return st.session_state.get("authenticated", False)