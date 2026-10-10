
from pathlib import Path
import json
import re
import sqlite3
import pandas as pd


# ==================================================
# 1. PROJECT PATHS
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
REPORT_DIR = PROJECT_ROOT / "reports" / "data_quality"

REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ==================================================
# 2. DATASET LOADERS
# ==================================================

def load_csv(file_path):
    return pd.read_csv(file_path)


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8-sig") as file:
        data = json.load(file)

    if isinstance(data, list):
        if all(isinstance(item, dict) for item in data):
            return pd.json_normalize(data)
        return pd.DataFrame({"value": data})

    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list) and all(
                isinstance(item, dict) for item in value
            ):
                return pd.json_normalize(value)

        return pd.json_normalize(data)

    raise ValueError("Unsupported JSON structure")


def load_xml(file_path):
    try:
        return pd.read_xml(file_path, parser="lxml")
    except Exception:
        return pd.read_xml(file_path, parser="etree")


def load_excel(file_path):
    if file_path.suffix.lower() == ".xls":
        return pd.read_excel(file_path, engine="xlrd")

    return pd.read_excel(file_path, engine="openpyxl")


def load_sqlite(file_path):
    tables = {}

    with sqlite3.connect(str(file_path)) as connection:
        table_names = pd.read_sql_query(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """,
            connection
        )["name"].tolist()

        for table_name in table_names:
            safe_name = table_name.replace('"', '""')

            tables[table_name] = pd.read_sql_query(
                f'SELECT * FROM "{safe_name}"',
                connection
            )

    if not tables:
        raise ValueError("No user tables found in SQLite database")

    return tables


def load_dataset(file_path):
    extension = file_path.suffix.lower()

    if extension == ".csv":
        return load_csv(file_path)

    if extension == ".json":
        return load_json(file_path)

    if extension == ".xml":
        return load_xml(file_path)

    if extension in {".xls", ".xlsx"}:
        return load_excel(file_path)

    if extension in {".sqlite", ".sqlite3", ".db"}:
        return load_sqlite(file_path)

    raise ValueError(f"Unsupported file format: {extension}")


# ==================================================
# 3. QUALITY ISSUE RECORDER
# ==================================================

def add_issue(
    issues,
    dataset,
    issue_type,
    column,
    affected_rows,
    severity,
    details
):
    if affected_rows <= 0:
        return

    issues.append({
        "Dataset": dataset,
        "Issue Type": issue_type,
        "Column": column,
        "Affected Rows": int(affected_rows),
        "Severity": severity,
        "Details": details
    })


# ==================================================
# 4. DATA QUALITY CHECKS
# ==================================================

def check_data_quality(dataset_name, df):
    issues = []
    row_count = len(df)

    if row_count == 0:
        add_issue(
            issues, dataset_name, "Empty Dataset", "",
            1, "High", "Dataset contains no records"
        )
        return issues

    # --------------------------------------------------
    # A. Missing values
    # --------------------------------------------------

    for column in df.columns:
        missing_count = int(df[column].isna().sum())

        if missing_count > 0:
            percentage = missing_count / row_count * 100

            severity = (
                "High" if percentage >= 20
                else "Medium" if percentage >= 5
                else "Low"
            )

            add_issue(
                issues,
                dataset_name,
                "Missing Values",
                str(column),
                missing_count,
                severity,
                f"{percentage:.2f}% of records have missing values"
            )

    # --------------------------------------------------
    # B. Blank text values
    # --------------------------------------------------

    for column in df.columns:
        series = df[column]

        if (
            pd.api.types.is_object_dtype(series)
            or pd.api.types.is_string_dtype(series)
        ):
            blank_count = int(
                series.astype("string").str.strip().eq("").sum()
            )

            add_issue(
                issues,
                dataset_name,
                "Blank Values",
                str(column),
                blank_count,
                "Low",
                "Records contain empty or whitespace-only strings"
            )

    # --------------------------------------------------
    # C. Leading/trailing whitespace
    # --------------------------------------------------

    for column in df.columns:
        series = df[column]

        if (
            pd.api.types.is_object_dtype(series)
            or pd.api.types.is_string_dtype(series)
        ):
            text_values = series.dropna().astype(str)

            whitespace_count = int(
                text_values.ne(text_values.str.strip()).sum()
            )

            add_issue(
                issues,
                dataset_name,
                "Leading/Trailing Whitespace",
                str(column),
                whitespace_count,
                "Low",
                "Text values contain leading or trailing spaces"
            )

    # --------------------------------------------------
    # D. Duplicate records
    # --------------------------------------------------

    duplicate_count = int(df.duplicated().sum())

    add_issue(
        issues,
        dataset_name,
        "Duplicate Rows",
        "",
        duplicate_count,
        "Medium",
        "Exact duplicate records after the first occurrence"
    )

    # --------------------------------------------------
    # E. Repeated standalone ID columns
    # --------------------------------------------------

    id_names = {
        "id",
        "record id",
        "record_id",
        "vendor id",
        "vendor_id"
    }

    for column in df.columns:
        normalized_column = str(column).strip().lower()

        if normalized_column in id_names:
            values = df[column].dropna()
            duplicate_ids = int(values.duplicated().sum())

            add_issue(
                issues,
                dataset_name,
                "Repeated ID Values",
                str(column),
                duplicate_ids,
                "Medium",
                "Repeated identifiers; confirm whether uniqueness is required"
            )

    # --------------------------------------------------
    # F. Negative numeric values
    # --------------------------------------------------

    numeric_terms = [
        "quantity",
        "weight",
        "freight cost",
        "insurance",
        "price",
        "value",
        "cost",
        "amount"
    ]

    for column in df.columns:
        column_name = str(column).lower()

        if any(term in column_name for term in numeric_terms):
            numeric_values = pd.to_numeric(
                df[column], errors="coerce"
            )

            negative_count = int((numeric_values < 0).sum())

            add_issue(
                issues,
                dataset_name,
                "Negative Numeric Values",
                str(column),
                negative_count,
                "Medium",
                "Negative values require business-rule validation"
            )

    # --------------------------------------------------
    # G. Invalid dates
    # --------------------------------------------------

    date_columns = [
        column for column in df.columns
        if "date" in str(column).lower()
        or "datetime" in str(column).lower()
    ]

    for column in date_columns:
        values = df[column]
        non_empty = values.notna() & (
            values.astype(str).str.strip() != ""
        )

        if not non_empty.any():
            continue

        parsed_dates = pd.to_datetime(
            values[non_empty],
            errors="coerce",
            format="mixed"
        )

        invalid_count = int(parsed_dates.isna().sum())

        add_issue(
            issues,
            dataset_name,
            "Invalid Date Values",
            str(column),
            invalid_count,
            "Medium",
            "Non-empty date values could not be parsed"
        )

    # --------------------------------------------------
    # H. Delivery date consistency
    # --------------------------------------------------

    column_lookup = {
        str(column).strip().lower(): column
        for column in df.columns
    }

    scheduled_column = next(
        (
            original for normalized, original in column_lookup.items()
            if "scheduled delivery date" in normalized
        ),
        None
    )

    delivered_column = next(
        (
            original for normalized, original in column_lookup.items()
            if "delivered to client date" in normalized
            or "delivery recorded date" in normalized
        ),
        None
    )

    if scheduled_column is not None and delivered_column is not None:
        scheduled = pd.to_datetime(
            df[scheduled_column], errors="coerce", format="mixed"
        )

        delivered = pd.to_datetime(
            df[delivered_column], errors="coerce", format="mixed"
        )

        both_dates_exist = scheduled.notna() & delivered.notna()

        late_delivery_count = int(
            (delivered[both_dates_exist] >
             scheduled[both_dates_exist]).sum()
        )

        add_issue(
            issues,
            dataset_name,
            "Late Delivery",
            str(delivered_column),
            late_delivery_count,
            "Medium",
            "Delivery date is later than scheduled date; verify business rules"
        )

    # --------------------------------------------------
    # I. Potential inconsistent vendor names
    # --------------------------------------------------

    vendor_columns = [
        column for column in df.columns
        if str(column).strip().lower() in {
            "vendor", "vendor name", "supplier", "supplier name"
        }
    ]

    for column in vendor_columns:
        original_names = df[column].dropna().astype(str).str.strip()
        original_names = original_names[original_names != ""]

        # Normalize case, whitespace and punctuation for comparison
        normalized_names = original_names.map(
            lambda value: re.sub(
                r"[^a-z0-9]+",
                "",
                value.casefold()
            )
        )

        comparison = pd.DataFrame({
            "Original": original_names,
            "Normalized": normalized_names
        })

        variants = comparison.groupby(
            "Normalized"
        )["Original"].nunique()

        variant_keys = set(variants[variants > 1].index)

        if variant_keys:
            flagged_rows = int(
                comparison["Normalized"].isin(variant_keys).sum()
            )

            variant_examples = (
                comparison[
                    comparison["Normalized"].isin(variant_keys)
                ]
                .groupby("Normalized")["Original"]
                .unique()
                .head(5)
                .tolist()
            )

            add_issue(
                issues,
                dataset_name,
                "Potential Inconsistent Vendor Names",
                str(column),
                flagged_rows,
                "Low",
                "Review spelling/case variants; examples: "
                + "; ".join(str(item) for item in variant_examples)
            )

    return issues


# ==================================================
# 5. MAIN PROCESS
# ==================================================

def main():
    if not RAW_DATA_DIR.exists():
        print(f"ERROR: Raw data folder not found: {RAW_DATA_DIR}")
        return

    supported_extensions = {
        ".csv", ".json", ".xml", ".xls", ".xlsx",
        ".sqlite", ".sqlite3", ".db"
    }

    files = sorted(
        path for path in RAW_DATA_DIR.rglob("*")
        if path.is_file()
        and path.suffix.lower() in supported_extensions
        and not path.name.startswith("~$")
    )

    all_issues = []
    dataset_summaries = []
    load_errors = []

    successful_files = 0
    successful_tables = 0

    for file_path in files:
        relative_path = file_path.relative_to(RAW_DATA_DIR)
        extension = file_path.suffix.lower()

        try:
            loaded = load_dataset(file_path)

            if extension in {".sqlite", ".sqlite3", ".db"}:
                tables = loaded.items()
            else:
                tables = [("", loaded)]

            file_success = True

            for table_name, df in tables:
                dataset_name = relative_path.as_posix()

                if table_name:
                    dataset_name += f" :: {table_name}"

                try:
                    if not isinstance(df, pd.DataFrame):
                        raise ValueError("Invalid dataframe")

                    if len(df.columns) == 0:
                        raise ValueError("Dataset has no columns")

                    issues = check_data_quality(dataset_name, df)
                    all_issues.extend(issues)

                    issue_rows = sum(
                        item["Affected Rows"] for item in issues
                    )

                    dataset_summaries.append({
                        "Dataset": dataset_name,
                        "Rows": len(df),
                        "Columns": len(df.columns),
                        "Missing Cells": int(df.isna().sum().sum()),
                        "Duplicate Rows": int(df.duplicated().sum()),
                        "Quality Issue Types": len(issues),
                        "Sum of Affected Rows Across Issues": issue_rows,
                        "Status": (
                            "Review Required" if issues else "No Issues Detected"
                        )
                    })

                    if table_name:
                        successful_tables += 1
                    else:
                        successful_files += 1

                    print(
                        f"Checked {dataset_name}: "
                        f"{len(df)} rows, {len(df.columns)} columns, "
                        f"{len(issues)} issue types"
                    )

                except Exception as error:
                    file_success = False

                    load_errors.append({
                        "Dataset": dataset_name,
                        "Error": str(error)
                    })

                    print(f"Could not check {dataset_name}: {error}")

            if not file_success:
                print(f"Some content in {file_path.name} needs review.")

        except Exception as error:
            load_errors.append({
                "Dataset": relative_path.as_posix(),
                "Error": str(error)
            })

            print(f"Could not load {file_path.name}: {error}")

    # ==================================================
    # 6. CREATE REPORT DATAFRAMES
    # ==================================================

    issues_df = pd.DataFrame(all_issues)
    summary_df = pd.DataFrame(dataset_summaries)
    errors_df = pd.DataFrame(load_errors)

    if not issues_df.empty:
        severity_summary = (
            issues_df.groupby("Severity", as_index=False)
            .agg(
                Issue_Types=("Issue Type", "count"),
                Affected_Rows_Sum=("Affected Rows", "sum")
            )
        )

        type_summary = (
            issues_df.groupby("Issue Type", as_index=False)
            .agg(
                Dataset_Count=("Dataset", "nunique"),
                Affected_Rows_Sum=("Affected Rows", "sum")
            )
        )
    else:
        severity_summary = pd.DataFrame(
            columns=[
                "Severity", "Issue_Types", "Affected_Rows_Sum"
            ]
        )

        type_summary = pd.DataFrame(
            columns=[
                "Issue Type", "Dataset_Count", "Affected_Rows_Sum"
            ]
        )

    # ==================================================
    # 7. SAVE CSV REPORTS
    # ==================================================

    issues_df.to_csv(
        REPORT_DIR / "data_quality_issues.csv",
        index=False
    )

    summary_df.to_csv(
        REPORT_DIR / "data_quality_summary.csv",
        index=False
    )

    errors_df.to_csv(
        REPORT_DIR / "data_quality_load_errors.csv",
        index=False
    )

    # ==================================================
    # 8. SAVE EXCEL REPORT
    # ==================================================

    excel_path = REPORT_DIR / "data_quality_report.xlsx"

    with pd.ExcelWriter(
        excel_path,
        engine="openpyxl"
    ) as writer:

        issues_df.to_excel(
            writer,
            sheet_name="Quality Issues",
            index=False
        )

        summary_df.to_excel(
            writer,
            sheet_name="Dataset Summary",
            index=False
        )

        severity_summary.to_excel(
            writer,
            sheet_name="Severity Summary",
            index=False
        )

        type_summary.to_excel(
            writer,
            sheet_name="Issue Type Summary",
            index=False
        )

        errors_df.to_excel(
            writer,
            sheet_name="Load Errors",
            index=False
        )

    # ==================================================
    # 9. FINAL RESULTS
    # ==================================================

    print("\n" + "=" * 50)
    print("DATA QUALITY CHECK COMPLETED")
    print("=" * 50)

    print(f"Source files found: {len(files)}")
    print(f"Non-SQLite datasets checked: {successful_files}")
    print(f"SQLite tables checked: {successful_tables}")
    print(f"Total datasets/tables checked: {len(summary_df)}")
    print(f"Quality issue records: {len(issues_df)}")
    print(f"Files/tables with load errors: {len(errors_df)}")

    print(f"\nExcel report: {excel_path}")
    print(f"Issues CSV: {REPORT_DIR / 'data_quality_issues.csv'}")
    print(f"Summary CSV: {REPORT_DIR / 'data_quality_summary.csv'}")
    print(f"Load errors: {REPORT_DIR / 'data_quality_load_errors.csv'}")


if __name__ == "__main__":
    main()
