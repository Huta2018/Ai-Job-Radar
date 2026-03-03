import streamlit as st

st.set_page_config(page_title="AI Job Radar")

st.title("🧭 Job Radar")

st.write("Enter your email to start")

email = st.text_input("Email", key="login_email_input")

if st.button("Continue", key="login_continue_btn"):
    if email:
        st.session_state["user_email"] = email.lower()
        st.switch_page("pages/1_Search.py")
    else:
        st.warning("Please enter your email.")
