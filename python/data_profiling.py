import pandas as pd
from pathlib import Path
import json
import xml.etree.ElementTree as ET


# ============================================================
# SUPPLY CHAIN DATA PROFILING
# ============================================================

print("=" * 60)
print("              SUPPLY CHAIN DATA PROFILING")
print("=" * 60)
print()


# ============================================================
# 1. PROJECT PATHS
# ============================================================

# Current file:
# ESCDP/etl/python/data_profiling.py
#
# parents[0] = python
# parents[1] = etl
# parents[2] = ESCDP

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Location of all datasets
RAW_DATA_FOLDER = PROJECT_ROOT / "data" / "raw"

# Location where profiling reports will be saved
OUTPUT_FOLDER = PROJECT_ROOT / "reports" / "data profiling"

# Create output folder if it doesn't already exist
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)


print("Project folder:")
print(PROJECT_ROOT)
print()

print("Looking for datasets in:")
print(RAW_DATA_FOLDER)
print()


# ============================================================
# 2. LOAD DATASET FUNCTION
# ============================================================

def load_dataset(file_path):

    extension = file_path.suffix.lower()

    try:

        # ----------------------------------------------------
        # CSV
        # ----------------------------------------------------

        if extension == ".csv":

            df = pd.read_csv(file_path)

            return df


        # ----------------------------------------------------
        # JSON
        # ----------------------------------------------------

        elif extension == ".json":

            try:

                # First try normal Pandas JSON loading
                df = pd.read_json(file_path)

                return df

            except Exception:

                # If that fails, load JSON manually
                with open(
                    file_path,
                    "r",
                    encoding="utf-8"
                ) as f:

                    data = json.load(f)


                # JSON contains a list of records
                if isinstance(data, list):

                    return pd.DataFrame(data)


                # JSON contains a dictionary
                elif isinstance(data, dict):

                    # Look for a list inside dictionary
                    for value in data.values():

                        if isinstance(value, list):

                            return pd.DataFrame(value)


                    # Single dictionary record
                    return pd.DataFrame([data])


        # ----------------------------------------------------
        # XML
        # ----------------------------------------------------

        elif extension == ".xml":

            try:

                # Try Pandas XML reader
                df = pd.read_xml(file_path)

                return df

            except Exception as xml_error:

                print(
                    f"XML reader warning for "
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
        # EXCEL
        # ----------------------------------------------------

        elif extension in [".xlsx", ".xls"]:

            df = pd.read_excel(file_path)

            return df


        # ----------------------------------------------------
        # Unsupported format
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
# 3. PROFILE DATASET FUNCTION
# ============================================================

def profile_dataset(df, dataset_name):

    results = []


    # --------------------------------------------------------
    # Dataset information
    # --------------------------------------------------------

    total_rows = len(df)

    total_columns = len(df.columns)

    duplicate_rows = df.duplicated().sum()


    # --------------------------------------------------------
    # Profile every column
    # --------------------------------------------------------

    for column in df.columns:

        series = df[column]


        # ----------------------------------------------------
        # Missing values
        # ----------------------------------------------------

        missing_count = series.isna().sum()

        if total_rows > 0:

            missing_percentage = (
                missing_count /
                total_rows
            ) * 100

        else:

            missing_percentage = 0


        # ----------------------------------------------------
        # Unique values
        # ----------------------------------------------------

        unique_count = series.nunique(
            dropna=True
        )


        # ----------------------------------------------------
        # Duplicate values
        # ----------------------------------------------------

        duplicate_values = series.duplicated().sum()


        # ----------------------------------------------------
        # Data type
        # ----------------------------------------------------

        data_type = str(series.dtype)


        # ----------------------------------------------------
        # Numeric statistics
        # ----------------------------------------------------

        if pd.api.types.is_numeric_dtype(series):

            minimum = series.min()

            maximum = series.max()

            mean = series.mean()

            median = series.median()

            standard_deviation = series.std()

        else:

            minimum = ""

            maximum = ""

            mean = ""

            median = ""

            standard_deviation = ""


        # ----------------------------------------------------
        # Most frequent value
        # ----------------------------------------------------

        if not series.dropna().empty:

            mode_values = series.mode()

            if not mode_values.empty:

                most_frequent = mode_values.iloc[0]

            else:

                most_frequent = ""

        else:

            most_frequent = ""


        # ----------------------------------------------------
        # Store profiling result
        # ----------------------------------------------------

        results.append({

            "Dataset": dataset_name,

            "Column": column,

            "Data Type": data_type,

            "Total Rows": total_rows,

            "Missing Values": missing_count,

            "Missing %": round(
                missing_percentage,
                2
            ),

            "Unique Values": unique_count,

            "Duplicate Values": duplicate_values,

            "Minimum": minimum,

            "Maximum": maximum,

            "Mean": mean,

            "Median": median,

            "Standard Deviation":
                standard_deviation,

            "Most Frequent Value":
                most_frequent,

            "Duplicate Rows in Dataset":
                duplicate_rows

        })


    return results


# ============================================================
# 4. MAIN PROFILING PROCESS
# ============================================================

def main():

    print("=" * 60)
    print("SEARCHING FOR DATASETS")
    print("=" * 60)
    print()


    # --------------------------------------------------------
    # Check raw folder
    # --------------------------------------------------------

    if not RAW_DATA_FOLDER.exists():

        print("ERROR: data/raw folder was not found.")

        print()

        print(
            "Expected location:"
        )

        print(RAW_DATA_FOLDER)

        return


    # --------------------------------------------------------
    # Supported file types
    # --------------------------------------------------------

    supported_extensions = [

        ".csv",

        ".json",

        ".xml",

        ".xlsx",

        ".xls"

    ]


    # --------------------------------------------------------
    # Find datasets
    # --------------------------------------------------------

    dataset_files = [

        file

        for file in RAW_DATA_FOLDER.iterdir()

        if file.is_file()

        and file.suffix.lower()
        in supported_extensions

    ]


    # --------------------------------------------------------
    # Check whether datasets exist
    # --------------------------------------------------------

    if not dataset_files:

        print(
            "ERROR: No datasets were found "
            "inside data/raw."
        )

        print()

        print(
            "Please place your dataset files here:"
        )

        print(RAW_DATA_FOLDER)

        return


    print(
        f"Found {len(dataset_files)} dataset(s)."
    )

    print()


    # ========================================================
    # Storage for results
    # ========================================================

    all_column_profiles = []

    dataset_summary = []

    successfully_loaded = 0


    # ========================================================
    # PROCESS EACH DATASET
    # ========================================================

    for file_path in sorted(dataset_files):

        print("-" * 60)

        print(
            f"Loading: {file_path.name}"
        )


        # ----------------------------------------------------
        # Load dataset
        # ----------------------------------------------------

        df = load_dataset(file_path)


        # ----------------------------------------------------
        # Failed dataset
        # ----------------------------------------------------

        if df is None:

            print(
                f"FAILED: {file_path.name}"
            )

            print()

            continue


        # ----------------------------------------------------
        # Successful dataset
        # ----------------------------------------------------

        successfully_loaded += 1


        print(
            f"Successfully loaded: "
            f"{file_path.name}"
        )

        print(
            f"Rows: {df.shape[0]}"
        )

        print(
            f"Columns: {df.shape[1]}"
        )

        print()


        # ====================================================
        # DATASET SUMMARY
        # ====================================================

        total_cells = (
            df.shape[0] *
            df.shape[1]
        )


        missing_cells = (
            df.isna()
            .sum()
            .sum()
        )


        if total_cells > 0:

            missing_percentage = (
                missing_cells /
                total_cells
            ) * 100

        else:

            missing_percentage = 0


        duplicate_rows = (
            df.duplicated()
            .sum()
        )


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

            "Missing %":
                round(
                    missing_percentage,
                    2
                ),

            "Duplicate Rows":
                duplicate_rows,

            "Memory Usage (KB)":
                round(
                    df.memory_usage(
                        deep=True
                    ).sum() / 1024,
                    2
                )

        })


        # ====================================================
        # COLUMN PROFILING
        # ====================================================

        profile_results = profile_dataset(

            df,

            file_path.name

        )


        all_column_profiles.extend(
            profile_results
        )


    # ========================================================
    # CHECK SUCCESS
    # ========================================================

    print("=" * 60)

    if successfully_loaded == 0:

        print(
            "ERROR: No datasets were "
            "successfully loaded."
        )

        print()

        print(
            "Please check your dataset files "
            "and their formats."
        )

        return


    print(
        f"{successfully_loaded} dataset(s) "
        f"successfully profiled."
    )

    print("=" * 60)

    print()


    # ========================================================
    # CREATE DATAFRAMES
    # ========================================================

    summary_df = pd.DataFrame(
        dataset_summary
    )


    column_profile_df = pd.DataFrame(
        all_column_profiles
    )


    # ========================================================
    # SAVE EXCEL REPORT
    # ========================================================

    excel_file = (
        OUTPUT_FOLDER /
        "data_profiling_report.xlsx"
    )


    with pd.ExcelWriter(

        excel_file,

        engine="openpyxl"

    ) as writer:


        # ----------------------------------------------------
        # Sheet 1: Dataset Summary
        # ----------------------------------------------------

        summary_df.to_excel(

            writer,

            sheet_name="Dataset Summary",

            index=False

        )


        # ----------------------------------------------------
        # Sheet 2: Column Profiling
        # ----------------------------------------------------

        column_profile_df.to_excel(

            writer,

            sheet_name="Column Profiling",

            index=False

        )


        # ----------------------------------------------------
        # Add sample data from each dataset
        # ----------------------------------------------------

        for file_path in sorted(
            dataset_files
        ):

            df = load_dataset(
                file_path
            )


            if df is not None:

                # Excel sheet names have
                # maximum 31 characters

                sheet_name = (
                    file_path.stem[:25]
                    + "_Sample"
                )


                df.head(100).to_excel(

                    writer,

                    sheet_name=sheet_name[:31],

                    index=False

                )


    # ========================================================
    # SAVE CSV REPORTS
    # ========================================================

    summary_csv = (
        OUTPUT_FOLDER /
        "dataset_summary.csv"
    )


    column_csv = (
        OUTPUT_FOLDER /
        "column_profiling.csv"
    )


    summary_df.to_csv(

        summary_csv,

        index=False

    )


    column_profile_df.to_csv(

        column_csv,

        index=False

    )


    # ========================================================
    # FINAL MESSAGE
    # ========================================================

    print("=" * 60)

    print("             PROFILING COMPLETED")

    print("=" * 60)

    print()

    print("Reports saved in:")

    print(OUTPUT_FOLDER)

    print()

    print("Files created:")

    print(
        "1. data_profiling_report.xlsx"
    )

    print(
        "2. dataset_summary.csv"
    )

    print(
        "3. column_profiling.csv"
    )

    print()

    print(
        "Open the Excel file to view "
        "the profiling results."
    )

    print()


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":

    main()