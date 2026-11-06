import logging

import pandas as pd


logger = logging.getLogger(__name__)


def remove_duplicates(df):
    """Remove duplicate rows."""
    rows_before = len(df)
    result = df.drop_duplicates()
    rows_after = len(result)

    logger.debug(f"remove_duplicates: {rows_before} -> {rows_after} rows")
    return result


def handle_missing(df, axis="rows"):
    """Drop rows or columns containing missing values."""
    if axis == "rows":
        rows_before = len(df)
        result = df.dropna(axis=0)
        rows_after = len(result)
        logger.debug(f"handle_missing: {rows_before} -> {rows_after} rows")
    elif axis == "columns":
        columns_before = len(df.columns)
        result = df.dropna(axis=1)
        columns_after = len(result.columns)
        logger.debug(
            f"handle_missing: {columns_before} -> "
            f"{columns_after} columns"
        )
    else:
        logger.error(f"Unsupported missing value axis: {axis}")
        raise ValueError(f"Unsupported missing value axis: {axis}")

    return result


def remove_outliers(df, columns, method, threshold):
    """Remove outliers from the specified numeric columns."""
    if method not in ["iqr", "zscore"]:
        logger.error(f"Unsupported outlier method: {method}")
        raise ValueError(f"Unsupported outlier method: {method}")

    result = df

    for column in columns:
        if column not in result.columns:
            logger.warning(f"Column not found: {column}")
            continue

        if not pd.api.types.is_numeric_dtype(result[column]):
            logger.warning(f"Column is not numeric: {column}")
            continue

        rows_before = len(result)

        if method == "iqr":
            q1 = result[column].quantile(0.25)
            q3 = result[column].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - threshold * iqr
            upper = q3 + threshold * iqr

            result = result[
                (result[column] >= lower) & (result[column] <= upper)
            ]
            rows_removed = rows_before - len(result)
            logger.debug(
                f"{column}: method={method}, threshold={threshold}, "
                f"lower={lower}, upper={upper}, removed={rows_removed}"
            )
        else:
            mean = result[column].mean()
            standard_deviation = result[column].std()

            if standard_deviation == 0 or pd.isna(standard_deviation):
                rows_removed = 0
            else:
                z_scores = ((result[column] - mean) / standard_deviation).abs()
                result = result[z_scores <= threshold]
                rows_removed = rows_before - len(result)

            logger.debug(
                f"{column}: method={method}, threshold={threshold}, "
                f"removed={rows_removed}"
            )

    return result


def process_data(df, config):
    """Apply the processing steps enabled in the configuration."""
    processing = config["processing"]
    result = df

    if processing["remove_duplicates"]:
        result = remove_duplicates(result)

    if processing["missing"]["enabled"]:
        result = handle_missing(
            result,
            processing["missing"]["axis"],
        )

    if processing["outliers"]["enabled"]:
        result = remove_outliers(
            result,
            processing["outliers"]["columns"],
            processing["outliers"]["method"],
            processing["outliers"]["threshold"],
        )

    return result


def create_cleaning_report(df_before, df_after):
    """Return a dictionary summarizing the cleaning results."""
    return {
        "rows_before": len(df_before),
        "rows_after": len(df_after),
        "rows_removed": len(df_before) - len(df_after),
        "columns_before": len(df_before.columns),
        "columns_after": len(df_after.columns),
        "columns_removed": len(df_before.columns) - len(df_after.columns),
    }
