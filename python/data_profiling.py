
from pathlib import Path
import json
import sqlite3
import pandas as pd


# ==================================================
# 1. PROJECT PATHS
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
REPORT_DIR = PROJECT_ROOT / "reports" / "data_profiling"

REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ==================================================
# 2. LOAD CSV
# ==================================================

def load_csv(file_path):
    return pd.read_csv(file_path)


# ==================================================
# 3. LOAD JSON
# ==================================================

def load_json(file_path):
    with open(file_path, "r", encoding="utf-8-sig") as file:
        data = json.load(file)

    if isinstance(data, list):
        if all(isinstance(item, dict) for item in data):
            return pd.json_normalize(data)
        return pd.DataFrame({"value": data})

    if isinstance(data, dict):
        # Find a list of records inside the JSON object
        for key, value in data.items():
            if isinstance(value, list) and all(
                isinstance(item, dict) for item in value
            ):
                return pd.json_normalize(value)

        # Handle a single JSON object
        return pd.json_normalize(data)

    raise ValueError(
        f"Unsupported JSON structure: {type(data).__name__}"
    )


# ==================================================
# 4. LOAD XML
# ==================================================

def load_xml(file_path):
    try:
        return pd.read_xml(file_path, parser="lxml")
    except Exception as first_error:
        try:
            return pd.read_xml(file_path, parser="etree")
        except Exception as second_error:
            raise ValueError(
                f"XML parsing failed. "
                f"lxml: {first_error}; etree: {second_error}"
            )


# ==================================================
# 5. LOAD EXCEL
# ==================================================

def load_excel(file_path):
    if file_path.suffix.lower() == ".xls":
        return pd.read_excel(file_path, engine="xlrd")

    return pd.read_excel(file_path, engine="openpyxl")


# ==================================================
# 6. LOAD SQLITE DATABASE
# ==================================================

def load_sqlite(file_path):
    """Read every table in a SQLite database."""

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
            # Escape quotes in table names safely
            safe_name = table_name.replace('"', '""')

            query = f'SELECT * FROM "{safe_name}"'
            tables[table_name] = pd.read_sql_query(
                query, connection
            )

    if not tables:
        raise ValueError("No user tables found in SQLite database.")

    return tables


# ==================================================
# 7. PROFILE ONE DATAFRAME
# ==================================================

def profile_dataframe(dataset_name, df):
    row_count = len(df)
    column_count = len(df.columns)

    missing_cells = int(df.isna().sum().sum())
    total_cells = row_count * column_count

    missing_percentage = (
        missing_cells / total_cells * 100
        if total_cells else 0
    )

    summary = {
        "Dataset": dataset_name,
        "Rows": row_count,
        "Columns": column_count,
        "Duplicate Rows": int(df.duplicated().sum()),
        "Missing Cells": missing_cells,
        "Missing Percentage": round(missing_percentage, 2),
        "Memory Usage (KB)": round(
            df.memory_usage(deep=True).sum() / 1024, 2
        )
    }

    column_profiles = []

    for column in df.columns:
        series = df[column]
        missing_count = int(series.isna().sum())

        if (
            pd.api.types.is_object_dtype(series)
            or pd.api.types.is_string_dtype(series)
        ):
            blank_count = int(
                series.astype("string").str.strip().eq("").sum()
            )
        else:
            blank_count = 0

        unique_count = int(series.nunique(dropna=True))

        missing_percent = (
            missing_count / row_count * 100
            if row_count else 0
        )

        value_counts = series.value_counts(dropna=True)
        repeated_occurrences = int(
            value_counts[value_counts > 1].sum()
        )

        sample_values = (
            series.dropna()
            .astype(str)
            .drop_duplicates()
            .head(5)
            .tolist()
        )

        profile = {
            "Dataset": dataset_name,
            "Column": str(column),
            "Data Type": str(series.dtype),
            "Missing Values": missing_count,
            "Missing Percentage": round(missing_percent, 2),
            "Blank Values": blank_count,
            "Unique Values": unique_count,
            "Repeated Value Occurrences": repeated_occurrences,
            "Sample Values": " | ".join(sample_values)
        }

        if pd.api.types.is_numeric_dtype(series):
            profile["Minimum"] = series.min()
            profile["Maximum"] = series.max()
            profile["Mean"] = series.mean()
            profile["Median"] = series.median()
        else:
            profile["Minimum"] = None
            profile["Maximum"] = None
            profile["Mean"] = None
            profile["Median"] = None

        column_profiles.append(profile)

    return summary, column_profiles


# ==================================================
# 8. MAIN PROFILING PROCESS
# ==================================================

