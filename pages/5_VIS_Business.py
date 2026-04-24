import streamlit as st
from auth import require_login
from sidebar_shared import render_sidebar

st.set_page_config(page_title="VIS Business", page_icon="💼", layout="wide")

result = require_login()
name = result[0] if isinstance(result, tuple) else result
render_sidebar(name)

st.markdown("# 💼 VIS Business")
st.info("Sezione in costruzione.")
