"""
ESCDP data cleaning pipeline — saves ALL processed datasets as CSV.

Input:
    ESCDP/data/raw/  (CSV, JSON, XML, XLS, XLSX, SQLite/DB)
Output:
    ESCDP/data/processed/*.csv
Reports:
    ESCDP/reports/data_quality/

Features:
- Recursively loads supported source formats.
- Converts each source dataset/table to a CSV output.
- Drops columns that are 100% missing.
- Normalizes common missing-value markers.
- Fills remaining missing values:
    * numeric columns -> median
    * text/category columns -> mode, or "Unknown" if no mode
    * date-like columns and identifiers -> left missing to avoid inventing dates/IDs
- Trims strings and removes exact duplicate rows.
- Leaves files in data/raw unchanged.
- Writes reports for summary, issues, imputation, and errors.

Install dependencies:
    python -m pip install pandas openpyxl xlrd sqlalchemy

Note:
- For SQLite, each table is exported to a separate CSV.
- Output filenames include the source filename and table/sheet name to avoid collisions.
- This is generic cleaning; review imputation_report.csv before using the data for analysis.
"""

from __future__ import annotations

import json
import re
import sqlite3
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORT_DIR = BASE_DIR / "reports" / "data_quality"

NULL_MARKERS = {"", "null", "none", "nan", "n/a", "na", "nil", "undefined"}
SUPPORTED_EXTENSIONS = {".csv", ".json", ".xml", ".xls", ".xlsx", ".sqlite", ".db"}

summary_rows: list[dict[str, Any]] = []
issue_rows: list[dict[str, Any]] = []
imputation_rows: list[dict[str, Any]] = []
error_rows: list[dict[str, Any]] = []


def is_date_column(name: Any) -> bool:
    n = str(name).lower().replace("_", " ")
    return any(x in n for x in ("date", "datetime", "timestamp", "created at", "updated at"))


def is_identifier_column(name: Any) -> bool:
    n = str(name).lower().replace("_", " ").strip()
    return (
        n in {"id", "order id", "product id", "supplier id", "vendor id",
              "warehouse id", "shipment id", "customer id", "record id",
              "po / so #", "asn/dn #", "tracking number"}
        or n.endswith(" id") or n.endswith(" key") or n.endswith(" #")
    )


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    for col in df.columns:
        if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
            df[col] = df[col].map(
                lambda v: pd.NA if isinstance(v, str) and v.strip().lower() in NULL_MARKERS
                else v.strip() if isinstance(v, str) else v
            )
    return df


def clean_dataframe(df: pd.DataFrame, dataset: str, location: str):
    df = normalize_dataframe(df)
    original_rows = len(df)
    dropped_columns = []

    # Remove columns that have no valid values.
    for col in list(df.columns):
        if len(df) > 0 and df[col].isna().all():
            dropped_columns.append(str(col))
            df = df.drop(columns=[col])
            issue_rows.append({
                "dataset": dataset, "location": location,
                "issue": "Dropped 100% missing column",
                "details": f"Column {col!r} had no non-missing values"
            })

    # Fill missing values according to the column's role/type.
    for col in df.columns:
        missing = int(df[col].isna().sum())
        if missing == 0:
            continue

        if is_date_column(col) or is_identifier_column(col):
            issue_rows.append({
                "dataset": dataset, "location": location,
                "issue": "Missing values retained",
                "details": f"{col!r}: {missing} missing value(s); dates and IDs are not safely imputed"
            })
            continue

        # Convert object columns to numeric if >=95% of non-missing values are numeric.
        series = df[col]
        if not pd.api.types.is_numeric_dtype(series):
            non_null = series.dropna()
            if len(non_null):
                parsed = pd.to_numeric(non_null, errors="coerce")
                if parsed.notna().mean() >= 0.95:
                    converted = pd.to_numeric(series, errors="coerce")
                    # Avoid conversion if it would create additional missing values.
                    if int(converted.isna().sum()) <= missing:
                        df[col] = converted
                        series = df[col]

        if pd.api.types.is_numeric_dtype(series):
            fill_value = series.median()
            if pd.isna(fill_value):
                issue_rows.append({
                    "dataset": dataset, "location": location,
                    "issue": "Missing values retained",
                    "details": f"{col!r}: no numeric median available"
                })
                continue
            df[col] = series.fillna(fill_value)
            method = "median"
        else:
            mode_values = series.mode(dropna=True)
            if not mode_values.empty:
                fill_value = mode_values.iloc[0]
                df[col] = series.fillna(fill_value)
                method = "mode"
            else:
                fill_value = "Unknown"
                df[col] = series.fillna(fill_value)
                method = "Unknown fallback"

        imputation_rows.append({
            "dataset": dataset, "location": location, "column": str(col),
            "missing_filled": missing, "method": method, "fill_value": str(fill_value)
        })

    # Remove exact duplicate rows only.
    before_dedup = len(df)
    df = df.drop_duplicates(keep="first")
    duplicates_removed = before_dedup - len(df)
    if duplicates_removed:
        issue_rows.append({
            "dataset": dataset, "location": location,
            "issue": "Exact duplicate rows removed",
            "details": f"{duplicates_removed} duplicate row(s) removed"
        })

    return df, {
        "rows_before": original_rows,
        "rows_after": len(df),
        "records_removed": duplicates_removed,
        "columns_dropped_100pct_missing": len(dropped_columns),
        "dropped_columns": "; ".join(dropped_columns)
    }


