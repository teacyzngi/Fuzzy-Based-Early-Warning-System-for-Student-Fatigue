"""
components/ui.py - Shared constants, session state and small display blocks.
"""

import streamlit as st

DISCLAIMER = "This system is an academic prototype and is not a medical diagnostic tool."
REPO_URL = "https://github.com/teacyzngi/Fuzzy-Based-Early-Warning-System-for-Student-Fatigue"

LEVEL_COLOR = {"LOW": "#10B981", "MODERATE": "#F59E0B", "HIGH": "#EF4444"}
LEVEL_BG = {"LOW": "#D1FAE5", "MODERATE": "#FEF3C7", "HIGH": "#FEE2E2"}
TERM_COLORS = ["#2563EB", "#F59E0B", "#EF4444"]

DEFAULT_INPUT = {"sleep_hours": 7.0, "outstanding_assignments": 3.0,
                 "screen_time_hours": 3.0, "meals_per_day": 3.0}

# README worked example, used on the "How the Model Works" page
WORKED_EXAMPLE = {"sleep_hours": 7.5, "outstanding_assignments": 7.0,
                  "screen_time_hours": 4.0, "meals_per_day": 2.5}


def init_state():
    if "assessed" not in st.session_state:
        st.session_state.assessed = None


def current_input() -> dict:
    """Last submitted input, or the default one."""
    return dict(st.session_state.assessed or DEFAULT_INPUT)


def level_badge(level: str, size: str = "1.6rem") -> str:
    """HTML pill for a fatigue level (rendered with unsafe_allow_html)."""
    return (f"<span style='display:inline-block;padding:0.15em 0.7em;border-radius:999px;"
            f"font-weight:700;font-size:{size};color:{LEVEL_COLOR[level]};"
            f"background:{LEVEL_BG[level]}'>{level}</span>")


def sidebar_footer():
    st.sidebar.caption(DISCLAIMER)
    st.sidebar.caption(f"[Source code on GitHub]({REPO_URL})")
