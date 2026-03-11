import re
from pathlib import Path

import pandas as pd
import pdfplumber

from utils.file_paths import PROCESSED_DIR


STANDARD_COLUMNS = [
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


HEADER_ALIASES = {
    "employee": "employee",
    "employee_name": "employee",
    "name": "employee",
    "hire_date": "hire_date",
    "date": "hire_date",
    "zone": "zone",
    "efficiency": "labor_efficiency",
    "efficiency_%": "labor_efficiency",
    "efficiency_percent": "labor_efficiency",
    "%_efficiency": "labor_efficiency",
    "credit_hrs": "credit_hours",
    "credit_hours": "credit_hours",
    "credit": "credit_hours",
    "actual_hrs": "actual_hours",
    "actual_hours": "actual_hours",
    "hrs_worked": "actual_hours",
    "worked_hours": "actual_hours",
    "rework_hrs": "rework_hours",
    "rework_hours": "rework_hours",
    "rework": "rework_hours",
    "break_meeting_clean": "breaks_hours",
    "break_meeting_clean_hours": "breaks_hours",
    "breaks_meeting_clean": "breaks_hours",
    "units_produced": "actual_units",
    "actual_units": "actual_units",
    "goal_units": "goal_units",
    "target_units": "goal_units",
}


def _clean_header(value) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("%", " percent ")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def _clean_cell(value) -> str:
    return str(value or "").replace("\n", " ").strip()


def _to_number(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("%", "").replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None


def _detect_line_name(page_text: str, page_number: int) -> str:
    text = (page_text or "").lower()

    if "co2" in text and "topping" in text:
        return "CO2 Topping"
    if "co2" in text and "prewire" in text:
        return "CO2 Prewire"
    if "co2" in text and "topper" in text:
        return "CO2 Topper"
    if "glycol" in text and "pipers" in text:
        return "Glycol Pipers"
    if "glycol" in text and "prewire" in text:
        return "Glycol Prewire"
    if "glycol" in text and "topper" in text:
        return "Glycol Topper"
    if "glycol" in text:
        return "Glycol Line"
    if "co2" in text:
        return "CO2 Line"

    return f"Page {page_number}"


def _detect_goal_units(page_text: str):
    if not page_text:
        return None

    patterns = [
        r"(\d+)\s+co2\s+units\s+per\s+wk",
        r"(\d+)\s+glycol\s+units\s+per\s+wk",
        r"goal\s+(\d+)\s+units?\s+per\s+wk",
    ]

    text = page_text.lower()
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
    return None


def _normalize_raw_df(raw_df: pd.DataFrame) -> pd.DataFrame:
    raw_df = raw_df.copy()
    raw_df.columns = [_clean_header(col) for col in raw_df.columns]
    renamed = {}
    for col in raw_df.columns:
        renamed[col] = HEADER_ALIASES.get(col, col)
    raw_df = raw_df.rename(columns=renamed)
    return raw_df


def _standardize_employee_table(raw_df: pd.DataFrame, line_name: str, goal_units, page_num: int, pdf_name: str):
    df = _normalize_raw_df(raw_df)

    required_like = {"employee"}
    if not required_like.issubset(set(df.columns)):
        return pd.DataFrame(columns=STANDARD_COLUMNS)

    out = pd.DataFrame()
    out["line"] = line_name
    out["employee"] = df.get("employee", "").astype(str).str.strip()
    out["zone"] = df.get("zone", "")
    out["hire_date"] = df.get("hire_date", "")
    out["goal_units"] = goal_units
    out["actual_units"] = None
    out["credit_hours"] = df.get("credit_hours")
    out["actual_hours"] = df.get("actual_hours")
    out["labor_efficiency"] = df.get("labor_efficiency")
    out["rework_hours"] = df.get("rework_hours")
    out["breaks_hours"] = df.get("breaks_hours")
    out["source_page"] = page_num
    out["source_pdf"] = pdf_name

    for col in STANDARD_COLUMNS:
        if col not in out.columns:
            out[col] = None

    out = out[STANDARD_COLUMNS]
    out = out[out["employee"].astype(str).str.strip() != ""].copy()
    return out


def _standardize_summary_table(raw_df: pd.DataFrame, page_num: int, pdf_name: str):
    df = _normalize_raw_df(raw_df)

    # Looking for summary-type tables like Zone / Units Produced / Actual Total Hours / Efficiency %
    if "zone" not in df.columns:
        return pd.DataFrame(columns=STANDARD_COLUMNS)

    out = pd.DataFrame()
    out["line"] = df.get("zone", "").astype(str).str.strip()
    out["employee"] = ""
    out["zone"] = df.get("zone", "")
    out["hire_date"] = ""
    out["goal_units"] = df.get("goal_units")
    out["actual_units"] = df.get("actual_units")
    out["credit_hours"] = None
    out["actual_hours"] = df.get("actual_hours")
    out["labor_efficiency"] = df.get("labor_efficiency")
    out["rework_hours"] = None
    out["breaks_hours"] = None
    out["source_page"] = page_num
    out["source_pdf"] = pdf_name

    for col in STANDARD_COLUMNS:
        if col not in out.columns:
            out[col] = None

    out = out[STANDARD_COLUMNS]
    out = out[out["line"].astype(str).str.strip() != ""].copy()
    return out


def _extract_tables_from_pdf(pdf_path: Path) -> pd.DataFrame:
    pdf_name = pdf_path.name
    all_rows = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""
            line_name = _detect_line_name(page_text, page_num)
            goal_units = _detect_goal_units(page_text)

            tables = page.extract_tables() or []

            for table in tables:
                if not table or len(table) < 2:
                    continue

                header = [_clean_cell(x) for x in table[0]]
                rows = [[_clean_cell(x) for x in row] for row in table[1:]]

                if not header or not rows:
                    continue

                raw_df = pd.DataFrame(rows, columns=header)

                employee_df = _standardize_employee_table(
                    raw_df=raw_df,
                    line_name=line_name,
                    goal_units=goal_units,
                    page_num=page_num,
                    pdf_name=pdf_name,
                )
                if not employee_df.empty:
                    all_rows.append(employee_df)

                summary_df = _standardize_summary_table(
                    raw_df=raw_df,
                    page_num=page_num,
                    pdf_name=pdf_name,
                )
                if not summary_df.empty:
                    all_rows.append(summary_df)

    if not all_rows:
        return pd.DataFrame(columns=STANDARD_COLUMNS)

    final_df = pd.concat(all_rows, ignore_index=True)

    for col in [
        "goal_units",
        "actual_units",
        "credit_hours",
        "actual_hours",
        "labor_efficiency",
        "rework_hours",
        "breaks_hours",
    ]:
        final_df[col] = final_df[col].apply(_to_number)

    return final_df[STANDARD_COLUMNS]


def parse_and_save_pdf(pdf_path, output_path=None) -> dict:
    """
    Parses a PDF and saves a normalized CSV for the dashboard.

    Returns:
        {
            "status": "success" | "error",
            "message": "...",
            "csv_path": "...",
            "rows": int
        }
    """
    try:
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            return {
                "status": "error",
                "message": f"PDF file not found: {pdf_path}",
                "csv_path": "",
                "rows": 0,
            }

        if output_path is None:
            output_path = PROCESSED_DIR / "latest.csv"
        else:
            output_path = Path(output_path)

        df = _extract_tables_from_pdf(pdf_path)

        if df.empty:
            return {
                "status": "error",
                "message": "No structured table data could be extracted from this PDF. Use the demo PDFs or another text-based PDF.",
                "csv_path": "",
                "rows": 0,
            }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)

        return {
            "status": "success",
            "message": f"Parsed {len(df)} rows successfully.",
            "csv_path": str(output_path),
            "rows": int(len(df)),
        }

    except Exception as exc:
        return {
            "status": "error",
            "message": f"Parser failed: {exc}",
            "csv_path": "",
            "rows": 0,
        }


if __name__ == "__main__":
    sample_path = PROCESSED_DIR / "debug_sample.csv"
    print(
        {
            "status": "info",
            "message": "Run this parser through app.py with an uploaded PDF.",
            "csv_path": str(sample_path),
            "rows": 0,
        }
    )