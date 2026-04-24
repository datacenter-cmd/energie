import streamlit as st
from auth import require_login
from sidebar_shared import render_sidebar

name = require_login()
render_sidebar(name)

st.markdown("# 💼 VIS Business")
st.info("Sezione in costruzione.")
