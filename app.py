"""
Fortlox Security website - entry point.
Sets up the three pages; the pages themselves are home.py, phones.py and cctv.py.
Product lists live in products.py, shared styling and contact details in common.py.
"""

import streamlit as st

from common import find_asset

st.set_page_config(
    page_title="Fortlox Security | Business telephony & CCTV",
    page_icon=find_asset("favicon.png", "emblem.png", "logo.png") or "🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

pages = [
    st.Page("home.py", title="Fortlox Security | Business telephony & CCTV", default=True),
    st.Page("phones.py", title="Phones | Fortlox Security", url_path="phones"),
    st.Page("cctv.py", title="CCTV | Fortlox Security", url_path="cctv"),
]
st.navigation(pages, position="hidden").run()
