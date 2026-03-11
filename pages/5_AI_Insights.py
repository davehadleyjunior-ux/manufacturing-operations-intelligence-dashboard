import streamlit as st

from utils.data_loader import load_latest_data
from utils.calculations import prepare_dataframe, build_line_summary, build_employee_summary, calculate_overview_metrics


st.title("AI Insights")
st.caption("Rule-based operational insights generated from the latest parsed dataset.")

df = load_latest_data()
df = prepare_dataframe(df)

if df.empty:
    st.warning("No parsed CSV found yet. Upload and process a PDF from the main page first.")
    st.stop()

line_summary = build_line_summary(df)
employee_summary = build_employee_summary(df)
metrics = calculate_overview_metrics(line_summary)

insights = []

if metrics["labor_efficiency"] >= 100:
    insights.append(f"Overall labor efficiency is strong at **{metrics['labor_efficiency']}%**.")
else:
    insights.append(f"Overall labor efficiency is **{metrics['labor_efficiency']}%**, which suggests room to improve labor utilization.")

if metrics["lines_below_goal"] > 0:
    below_goal_lines = line_summary[line_summary["below_goal"]]["line"].tolist()
    insights.append(f"**{metrics['lines_below_goal']}** line(s) are below goal: {', '.join(below_goal_lines)}.")
else:
    insights.append("All lines are currently meeting or exceeding goal units.")

if not employee_summary.empty:
    top_emp = employee_summary.iloc[0]
    insights.append(
        f"Top performer by labor efficiency is **{top_emp['employee']}** on **{top_emp['line']}** at **{top_emp['labor_efficiency']:.1f}%**."
    )

    rework_df = employee_summary.sort_values("rework_hours", ascending=False)
    if not rework_df.empty and rework_df.iloc[0]["rework_hours"] > 0:
        worst_rework = rework_df.iloc[0]
        insights.append(
            f"Highest rework belongs to **{worst_rework['employee']}** on **{worst_rework['line']}** with **{worst_rework['rework_hours']:.1f}** rework hours."
        )

st.subheader("Generated Insights")
for i, insight in enumerate(insights, start=1):
    st.markdown(f"**{i}.** {insight}")

st.subheader("Latest Line Summary")
st.dataframe(line_summary, width="stretch")