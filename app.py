import io
from datetime import timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Manufacturing_Ops_V4",
    layout="wide"
)

st.markdown(
    """
    <style>
        .stApp {
            background-color: #111827;
            color: #f9fafb;
        }
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }
        h1, h2, h3, h4, h5, h6, p, div, span, label {
            color: #f9fafb !important;
        }
        .metric-card {
            background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            padding: 18px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.20);
        }
        .section-card {
            background: #1f2937;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            padding: 18px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.18);
            margin-bottom: 1rem;
        }
        .good-text {
            color: #22c55e !important;
            font-weight: 700;
        }
        .bad-text {
            color: #ef4444 !important;
            font-weight: 700;
        }
        .neutral-text {
            color: #e5e7eb !important;
            font-weight: 700;
        }
        .small-note {
            color: #cbd5e1 !important;
            font-size: 0.9rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)

COLUMN_ALIASES = {
    "date": [
        "date", "day", "report_date", "production_date", "work_date", "service_date"
    ],
    "output_units": [
        "output_units", "units", "units_produced", "produced_units",
        "production_output", "daily_output", "parts_produced", "pieces_produced"
    ],
    "downtime_minutes": [
        "downtime_minutes", "downtime_mins", "downtime", "minutes_down",
        "downtime_minutes_total", "machine_downtime_minutes", "down_minutes"
    ],
    "scrap_rate": [
        "scrap_rate", "scrap_percent", "scrap_pct", "reject_rate", "defect_rate"
    ],
    "labor_hours": [
        "labor_hours", "hours_worked", "worked_hours", "man_hours",
        "laborhrs", "total_labor_hours", "tech_hours", "technician_hours"
    ],
    "orders_completed": [
        "orders_completed", "jobs_completed", "completed_jobs", "orders_done",
        "work_orders_closed", "service_calls_completed", "tickets_closed",
        "calls_completed"
    ],
    "revenue": [
        "revenue", "sales", "daily_revenue", "income", "gross_sales"
    ],
    "notes": [
        "notes", "comments", "remarks", "issues", "observations"
    ],
}

REQUIRED_MINIMUM = ["date"]
DEFAULT_NUMERIC_COLUMNS = [
    "output_units",
    "downtime_minutes",
    "scrap_rate",
    "labor_hours",
    "orders_completed",
    "revenue",
]


def normalize_column_name(col: str) -> str:
    return (
        str(col)
        .strip()
        .lower()
        .replace("%", "percent")
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
    )


def build_reverse_alias_map() -> dict:
    reverse_map = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            reverse_map[normalize_column_name(alias)] = canonical
    return reverse_map


def auto_map_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, dict, list]:
    reverse_map = build_reverse_alias_map()
    original_columns = list(df.columns)
    renamed = {}
    unmatched = []

    for col in original_columns:
        normalized = normalize_column_name(col)
        if normalized in reverse_map:
            renamed[col] = reverse_map[normalized]
        else:
            unmatched.append(col)

    mapped_df = df.rename(columns=renamed).copy()
    return mapped_df, renamed, unmatched


def validate_and_clean_data(df: pd.DataFrame) -> tuple[pd.DataFrame, list]:
    errors = []

    for col in REQUIRED_MINIMUM:
        if col not in df.columns:
            errors.append(
                "I couldn't find a Date column. Use one of these names: "
                "Date, Day, Report Date, Production Date, Service Date."
            )

    if errors:
        return df, errors

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    if df["date"].isna().all():
        errors.append("The Date column exists, but none of the values could be read as real dates.")

    for col in DEFAULT_NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("$", "", regex=False)
                .str.replace("%", "", regex=False)
                .str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "scrap_rate" in df.columns:
        if df["scrap_rate"].dropna().gt(1).mean() > 0.5:
            df["scrap_rate"] = df["scrap_rate"] / 100.0

    df = df.sort_values("date").reset_index(drop=True)

    if df["date"].isna().any():
        bad_count = int(df["date"].isna().sum())
        errors.append(f"{bad_count} row(s) had invalid dates and may not chart correctly.")

    return df, errors


def load_file(uploaded_file) -> pd.DataFrame:
    file_name = uploaded_file.name.lower()
    if file_name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    if file_name.endswith(".xlsx"):
        return pd.read_excel(uploaded_file)
    raise ValueError("Unsupported file type. Please upload a CSV or XLSX file.")


def create_manufacturing_template() -> pd.DataFrame:
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=30, freq="D")

    np.random.seed(42)
    output_units = np.random.normal(520, 45, len(dates)).round().astype(int)
    downtime_minutes = np.random.normal(52, 16, len(dates)).clip(5, None).round(1)
    scrap_rate = np.random.normal(0.035, 0.008, len(dates)).clip(0.01, 0.08)
    labor_hours = np.random.normal(78, 7, len(dates)).clip(50, None).round(1)
    orders_completed = np.random.normal(24, 4, len(dates)).clip(10, None).round().astype(int)
    revenue = np.random.normal(12450, 1200, len(dates)).clip(8000, None).round(2)

    output_units[10] = 410
    downtime_minutes[10] = 110
    scrap_rate[10] = 0.067
    revenue[10] = 9800

    output_units[21] = 430
    downtime_minutes[21] = 95
    scrap_rate[21] = 0.061
    revenue[21] = 10150

    notes = []
    for i in range(len(dates)):
        if i == 10:
            notes.append("Unplanned downtime due to line jam")
        elif i == 21:
            notes.append("Material delay and higher defect count")
        else:
            notes.append("Normal operating day")

    return pd.DataFrame({
        "Date": dates,
        "Output Units": output_units,
        "Downtime Minutes": downtime_minutes,
        "Scrap Rate": scrap_rate,
        "Labor Hours": labor_hours,
        "Orders Completed": orders_completed,
        "Revenue": revenue,
        "Notes": notes
    })


def create_service_template() -> pd.DataFrame:
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=30, freq="D")

    np.random.seed(99)
    jobs_completed = np.random.normal(18, 3, len(dates)).clip(8, None).round().astype(int)
    labor_hours = np.random.normal(42, 6, len(dates)).clip(20, None).round(1)
    downtime_minutes = np.random.normal(18, 8, len(dates)).clip(0, None).round(1)
    revenue = np.random.normal(4850, 650, len(dates)).clip(2500, None).round(2)
    output_units = np.random.normal(21, 3, len(dates)).clip(10, None).round().astype(int)
    scrap_rate = np.random.normal(0.018, 0.007, len(dates)).clip(0.0, 0.06)

    jobs_completed[8] = 11
    labor_hours[8] = 49.5
    downtime_minutes[8] = 42
    revenue[8] = 3350

    jobs_completed[19] = 12
    labor_hours[19] = 50.0
    downtime_minutes[19] = 37
    revenue[19] = 3425

    notes = []
    for i in range(len(dates)):
        if i == 8:
            notes.append("Tech absence and longer appointment times")
        elif i == 19:
            notes.append("Parts delay and customer reschedules")
        else:
            notes.append("Normal service day")

    return pd.DataFrame({
        "Service Date": dates,
        "Jobs Completed": jobs_completed,
        "Technician Hours": labor_hours,
        "Downtime Minutes": downtime_minutes,
        "Revenue": revenue,
        "Service Calls Completed": output_units,
        "Scrap Rate": scrap_rate,
        "Notes": notes
    })


def df_to_excel_bytes(df: pd.DataFrame, sheet_name: str) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    output.seek(0)
    return output.getvalue()


def format_delta(current, previous, higher_is_better=True, as_percent=False):
    if pd.isna(current) or pd.isna(previous):
        return "No comparison"
    diff = current - previous
    if as_percent:
        diff_display = f"{diff:+.2%}"
    else:
        diff_display = f"{diff:+,.2f}"

    good = diff >= 0 if higher_is_better else diff <= 0
    css_class = "good-text" if good else "bad-text"
    return f"<span class='{css_class}'>{diff_display}</span>"


def latest_vs_previous(df: pd.DataFrame, col: str):
    if col not in df.columns:
        return np.nan, np.nan
    series = df[col].dropna()
    if len(series) == 0:
        return np.nan, np.nan
    current = series.iloc[-1]
    previous = series.iloc[-2] if len(series) > 1 else np.nan
    return current, previous


def detect_anomalies(df: pd.DataFrame, metric_cols: list[str]) -> pd.DataFrame:
    rows = []
    for col in metric_cols:
        if col not in df.columns:
            continue
        series = df[col].dropna()
        if len(series) < 8:
            continue

        mean_val = series.mean()
        std_val = series.std(ddof=0)

        if std_val == 0 or pd.isna(std_val):
            continue

        z_scores = (df[col] - mean_val) / std_val
        anomaly_idx = df.index[z_scores.abs() >= 2].tolist()

        for idx in anomaly_idx:
            rows.append({
                "date": df.loc[idx, "date"],
                "metric": col,
                "value": df.loc[idx, col],
                "z_score": float(z_scores.loc[idx]),
                "severity": "High" if abs(z_scores.loc[idx]) >= 3 else "Medium"
            })

    if not rows:
        return pd.DataFrame(columns=["date", "metric", "value", "z_score", "severity"])

    out = pd.DataFrame(rows).sort_values(["date", "severity"], ascending=[False, True])
    return out.reset_index(drop=True)


def generate_root_cause_hints(df: pd.DataFrame) -> list[str]:
    hints = []

    if {"output_units", "downtime_minutes"}.issubset(df.columns):
        corr = df[["output_units", "downtime_minutes"]].corr().iloc[0, 1]
        if pd.notna(corr) and corr < -0.35:
            hints.append(
                "Output appears to drop when downtime increases. This suggests downtime is a likely driver of weaker performance days."
            )

    if {"scrap_rate", "output_units"}.issubset(df.columns):
        corr = df[["scrap_rate", "output_units"]].corr().iloc[0, 1]
        if pd.notna(corr) and corr < -0.25:
            hints.append(
                "Higher scrap rate seems linked with lower output. Quality issues may be reducing performance."
            )

    if {"labor_hours", "output_units"}.issubset(df.columns):
        corr = df[["labor_hours", "output_units"]].corr().iloc[0, 1]
        if pd.notna(corr) and corr > 0.30:
            hints.append(
                "Higher labor hours generally align with higher output. Staffing capacity may be affecting throughput."
            )

    if {"orders_completed", "revenue"}.issubset(df.columns):
        corr = df[["orders_completed", "revenue"]].corr().iloc[0, 1]
        if pd.notna(corr) and corr > 0.40:
            hints.append(
                "Revenue appears to move with completed work. Throughput improvements may have a direct financial effect."
            )

    if not hints:
        hints.append(
            "No strong statistical driver stood out yet. More historical rows will improve the quality of the root-cause hints."
        )

    return hints


def simple_forecast(df: pd.DataFrame, col: str, periods: int = 7) -> pd.DataFrame:
    if col not in df.columns:
        return pd.DataFrame()

    working = df[["date", col]].dropna().copy()
    if len(working) < 7:
        return pd.DataFrame()

    working["date"] = pd.to_datetime(working["date"])
    working = working.sort_values("date").reset_index(drop=True)
    working["t"] = np.arange(len(working))

    slope, intercept = np.polyfit(working["t"], working[col], 1)

    future_dates = [working["date"].iloc[-1] + timedelta(days=i) for i in range(1, periods + 1)]
    future_t = np.arange(len(working), len(working) + periods)
    preds = intercept + slope * future_t

    forecast_df = pd.DataFrame({
        "date": future_dates,
        col: preds,
        "type": "Forecast"
    })

    hist_df = working[["date", col]].copy()
    hist_df["type"] = "Historical"

    return pd.concat([hist_df, forecast_df], ignore_index=True)


def executive_summary(df: pd.DataFrame, anomalies_df: pd.DataFrame) -> list[str]:
    bullets = []

    if "output_units" in df.columns and df["output_units"].notna().any():
        recent_avg = df["output_units"].tail(7).mean()
        prior_avg = df["output_units"].iloc[-14:-7].mean() if len(df) >= 14 else np.nan
        if pd.notna(prior_avg):
            if recent_avg > prior_avg:
                bullets.append(
                    f"Average output improved over the most recent 7-day period, rising from {prior_avg:,.0f} to {recent_avg:,.0f}."
                )
            else:
                bullets.append(
                    f"Average output softened over the most recent 7-day period, moving from {prior_avg:,.0f} to {recent_avg:,.0f}."
                )

    if "orders_completed" in df.columns and df["orders_completed"].notna().any():
        recent_orders = df["orders_completed"].tail(7).mean()
        bullets.append(f"Average completed work over the latest 7 days is {recent_orders:,.1f}.")

    if "downtime_minutes" in df.columns and df["downtime_minutes"].notna().any():
        recent_down = df["downtime_minutes"].tail(7).mean()
        bullets.append(f"Average downtime over the latest 7 days is {recent_down:,.1f} minutes.")

    if "scrap_rate" in df.columns and df["scrap_rate"].notna().any():
        recent_scrap = df["scrap_rate"].tail(7).mean()
        bullets.append(f"Average scrap/error rate over the latest 7 days is {recent_scrap:.2%}.")

    if len(anomalies_df) > 0:
        latest_anomaly = anomalies_df.iloc[0]
        bullets.append(
            f"An unusual change was detected on {latest_anomaly['date'].date()} in {latest_anomaly['metric']} with {latest_anomaly['severity'].lower()} severity."
        )
    else:
        bullets.append("No major anomalies were detected in the current dataset.")

    if not bullets:
        bullets.append("Upload more historical data to generate a stronger executive summary.")

    return bullets


def show_metric_card(title: str, value_text: str, delta_html: str):
    st.markdown(
        f"""
        <div class="metric-card">
            <div style="font-size:0.95rem; color:#cbd5e1;">{title}</div>
            <div style="font-size:2rem; font-weight:800; margin-top:4px;">{value_text}</div>
            <div style="margin-top:8px;">{delta_html}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def human_label(col_name: str) -> str:
    return col_name.replace("_", " ").title()


def prepare_demo_df(template_type: str) -> pd.DataFrame:
    if template_type == "Service Business":
        demo_df = create_service_template()
    else:
        demo_df = create_manufacturing_template()

    mapped_df, _, _ = auto_map_columns(demo_df)
    cleaned_df, _ = validate_and_clean_data(mapped_df)
    return cleaned_df


st.title("Manufacturing_Ops_V4")
st.caption("Upload a CSV or Excel file and the dashboard will auto-map common column names, detect anomalies, and generate a professional operating view.")

with st.sidebar:
    st.markdown("## Upload Data")
    uploaded_file = st.file_uploader("Choose a CSV or XLSX file", type=["csv", "xlsx"])

    st.markdown("## Starter Templates")
    st.download_button(
        label="Download Manufacturing Template",
        data=df_to_excel_bytes(create_manufacturing_template(), "Manufacturing_Template"),
        file_name="manufacturing_dashboard_starter_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.download_button(
        label="Download Service Business Template",
        data=df_to_excel_bytes(create_service_template(), "Service_Business_Template"),
        file_name="service_business_dashboard_starter_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.markdown("## Demo Mode")
    demo_mode = st.radio(
        "When no file is uploaded, preview:",
        ["Manufacturing", "Service Business"],
        index=0
    )

    st.markdown(
        """
        <div class="small-note">
        Recommended columns:
        Date / Service Date, Output Units or Service Calls Completed, Downtime Minutes,
        Scrap Rate, Labor Hours / Technician Hours, Orders Completed / Jobs Completed, Revenue, Notes
        </div>
        """,
        unsafe_allow_html=True
    )

if uploaded_file is None:
    st.markdown(
        """
        <div class="section-card">
            <h3>Getting Started</h3>
            <p>Upload your own CSV/XLSX file or download one of the starter templates from the sidebar.</p>
            <p>This version is built to reduce upload friction for both manufacturing and service businesses by auto-mapping common spreadsheet column names.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    data_df = prepare_demo_df(demo_mode)
else:
    try:
        raw_df = load_file(uploaded_file)
        mapped_df, renamed_cols, unmatched_cols = auto_map_columns(raw_df)
        data_df, validation_messages = validate_and_clean_data(mapped_df)

        if renamed_cols:
            with st.expander("Mapped Columns"):
                map_view = pd.DataFrame({
                    "Original Column": list(renamed_cols.keys()),
                    "Mapped To": list(renamed_cols.values())
                })
                st.dataframe(map_view, use_container_width=True)

        if unmatched_cols:
            with st.expander("Unmatched Columns"):
                st.write("These columns were left untouched because they were not recognized:")
                st.write(unmatched_cols)

        for msg in validation_messages:
            if "invalid dates" in msg.lower():
                st.warning(msg)
            else:
                st.error(msg)

        if any("couldn't find a Date column" in msg for msg in validation_messages):
            st.stop()

    except Exception as e:
        st.error(f"File could not be loaded: {e}")
        st.stop()

if "date" not in data_df.columns:
    st.error("A valid Date column is required to continue.")
    st.stop()

data_df = data_df.dropna(subset=["date"]).copy()
data_df = data_df.sort_values("date").reset_index(drop=True)

with st.container():
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Executive Summary")

    anomalies = detect_anomalies(
        data_df,
        metric_cols=[c for c in DEFAULT_NUMERIC_COLUMNS if c in data_df.columns]
    )
    summary_lines = executive_summary(data_df, anomalies)

    for line in summary_lines:
        st.markdown(f"- {line}")

    st.markdown("</div>", unsafe_allow_html=True)

kpi_cols = st.columns(4)

if "output_units" in data_df.columns:
    current, previous = latest_vs_previous(data_df, "output_units")
    with kpi_cols[0]:
        show_metric_card(
            "Latest Output / Volume",
            f"{current:,.0f}" if pd.notna(current) else "N/A",
            format_delta(current, previous, higher_is_better=True)
        )

if "downtime_minutes" in data_df.columns:
    current, previous = latest_vs_previous(data_df, "downtime_minutes")
    with kpi_cols[1]:
        show_metric_card(
            "Latest Downtime Minutes",
            f"{current:,.1f}" if pd.notna(current) else "N/A",
            format_delta(current, previous, higher_is_better=False)
        )

if "scrap_rate" in data_df.columns:
    current, previous = latest_vs_previous(data_df, "scrap_rate")
    with kpi_cols[2]:
        show_metric_card(
            "Latest Scrap / Error Rate",
            f"{current:.2%}" if pd.notna(current) else "N/A",
            format_delta(current, previous, higher_is_better=False, as_percent=True)
        )

if "revenue" in data_df.columns:
    current, previous = latest_vs_previous(data_df, "revenue")
    with kpi_cols[3]:
        show_metric_card(
            "Latest Revenue",
            f"${current:,.2f}" if pd.notna(current) else "N/A",
            format_delta(current, previous, higher_is_better=True)
        )

chart_row_1 = st.columns(2)
chart_row_2 = st.columns(2)

if "output_units" in data_df.columns:
    with chart_row_1[0]:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Output / Volume Trend")
        fig = px.line(
            data_df,
            x="date",
            y="output_units",
            markers=True,
            template="plotly_dark"
        )
        fig.update_layout(
            paper_bgcolor="#1f2937",
            plot_bgcolor="#1f2937",
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

if "downtime_minutes" in data_df.columns:
    with chart_row_1[1]:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Downtime Trend")
        fig = px.bar(
            data_df,
            x="date",
            y="downtime_minutes",
            template="plotly_dark"
        )
        fig.update_layout(
            paper_bgcolor="#1f2937",
            plot_bgcolor="#1f2937",
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

if "scrap_rate" in data_df.columns:
    with chart_row_2[0]:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Scrap / Error Rate Trend")
        fig = px.line(
            data_df,
            x="date",
            y="scrap_rate",
            markers=True,
            template="plotly_dark"
        )
        fig.update_layout(
            yaxis_tickformat=".1%",
            paper_bgcolor="#1f2937",
            plot_bgcolor="#1f2937",
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

if "revenue" in data_df.columns:
    with chart_row_2[1]:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Revenue Trend")
        fig = px.area(
            data_df,
            x="date",
            y="revenue",
            template="plotly_dark"
        )
        fig.update_layout(
            paper_bgcolor="#1f2937",
            plot_bgcolor="#1f2937",
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

lower_row = st.columns(2)

with lower_row[0]:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Anomaly Detection")
    if len(anomalies) == 0:
        st.success("No significant anomalies detected in the uploaded dataset.")
    else:
        display_anomalies = anomalies.copy()
        display_anomalies["date"] = pd.to_datetime(display_anomalies["date"]).dt.date
        display_anomalies["metric"] = display_anomalies["metric"].apply(human_label)
        st.dataframe(display_anomalies, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with lower_row[1]:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Root Cause Hints")
    hints = generate_root_cause_hints(data_df)
    for hint in hints:
        st.markdown(f"- {hint}")
    st.markdown("</div>", unsafe_allow_html=True)

available_forecast_metrics = [c for c in DEFAULT_NUMERIC_COLUMNS if c in data_df.columns]

if len(available_forecast_metrics) > 0:
    forecast_section_cols = st.columns([1, 2])

    with forecast_section_cols[0]:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Forecast Controls")
        forecast_metric = st.selectbox(
            "Choose a metric to forecast",
            options=available_forecast_metrics,
            format_func=human_label
        )
        forecast_days = st.slider("Forecast horizon (days)", 3, 14, 7)
        st.markdown("</div>", unsafe_allow_html=True)

    with forecast_section_cols[1]:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader(f"{human_label(forecast_metric)} Forecast")
        forecast_df = simple_forecast(data_df, forecast_metric, periods=forecast_days)

        if forecast_df.empty:
            st.info("At least 7 rows of clean historical data are needed to generate a forecast.")
        else:
            fig = px.line(
                forecast_df,
                x="date",
                y=forecast_metric,
                color="type",
                markers=True,
                template="plotly_dark"
            )
            fig.update_layout(
                paper_bgcolor="#1f2937",
                plot_bgcolor="#1f2937",
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

with st.expander("Preview Cleaned Data"):
    st.dataframe(data_df, use_container_width=True)

with st.expander("Business Use Tip"):
    st.write(
        "This version is designed to be easier to sell as a service because both manufacturing and service businesses can use a starter spreadsheet template, upload it, and immediately see charts, anomalies, and a summary without manual column cleanup."
    )