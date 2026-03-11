import pandas as pd
import plotly.express as px


def build_goal_vs_actual_chart(line_summary: pd.DataFrame):
    if line_summary is None or line_summary.empty:
        return None

    chart_df = line_summary[["line", "goal_units", "actual_units"]].copy()
    chart_df.columns = ["Line / Section", "goal_units", "actual_units"]
    chart_df = chart_df.melt(
        id_vars="Line / Section",
        value_vars=["goal_units", "actual_units"],
        var_name="Metric",
        value_name="Units",
    )

    fig = px.bar(
        chart_df,
        x="Line / Section",
        y="Units",
        color="Metric",
        barmode="group",
        title="Goal Units vs Actual Units by Line / Section",
    )
    return fig


def build_credit_vs_actual_chart(line_summary: pd.DataFrame):
    if line_summary is None or line_summary.empty:
        return None

    chart_df = line_summary[["line", "credit_hours", "actual_hours"]].copy()
    chart_df.columns = ["Line / Section", "credit_hours", "actual_hours"]
    chart_df = chart_df.melt(
        id_vars="Line / Section",
        value_vars=["credit_hours", "actual_hours"],
        var_name="Metric",
        value_name="Hours",
    )

    fig = px.bar(
        chart_df,
        x="Line / Section",
        y="Hours",
        color="Metric",
        barmode="group",
        title="Credit Hours vs Actual Hours Worked",
    )
    return fig


def build_line_efficiency_chart(line_summary: pd.DataFrame):
    if line_summary is None or line_summary.empty:
        return None

    fig = px.bar(
        line_summary,
        x="line",
        y="labor_efficiency",
        title="Labor Efficiency by Line / Section",
    )
    return fig


def build_employee_efficiency_chart(employee_summary: pd.DataFrame, top_n: int = 15):
    if employee_summary is None or employee_summary.empty:
        return None

    chart_df = employee_summary.head(top_n).copy()

    fig = px.bar(
        chart_df,
        x="employee",
        y="labor_efficiency",
        color="line",
        title=f"Top {top_n} Employee Efficiency",
    )
    return fig


def build_rework_chart(line_summary: pd.DataFrame):
    if line_summary is None or line_summary.empty:
        return None

    fig = px.bar(
        line_summary,
        x="line",
        y="rework_hours",
        title="Rework Hours by Line / Section",
    )
    return fig