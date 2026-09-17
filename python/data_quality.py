import pandas as pd
from pathlib import Path
import json
import xml.etree.ElementTree as ET


# ============================================================
# SUPPLY CHAIN DATA QUALITY CHECK
# ============================================================

print("=" * 60)
print("              SUPPLY CHAIN DATA QUALITY")
print("=" * 60)
print()


# ============================================================
# 1. PROJECT PATHS
# ============================================================

# Current file:
# ESCDP/etl/python/data_quality.py
#
# parents[0] = python
# parents[1] = etl
# parents[2] = ESCDP

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Dataset location
RAW_DATA_FOLDER = PROJECT_ROOT / "data" / "raw"

# Existing report folder
OUTPUT_FOLDER = PROJECT_ROOT / "reports" / "data quality"

# Create folder if it does not exist
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)


print("Project folder:")
print(PROJECT_ROOT)

print()

print("Looking for datasets in:")
print(RAW_DATA_FOLDER)

print()


# ============================================================
# 2. LOAD DATASET
# ============================================================

def load_dataset(file_path):

    extension = file_path.suffix.lower()

    try:

        # ----------------------------------------------------
        # CSV
        # ----------------------------------------------------

        if extension == ".csv":

            return pd.read_csv(file_path)


        # ----------------------------------------------------
        # JSON
        # ----------------------------------------------------

        elif extension == ".json":

            try:

                return pd.read_json(file_path)

            except Exception:

                with open(
                    file_path,
                    "r",
                    encoding="utf-8"
                ) as f:

                    data = json.load(f)


                if isinstance(data, list):

                    return pd.DataFrame(data)


                elif isinstance(data, dict):

                    # Look for list of records
                    for value in data.values():

                        if isinstance(value, list):

                            return pd.DataFrame(value)

                    # Single record
                    return pd.DataFrame([data])


        # ----------------------------------------------------
        # XML
        # ----------------------------------------------------

        elif extension == ".xml":

            try:

                return pd.read_xml(file_path)

            except Exception as xml_error:

                print(
                    f"XML warning for "
                    f"{file_path.name}: {xml_error}"
                )

                # Generic XML fallback
                tree = ET.parse(file_path)

                root = tree.getroot()

                rows = []

                for child in root:

                    row = {}

                    for element in child:

                        row[element.tag] = element.text

                    if row:

                        rows.append(row)

                if rows:

                    return pd.DataFrame(rows)

                return None


        # ----------------------------------------------------
        # Excel
        # ----------------------------------------------------

        elif extension in [".xlsx", ".xls"]:

            return pd.read_excel(file_path)


        # ----------------------------------------------------
        # Unsupported file
        # ----------------------------------------------------

        else:

            print(
                f"Unsupported file format: "
                f"{file_path.name}"
            )

            return None


    except Exception as error:

        print(
            f"ERROR loading {file_path.name}: "
            f"{error}"
        )

        return None


# ============================================================
# 3. ADD QUALITY ISSUE
# ============================================================

def add_issue(
    issues,
    dataset,
    column,
    issue_type,
    issue_count,
    percentage,
    severity,
    description
):

    issues.append({

        "Dataset": dataset,

        "Column": column,

        "Issue Type": issue_type,

        "Issue Count": issue_count,

        "Percentage": round(
            percentage,
            2
        ),

        "Severity": severity,

        "Description": description

    })


# ============================================================
# 4. CHECK ONE DATASET
# ============================================================

