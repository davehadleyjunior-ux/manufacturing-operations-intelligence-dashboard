import streamlit as st

from utils.data_loader import load_latest_data
from utils.calculations import prepare_dataframe, build_line_summary
from utils.chart_builders import build_line_efficiency_chart, build_rework_chart


st.title("Line Performance")
st.caption("Compare output, efficiency, and rework across production lines.")

df = load_latest_data()
df = prepare_dataframe(df)

if df.empty:
    st.warning("No parsed CSV found yet. Upload and process a PDF from the main page first.")
    st.stop()

line_summary = build_line_summary(df)

c1, c2 = st.columns(2)

with c1:
    fig1 = build_line_efficiency_chart(line_summary)
    if fig1 is not None:
        st.plotly_chart(fig1, width="stretch")

with c2:
    fig2 = build_rework_chart(line_summary)
    if fig2 is not None:
        st.plotly_chart(fig2, width="stretch")

st.subheader("Line Detail")
st.dataframe(line_summary, width="stretch")