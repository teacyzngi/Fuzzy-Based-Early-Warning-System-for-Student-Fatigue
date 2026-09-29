"""
app.py - Streamlit entry point (navigation only).

Only presentation code lives in app.py, pages/ and components/. The
algorithmic core is in:
    fuzzy_model.py      Mamdani fuzzy inference (fatigue index)
    recommendation.py   forward-chaining knowledge base (recommended actions)
    evaluation.py       survey validation and agreement statistics

Run locally:
    pip install -r requirements.txt
    streamlit run app.py
"""

import streamlit as st

from components.ui import init_state, sidebar_footer

st.set_page_config(page_title="Student Fatigue Early Warning", page_icon="🧭", layout="wide")
init_state()

pages = [
    st.Page("pages/home.py", title="Home", icon=":material/home:", default=True),
    st.Page("pages/assessment.py", title="Assessment", icon=":material/edit_note:"),
    st.Page("pages/model.py", title="How the Model Works", icon=":material/account_tree:"),
    st.Page("pages/survey.py", title="Survey Data & Evaluation", icon=":material/bar_chart:"),
    st.Page("pages/about.py", title="About & Limitations", icon=":material/info:"),
]
nav = st.navigation(pages)
sidebar_footer()
nav.run()