def check_dataset(df, dataset_name):

    issues = []

    total_rows = len(df)


    # ========================================================
    # CHECK 1: DUPLICATE ROWS
    # ========================================================

    duplicate_rows = df.duplicated().sum()

    if duplicate_rows > 0:

        percentage = (
            duplicate_rows /
            total_rows *
            100
            if total_rows > 0
            else 0
        )

        if percentage >= 10:

            severity = "High"

        elif percentage >= 2:

            severity = "Medium"

        else:

            severity = "Low"


        add_issue(

            issues,

            dataset_name,

            "ALL COLUMNS",

            "Duplicate Rows",

            duplicate_rows,

            percentage,

            severity,

            "Completely duplicated records found."

        )


    # ========================================================
    # CHECK EVERY COLUMN
    # ========================================================

    for column in df.columns:

        series = df[column]


        # ====================================================
        # CHECK 2: MISSING VALUES
        # ====================================================

        missing_count = series.isna().sum()

        if missing_count > 0:

            percentage = (
                missing_count /
                total_rows *
                100
                if total_rows > 0
                else 0
            )


            if percentage >= 20:

                severity = "High"

            elif percentage >= 5:

                severity = "Medium"

            else:

                severity = "Low"


            add_issue(

                issues,

                dataset_name,

                column,

                "Missing Values",

                missing_count,

                percentage,

                severity,

                "Column contains missing/null values."

            )


        # ====================================================
        # CHECK 3: BLANK STRINGS
        # ====================================================

        if (
            pd.api.types.is_object_dtype(series)
            or
            pd.api.types.is_string_dtype(series)
        ):

            blank_count = (
                series
                .fillna("")
                .astype(str)
                .str.strip()
                .eq("")
                .sum()
            )


            if blank_count > 0:

                percentage = (
                    blank_count /
                    total_rows *
                    100
                    if total_rows > 0
                    else 0
                )


                if percentage >= 10:

                    severity = "High"

                elif percentage >= 2:

                    severity = "Medium"

                else:

                    severity = "Low"


                add_issue(

                    issues,

                    dataset_name,

                    column,

                    "Blank Values",

                    blank_count,

                    percentage,

                    severity,

                    "Column contains blank or empty string values."

                )


        # ====================================================
        # CHECK 4: LEADING / TRAILING WHITESPACE
        # ====================================================

        if (
            pd.api.types.is_object_dtype(series)
            or
            pd.api.types.is_string_dtype(series)
        ):

            try:

                whitespace_count = (
                    series
                    .dropna()
                    .astype(str)
                    .apply(
                        lambda x:
                        x != x.strip()
                    )
                    .sum()
                )

            except Exception:

                whitespace_count = 0


            if whitespace_count > 0:

                percentage = (
                    whitespace_count /
                    total_rows *
                    100
                    if total_rows > 0
                    else 0
                )


                add_issue(

                    issues,

                    dataset_name,

                    column,

                    "Whitespace Issues",

                    whitespace_count,

                    percentage,

                    "Low",

                    "Values contain leading or trailing whitespace."

                )


        # ====================================================
        # CHECK 5: NEGATIVE NUMERIC VALUES
        # ====================================================

        if pd.api.types.is_numeric_dtype(series):

            try:

                negative_count = (
                    series < 0
                ).sum()

            except Exception:

                negative_count = 0


            if negative_count > 0:

                percentage = (
                    negative_count /
                    total_rows *
                    100
                    if total_rows > 0
                    else 0
                )


                add_issue(

                    issues,

                    dataset_name,

                    column,

                    "Negative Values",

                    negative_count,

                    percentage,

                    "Medium",

                    "Negative numeric values detected. "
                    "Verify whether negative values are valid "
                    "for this business field."

                )


        # ====================================================
        # CHECK 6: PERCENTAGE VALUES OUTSIDE 0-100
        # ====================================================

        column_lower = str(column).lower()

        percentage_keywords = [

            "percent",

            "percentage",

            "rate",

            "discount rate",

            "%"

        ]


        is_percentage_column = any(

            keyword in column_lower

            for keyword in percentage_keywords

        )


        if (
            is_percentage_column
            and
            pd.api.types.is_numeric_dtype(series)
        ):

            invalid_percentage = (
                (series < 0)
                |
                (series > 100)
            ).sum()


            if invalid_percentage > 0:

                percentage = (
                    invalid_percentage /
                    total_rows *
                    100
                    if total_rows > 0
                    else 0
                )


                add_issue(

                    issues,

                    dataset_name,

                    column,

                    "Invalid Percentage",

                    invalid_percentage,

                    percentage,

                    "High",

                    "Percentage/rate value is outside "
                    "the expected 0-100 range."

                )


        # ====================================================
        # CHECK 7: INVALID DATE VALUES
        # ====================================================

        column_lower = str(column).lower()

        date_keywords = [

            "date",

            "time",

            "timestamp"

        ]


        is_date_column = any(

            keyword in column_lower

            for keyword in date_keywords

        )


        if is_date_column:

            try:

                converted_dates = pd.to_datetime(

                    series,

                    errors="coerce"

                )


                invalid_dates = (

                    converted_dates.isna()
                    &
                    series.notna()

                ).sum()


                if invalid_dates > 0:

                    percentage = (
                        invalid_dates /
                        total_rows *
                        100
                        if total_rows > 0
                        else 0
                    )


                    if percentage >= 10:

                        severity = "High"

                    elif percentage >= 2:

                        severity = "Medium"

                    else:

                        severity = "Low"


                    add_issue(

                        issues,

                        dataset_name,

                        column,

                        "Invalid Date Values",

                        invalid_dates,

                        percentage,

                        severity,

                        "Values could not be interpreted "
                        "as valid dates."

                    )

            except Exception:

                pass


        # ====================================================
        # CHECK 8: POSSIBLE DUPLICATE IDENTIFIER VALUES
        # ====================================================

        # We only report this as a DATA QUALITY observation.
        # Repeated Order IDs can be valid because one order
        # can contain multiple order lines.

        identifier_keywords = [

            "id",

            "number",

            "no.",

            "#"

        ]


        is_identifier = any(

            keyword in column_lower

            for keyword in identifier_keywords

        )


        if is_identifier:

            non_null = series.dropna()

            if len(non_null) > 0:

                duplicated_identifier_count = (
                    non_null.duplicated()
                    .sum()
                )


                if duplicated_identifier_count > 0:

                    percentage = (
                        duplicated_identifier_count /
                        len(non_null) *
                        100
                    )


                    add_issue(

                        issues,

                        dataset_name,

                        column,

                        "Repeated Identifier Values",

                        duplicated_identifier_count,

                        percentage,

                        "Review",

                        "Identifier-like values are repeated. "
                        "Check whether repetition is expected "
                        "for the dataset grain."

                    )


    return issues