def main():
    if not RAW_DATA_DIR.exists():
        print(f"ERROR: Folder not found: {RAW_DATA_DIR}")
        return

    supported_extensions = {
        ".csv", ".json", ".xml", ".xls", ".xlsx",
        ".sqlite", ".sqlite3", ".db"
    }

    dataset_files = sorted(
        file_path
        for file_path in RAW_DATA_DIR.rglob("*")
        if file_path.is_file()
        and file_path.suffix.lower() in supported_extensions
        and not file_path.name.startswith("~$")
    )

    if not dataset_files:
        print("No supported datasets found.")
        return

    dataset_summaries = []
    all_column_profiles = []
    load_errors = []

    successful_files = 0
    successful_tables = 0

    for file_path in dataset_files:
        relative_path = file_path.relative_to(RAW_DATA_DIR)
        extension = file_path.suffix.lower()

        try:
            if extension in {".sqlite", ".sqlite3", ".db"}:
                tables = load_sqlite(file_path)

                for table_name, df in tables.items():
                    dataset_name = (
                        f"{relative_path.as_posix()} :: {table_name}"
                    )

                    try:
                        if len(df.columns) == 0:
                            raise ValueError(
                                "Table contains no columns."
                            )

                        summary, column_profiles = profile_dataframe(
                            dataset_name, df
                        )

                        dataset_summaries.append(summary)
                        all_column_profiles.extend(column_profiles)
                        successful_tables += 1

                        print(
                            f"Profiled ERP table {table_name}: "
                            f"{len(df)} rows, {len(df.columns)} columns"
                        )

                    except Exception as error:
                        load_errors.append({
                            "Dataset": dataset_name,
                            "Error": str(error)
                        })

                        print(
                            f"Could not profile table {table_name}: "
                            f"{error}"
                        )

            else:
                if extension == ".csv":
                    df = load_csv(file_path)
                elif extension == ".json":
                    df = load_json(file_path)
                elif extension == ".xml":
                    df = load_xml(file_path)
                elif extension in {".xls", ".xlsx"}:
                    df = load_excel(file_path)
                else:
                    continue

                if len(df.columns) == 0:
                    raise ValueError("Dataset contains no columns.")

                dataset_name = relative_path.as_posix()

                summary, column_profiles = profile_dataframe(
                    dataset_name, df
                )

                dataset_summaries.append(summary)
                all_column_profiles.extend(column_profiles)
                successful_files += 1

                print(
                    f"Profiled {file_path.name}: "
                    f"{len(df)} rows, {len(df.columns)} columns"
                )

        except Exception as error:
            load_errors.append({
                "Dataset": relative_path.as_posix(),
                "Error": str(error)
            })

            print(
                f"Could not load {file_path.name}: {error}"
            )

    # ==================================================
    # 9. CREATE REPORT DATAFRAMES
    # ==================================================

    summary_df = pd.DataFrame(dataset_summaries)
    columns_df = pd.DataFrame(all_column_profiles)
    errors_df = pd.DataFrame(load_errors)

    # ==================================================
    # 10. SAVE CSV REPORTS
    # ==================================================

    summary_df.to_csv(
        REPORT_DIR / "dataset_summary.csv",
        index=False
    )

    columns_df.to_csv(
        REPORT_DIR / "column_profiling.csv",
        index=False
    )

    errors_df.to_csv(
        REPORT_DIR / "profiling_errors.csv",
        index=False
    )

    # ==================================================
    # 11. SAVE EXCEL REPORT
    # ==================================================

    excel_path = REPORT_DIR / "data_profiling_report.xlsx"

    with pd.ExcelWriter(
        excel_path,
        engine="openpyxl"
    ) as writer:

        summary_df.to_excel(
            writer,
            sheet_name="Dataset Summary",
            index=False
        )

        columns_df.to_excel(
            writer,
            sheet_name="Column Profiling",
            index=False
        )

        errors_df.to_excel(
            writer,
            sheet_name="Load Errors",
            index=False
        )

    # ==================================================
    # 12. PRINT FINAL RESULTS
    # ==================================================

    print("\n" + "=" * 50)
    print("DATA PROFILING COMPLETED")
    print("=" * 50)

    print(f"Source files found: {len(dataset_files)}")
    print(f"Non-SQLite files profiled: {successful_files}")
    print(f"SQLite tables profiled: {successful_tables}")
    print(f"Total datasets/tables profiled: {len(summary_df)}")
    print(f"Files/tables with errors: {len(errors_df)}")

    print(f"\nExcel report: {excel_path}")
    print(f"Dataset summary: {REPORT_DIR / 'dataset_summary.csv'}")
    print(f"Column profiling: {REPORT_DIR / 'column_profiling.csv'}")
    print(f"Errors: {REPORT_DIR / 'profiling_errors.csv'}")


if __name__ == "__main__":
    main()
