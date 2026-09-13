"""
Internal metrics view. Run with: streamlit run dashboard/metrics_dashboard.py
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st

from storage.db import get_feedback_summary

st.set_page_config(page_title="KBA Metrics", layout="centered")
st.title("KBA Metrics Dashboard")

st.subheader("User Feedback")
summary = get_feedback_summary()
col1, col2, col3 = st.columns(3)
col1.metric("Total responses rated", summary["total"])
col2.metric("👍 Positive", summary["positive"])
col3.metric("👎 Negative", summary["negative"])
if summary["total"] > 0:
    st.progress(summary["positive"] / summary["total"])

st.subheader("Latest Evaluation Run")
eval_report_path = Path("docs/eval-report.md")
if eval_report_path.exists():
    st.markdown(eval_report_path.read_text())
else:
    st.info("No evaluation report yet — run `python -m evaluation.run_eval` first.")