def records_to_dataframe(obj: Any) -> pd.DataFrame:
    """Convert common JSON/XML structures into a tabular DataFrame."""
    if isinstance(obj, list):
        if not obj:
            return pd.DataFrame()
        if all(isinstance(x, dict) for x in obj):
            return pd.json_normalize(obj, sep="_")
        return pd.DataFrame({"value": obj})
    if isinstance(obj, dict):
        # Prefer common record-list keys, but preserve other nested dictionaries via normalization.
        for key in ("data", "records", "items", "results", "orders", "shipments", "vendors", "products"):
            if isinstance(obj.get(key), list):
                value = obj[key]
                if value and all(isinstance(x, dict) for x in value):
                    return pd.json_normalize(value, sep="_")
                return pd.DataFrame({"value": value})
        return pd.json_normalize(obj, sep="_")
    return pd.DataFrame({"value": [obj]})


def xml_to_dataframe(src: Path) -> pd.DataFrame:
    root = ET.parse(src).getroot()
    # Each direct child is treated as a record; nested children become flattened columns.
    records = []
    children = list(root)
    if not children:
        return pd.DataFrame([{"tag": root.tag, "text": root.text}])

    for child in children:
        record = {}
        # Include attributes and child text.
        for k, v in child.attrib.items():
            record[f"@{k}"] = v
        for sub in list(child):
            key = sub.tag
            if list(sub):
                record[key] = json.dumps(
                    {inner.tag: inner.text for inner in list(sub)},
                    ensure_ascii=False
                )
            else:
                record[key] = sub.text
        if not record:
            record = {"value": child.text}
        records.append(record)
    return pd.DataFrame(records)


def load_source(src: Path) -> list[tuple[str, pd.DataFrame]]:
    ext = src.suffix.lower()
    if ext == ".csv":
        return [(src.stem, pd.read_csv(src, dtype=object, keep_default_na=True))]
    if ext == ".json":
        with src.open("r", encoding="utf-8-sig") as f:
            obj = json.load(f)
        return [(src.stem, records_to_dataframe(obj))]
    if ext == ".xml":
        return [(src.stem, xml_to_dataframe(src))]
    if ext in {".xls", ".xlsx"}:
        engine = "xlrd" if ext == ".xls" else "openpyxl"
        sheets = pd.read_excel(src, sheet_name=None, dtype=object, keep_default_na=True, engine=engine)
        return [(f"{src.stem}_{sheet}", df) for sheet, df in sheets.items()]
    if ext in {".sqlite", ".db"}:
        outputs = []
        conn = sqlite3.connect(src)
        try:
            tables = pd.read_sql_query(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
                conn
            )["name"].tolist()
            for table in tables:
                safe_table = '"' + table.replace('"', '""') + '"'
                df = pd.read_sql_query(f"SELECT * FROM {safe_table}", conn)
                outputs.append((f"{src.stem}_{table}", df))
        finally:
            conn.close()
        return outputs
    return []


def safe_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._") or "dataset"


def main() -> None:
    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"Raw data folder not found: {RAW_DIR}\n"
            "Place this script at ESCDP/etl/python/data_cleaning.py and create ESCDP/data/raw."
        )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    for src in sorted(RAW_DIR.rglob("*")):
        if not src.is_file() or src.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        try:
            tables_or_frames = load_source(src)
            for output_name, df in tables_or_frames:
                cleaned, stats = clean_dataframe(df, src.name, output_name)
                relative_parent = src.parent.relative_to(RAW_DIR)
                out_dir = PROCESSED_DIR / relative_parent
                out_dir.mkdir(parents=True, exist_ok=True)
                out_file = out_dir / f"{safe_filename(output_name)}.csv"
                cleaned.to_csv(out_file, index=False, encoding="utf-8-sig")
                summary_rows.append({
                    "source_file": str(src.relative_to(RAW_DIR)),
                    "source_format": src.suffix.lower(),
                    "output_file": str(out_file.relative_to(BASE_DIR)),
                    "status": "SUCCESS",
                    **stats
                })
                print(f"[OK] {src.name} -> {out_file.relative_to(BASE_DIR)}")
        except Exception as exc:
            error_rows.append({
                "source_file": str(src.relative_to(RAW_DIR)),
                "error": str(exc),
                "traceback": traceback.format_exc()
            })
            summary_rows.append({
                "source_file": str(src.relative_to(RAW_DIR)),
                "source_format": src.suffix.lower(),
                "status": "FAILED",
                "error": str(exc)
            })
            print(f"[ERROR] {src.name}: {exc}")

    pd.DataFrame(summary_rows).to_csv(REPORT_DIR / "cleaning_summary.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(issue_rows, columns=["dataset", "location", "issue", "details"]).to_csv(
        REPORT_DIR / "cleaning_issues.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(imputation_rows, columns=[
        "dataset", "location", "column", "missing_filled", "method", "fill_value"
    ]).to_csv(REPORT_DIR / "imputation_report.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(error_rows, columns=["source_file", "error", "traceback"]).to_csv(
        REPORT_DIR / "cleaning_errors.csv", index=False, encoding="utf-8-sig")

    print("\nFinished.")
    print(f"Processed CSV files: {PROCESSED_DIR}")
    print(f"Reports: {REPORT_DIR}")
    print("Review cleaning_summary.csv, imputation_report.csv, and cleaning_errors.csv.")


if __name__ == "__main__":
    main()
