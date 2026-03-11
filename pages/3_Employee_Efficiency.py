import streamlit as st

from utils.data_loader import load_latest_data
from utils.calculations import prepare_dataframe, build_employee_summary
from utils.chart_builders import build_employee_efficiency_chart


st.title("Employee Efficiency")
st.caption("Review labor efficiency, actual hours, and rework by employee.")

df = load_latest_data()
df = prepare_dataframe(df)

if df.empty:
    st.warning("No parsed CSV found yet. Upload and process a PDF from the main page first.")
    st.stop()

employee_summary = build_employee_summary(df)

if employee_summary.empty:
    st.warning("No employee rows were parsed from the latest PDF.")
    st.stop()

fig = build_employee_efficiency_chart(employee_summary, top_n=15)
if fig is not None:
    st.plotly_chart(fig, width="stretch")

st.subheader("Employee Detail")
st.dataframe(employee_summary, width="stretch")