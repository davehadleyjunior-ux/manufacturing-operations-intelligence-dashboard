import pandas as pd


def _to_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    df = df.copy()
    for col in cols:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace("%", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(
            columns=[
                "line",
                "employee",
                "zone",
                "hire_date",
                "goal_units",
                "actual_units",
                "credit_hours",
                "actual_hours",
                "labor_efficiency",
                "rework_hours",
                "breaks_hours",
                "source_page",
                "source_pdf",
            ]
        )

    df = df.copy()
    numeric_cols = [
        "goal_units",
        "actual_units",
        "credit_hours",
        "actual_hours",
        "labor_efficiency",
        "rework_hours",
        "breaks_hours",
    ]
    df = _to_numeric(df, numeric_cols)

    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    if "line" not in df.columns:
        df["line"] = "Unknown"

    df["line"] = df["line"].fillna("Unknown").replace("", "Unknown")

    if "employee" not in df.columns:
        df["employee"] = ""

    return df


def build_line_summary(df: pd.DataFrame) -> pd.DataFrame:
    df = prepare_dataframe(df)

    if df.empty:
        return pd.DataFrame(
            columns=[
                "line",
                "goal_units",
                "actual_units",
                "credit_hours",
                "actual_hours",
                "rework_hours",
                "employee_count",
                "labor_efficiency",
                "below_goal",
            ]
        )

    grouped = (
        df.groupby("line", dropna=False)
        .agg(
            goal_units=("goal_units", "max"),
            actual_units=("actual_units", "max"),
            credit_hours=("credit_hours", "sum"),
            actual_hours=("actual_hours", "sum"),
            rework_hours=("rework_hours", "sum"),
            employee_count=("employee", lambda s: s.astype(str).replace("", pd.NA).dropna().nunique()),
        )
        .reset_index()
    )

    grouped["goal_units"] = grouped["goal_units"].fillna(0)
    grouped["actual_units"] = grouped["actual_units"].fillna(0)

    # Fallbacks so charts still work even if the PDF had partial data
    grouped.loc[grouped["actual_units"] <= 0, "actual_units"] = grouped["employee_count"]
    grouped.loc[grouped["goal_units"] <= 0, "goal_units"] = grouped["actual_units"]

    grouped["labor_efficiency"] = 0.0
    mask = grouped["actual_hours"] > 0
    grouped.loc[mask, "labor_efficiency"] = (
        grouped.loc[mask, "credit_hours"] / grouped.loc[mask, "actual_hours"] * 100
    )

    grouped["below_goal"] = grouped["actual_units"] < grouped["goal_units"]

    return grouped.sort_values("line").reset_index(drop=True)


def build_employee_summary(df: pd.DataFrame) -> pd.DataFrame:
    df = prepare_dataframe(df)

    if df.empty:
        return pd.DataFrame(
            columns=[
                "employee",
                "line",
                "credit_hours",
                "actual_hours",
                "rework_hours",
                "labor_efficiency",
            ]
        )

    employee_df = df[df["employee"].astype(str).str.strip() != ""].copy()

    if employee_df.empty:
        return pd.DataFrame(
            columns=[
                "employee",
                "line",
                "credit_hours",
                "actual_hours",
                "rework_hours",
                "labor_efficiency",
            ]
        )

    grouped = (
        employee_df.groupby(["employee", "line"], dropna=False)
        .agg(
            credit_hours=("credit_hours", "sum"),
            actual_hours=("actual_hours", "sum"),
            rework_hours=("rework_hours", "sum"),
        )
        .reset_index()
    )

    grouped["labor_efficiency"] = 0.0
    mask = grouped["actual_hours"] > 0
    grouped.loc[mask, "labor_efficiency"] = (
        grouped.loc[mask, "credit_hours"] / grouped.loc[mask, "actual_hours"] * 100
    )

    return grouped.sort_values(["labor_efficiency", "credit_hours"], ascending=[False, False]).reset_index(drop=True)


def calculate_overview_metrics(line_summary: pd.DataFrame) -> dict:
    if line_summary is None or line_summary.empty:
        return {
            "goal_units": 0,
            "actual_units": 0,
            "credit_hours": 0.0,
            "actual_hours": 0.0,
            "labor_efficiency": 0.0,
            "lines_below_goal": 0,
        }

    total_credit = float(line_summary["credit_hours"].sum())
    total_actual = float(line_summary["actual_hours"].sum())

    labor_eff = 0.0
    if total_actual > 0:
        labor_eff = (total_credit / total_actual) * 100

    return {
        "goal_units": int(line_summary["goal_units"].sum()),
        "actual_units": int(line_summary["actual_units"].sum()),
        "credit_hours": round(total_credit, 1),
        "actual_hours": round(total_actual, 1),
        "labor_efficiency": round(labor_eff, 1),
        "lines_below_goal": int(line_summary["below_goal"].sum()),
    }