# ============================================================
# 5. MAIN FUNCTION
# ============================================================

def main():

    print("=" * 60)
    print("SEARCHING FOR DATASETS")
    print("=" * 60)
    print()


    # --------------------------------------------------------
    # Check data/raw folder
    # --------------------------------------------------------

    if not RAW_DATA_FOLDER.exists():

        print(
            "ERROR: data/raw folder was not found."
        )

        print()

        print(
            "Expected location:"
        )

        print(RAW_DATA_FOLDER)

        return


    # --------------------------------------------------------
    # Supported files
    # --------------------------------------------------------

    supported_extensions = [

        ".csv",

        ".json",

        ".xml",

        ".xlsx",

        ".xls"

    ]


    # --------------------------------------------------------
    # Find dataset files
    # --------------------------------------------------------

    dataset_files = [

        file

        for file in RAW_DATA_FOLDER.iterdir()

        if file.is_file()

        and file.suffix.lower()
        in supported_extensions

    ]


    # --------------------------------------------------------
    # No datasets
    # --------------------------------------------------------

    if not dataset_files:

        print(
            "ERROR: No datasets found inside data/raw."
        )

        print()

        print(
            "Put all your dataset files here:"
        )

        print(RAW_DATA_FOLDER)

        return


    print(
        f"Found {len(dataset_files)} dataset(s)."
    )

    print()


    # ========================================================
    # RESULT STORAGE
    # ========================================================

    all_issues = []

    dataset_summary = []


    # ========================================================
    # PROCESS DATASETS
    # ========================================================

    for file_path in sorted(dataset_files):

        print("-" * 60)

        print(
            f"Checking: {file_path.name}"
        )


        # ----------------------------------------------------
        # Load
        # ----------------------------------------------------

        df = load_dataset(file_path)


        if df is None:

            print(
                f"FAILED: {file_path.name}"
            )

            print()

            continue


        print(
            f"Loaded successfully."
        )

        print(
            f"Rows: {df.shape[0]}"
        )

        print(
            f"Columns: {df.shape[1]}"
        )


        # ----------------------------------------------------
        # Run quality checks
        # ----------------------------------------------------

        issues = check_dataset(

            df,

            file_path.name

        )


        all_issues.extend(issues)


        # ----------------------------------------------------
        # Dataset summary
        # ----------------------------------------------------

        total_cells = (
            df.shape[0] *
            df.shape[1]
        )


        missing_cells = (
            df.isna()
            .sum()
            .sum()
        )


        duplicate_rows = (
            df.duplicated()
            .sum()
        )


        # Count issue records for this dataset
        dataset_issue_count = len(issues)


        # ----------------------------------------------------
        # Overall quality status
        # ----------------------------------------------------

        high_count = sum(

            1

            for issue in issues

            if issue["Severity"] == "High"

        )


        medium_count = sum(

            1

            for issue in issues

            if issue["Severity"] == "Medium"

        )


        if high_count > 0:

            quality_status = "Needs Attention"

        elif medium_count > 0:

            quality_status = "Review Required"

        elif dataset_issue_count > 0:

            quality_status = "Minor Issues"

        else:

            quality_status = "Good"


        dataset_summary.append({

            "Dataset":

                file_path.name,

            "Rows":

                df.shape[0],

            "Columns":

                df.shape[1],

            "Total Cells":

                total_cells,

            "Missing Cells":

                missing_cells,

            "Duplicate Rows":

                duplicate_rows,

            "Quality Issues":

                dataset_issue_count,

            "High Severity Issues":

                high_count,

            "Medium Severity Issues":

                medium_count,

            "Quality Status":

                quality_status

        })


        print(
            f"Quality issues found: "
            f"{dataset_issue_count}"
        )

        print()


    # ========================================================
    # CREATE DATAFRAMES
    # ========================================================

    issues_df = pd.DataFrame(
        all_issues
    )


    summary_df = pd.DataFrame(
        dataset_summary
    )


    # ========================================================
    # IF NO ISSUES FOUND
    # ========================================================

    if issues_df.empty:

        issues_df = pd.DataFrame({

            "Dataset": [],

            "Column": [],

            "Issue Type": [],

            "Issue Count": [],

            "Percentage": [],

            "Severity": [],

            "Description": []

        })


    # ========================================================
    # SEVERITY SUMMARY
    # ========================================================

    if not issues_df.empty:

        severity_summary = (

            issues_df
            .groupby("Severity")
            .size()
            .reset_index(
                name="Number of Issues"
            )

        )

    else:

        severity_summary = pd.DataFrame({

            "Severity": [],

            "Number of Issues": []

        })


    # ========================================================
    # ISSUE TYPE SUMMARY
    # ========================================================

    if not issues_df.empty:

        issue_type_summary = (

            issues_df
            .groupby("Issue Type")
            .agg(

                Number_of_Issues=(
                    "Issue Type",
                    "count"
                ),

                Total_Affected_Records=(
                    "Issue Count",
                    "sum"
                )

            )
            .reset_index()

        )

    else:

        issue_type_summary = pd.DataFrame({

            "Issue Type": [],

            "Number_of_Issues": [],

            "Total_Affected_Records": []

        })


    # ========================================================
    # SAVE EXCEL REPORT
    # ========================================================

    excel_file = (

        OUTPUT_FOLDER /

        "data_quality_report.xlsx"

    )


    with pd.ExcelWriter(

        excel_file,

        engine="openpyxl"

    ) as writer:


        # ----------------------------------------------------
        # Sheet 1
        # ----------------------------------------------------

        issues_df.to_excel(

            writer,

            sheet_name="Quality Issues",

            index=False

        )


        # ----------------------------------------------------
        # Sheet 2
        # ----------------------------------------------------

        summary_df.to_excel(

            writer,

            sheet_name="Dataset Summary",

            index=False

        )


        # ----------------------------------------------------
        # Sheet 3
        # ----------------------------------------------------

        severity_summary.to_excel(

            writer,

            sheet_name="Severity Summary",

            index=False

        )


        # ----------------------------------------------------
        # Sheet 4
        # ----------------------------------------------------

        issue_type_summary.to_excel(

            writer,

            sheet_name="Issue Type Summary",

            index=False

        )


    # ========================================================
    # SAVE CSV FILES
    # ========================================================

    issues_csv = (

        OUTPUT_FOLDER /

        "data_quality_issues.csv"

    )


    summary_csv = (

        OUTPUT_FOLDER /

        "data_quality_summary.csv"

    )


    issues_df.to_csv(

        issues_csv,

        index=False

    )


    summary_df.to_csv(

        summary_csv,

        index=False

    )


    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    print("=" * 60)

    print("             DATA QUALITY COMPLETED")

    print("=" * 60)

    print()

    print("Reports saved in:")

    print(OUTPUT_FOLDER)

    print()

    print("Files created:")

    print("1. data_quality_report.xlsx")

    print("2. data_quality_issues.csv")

    print("3. data_quality_summary.csv")

    print()

    print(
        f"Datasets checked: "
        f"{len(summary_df)}"
    )

    print(
        f"Total quality issue records: "
        f"{len(issues_df)}"
    )

    print()


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":

    main()