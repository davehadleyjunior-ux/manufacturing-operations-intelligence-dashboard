import streamlit as st

from utils.data_loader import load_latest_data
from utils.calculations import prepare_dataframe, build_line_summary, calculate_overview_metrics
from utils.chart_builders import build_goal_vs_actual_chart, build_credit_vs_actual_chart


st.title("Overview")
st.caption("Executive snapshot of line output, labor performance, and production efficiency.")

df = load_latest_data()
df = prepare_dataframe(df)

if df.empty:
    st.warning("No parsed CSV found yet. Upload and process a PDF from the main page first.")
    st.stop()

line_summary = build_line_summary(df)
metrics = calculate_overview_metrics(line_summary)

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Goal Units", metrics["goal_units"])
k2.metric("Actual Units", metrics["actual_units"])
k3.metric("Credit Hours", metrics["credit_hours"])
k4.metric("Actual Hours", metrics["actual_hours"])
k5.metric("Labor Efficiency", f"{metrics['labor_efficiency']}%")
k6.metric("Lines Below Goal", metrics["lines_below_goal"])

c1, c2 = st.columns(2)

with c1:
    fig1 = build_goal_vs_actual_chart(line_summary)
    if fig1 is not None:
        st.plotly_chart(fig1, width="stretch")

with c2:
    fig2 = build_credit_vs_actual_chart(line_summary)
    if fig2 is not None:
        st.plotly_chart(fig2, width="stretch")

st.subheader("Line Summary")
st.dataframe(line_summary, width="stretch")