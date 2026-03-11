from pathlib import Path
import pandas as pd
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


def empty_dataframe() -> pd.DataFrame:
    return pd.DataFrame(columns=STANDARD_COLUMNS)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [
        str(c)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("-", "_")
        for c in df.columns
    ]
    return df


def load_latest_data() -> pd.DataFrame:
    possible_files = [
        PROCESSED_DIR / "latest.csv",
        PROCESSED_DIR / "parsed_output.csv",
        PROCESSED_DIR / "output.csv",
    ]

    for file_path in possible_files:
        if file_path.exists():
            try:
                df = pd.read_csv(file_path)
                df = normalize_columns(df)
                for col in STANDARD_COLUMNS:
                    if col not in df.columns:
                        df[col] = None
                return df[STANDARD_COLUMNS]
            except Exception:
                pass

    return empty_dataframe()