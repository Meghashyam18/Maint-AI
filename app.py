import streamlit as st

from utils.data_loader import load_and_prepare_data
from pages.maintenance_history import show_maintenance_history
from pages.new_inspection import show_new_inspection
from pages.generated_reports import show_generated_reports


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Field Maintenance Report Generator",
    page_icon="🔧",
    layout="wide"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }

    .main-header {
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(128, 128, 128, 0.25);
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="main-header">
        <h1>🔧 AI Field Maintenance Report Generator</h1>
        <p>
            Review machine maintenance history, perform new inspections,
            upload machine evidence, generate AI-assisted maintenance reports,
            and download previously generated reports.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# LOAD DATA
# ============================================================

df, display_df = load_and_prepare_data()


# ============================================================
# NAVIGATION
# ============================================================

st.sidebar.title("🔧 Navigation")

page = st.sidebar.radio(
    "Select Page",
    [
        "Maintenance History",
        "MAINT AI",
        "Generated Reports"
    ]
)


# ============================================================
# SHOW SELECTED PAGE
# ============================================================

if page == "Maintenance History":
    show_maintenance_history(df, display_df)

elif page == "MAINT AI":
    show_new_inspection(df, display_df)

elif page == "Generated Reports":
    show_generated_reports()