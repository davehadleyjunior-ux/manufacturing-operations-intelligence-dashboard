import streamlit as st

from utils.data_loader import load_latest_data
from utils.calculations import prepare_dataframe, build_employee_summary, build_line_summary
from utils.chart_builders import build_credit_vs_actual_chart


st.title("Credit Hours")
st.caption("Analyze credit hours earned against actual hours worked.")

df = load_latest_data()
df = prepare_dataframe(df)

if df.empty:
    st.warning("No parsed CSV found yet. Upload and process a PDF from the main page first.")
    st.stop()

line_summary = build_line_summary(df)
employee_summary = build_employee_summary(df)

fig = build_credit_vs_actual_chart(line_summary)
if fig is not None:
    st.plotly_chart(fig, width="stretch")

if not employee_summary.empty:
    detail = employee_summary.copy()
    detail["variance_hours"] = detail["credit_hours"] - detail["actual_hours"]

    st.subheader("Employee Credit Hour Detail")
    st.dataframe(detail, width="stretch")
else:
    st.warning("No employee credit-hour detail was parsed from the latest PDF.")