import logging

import pandas as pd


logger = logging.getLogger(__name__)


def validate_dataframe(df, required_columns, numeric_columns):
    """Validate the DataFrame and return valid data.

    required_columns: a list of column names that must exist.
    numeric_columns: a list of column names whose values should be numeric.
    """
    for column in required_columns:
        if column not in df.columns:
            logger.error(f"Required column missing: {column}")
            raise ValueError(f"Required column missing: {column}")

    rows_before = len(df)

    for column in numeric_columns:
        invalid_rows = []

        for index, value in df[column].items():
            if pd.notna(value):
                try:
                    float(value)
                except ValueError:
                    logger.warning(
                        f"Invalid numeric value in {column} at row {index}: "
                        f"{value}"
                    )
                    invalid_rows.append(index)

        df = df.drop(invalid_rows)

        if invalid_rows:
            logger.warning(
                f"Removed {len(invalid_rows)} rows with invalid numeric "
                f"values in {column}"
            )

        df[column] = pd.to_numeric(df[column])

    rows_removed = rows_before - len(df)
    logger.debug(
        f"Validation: {rows_before} -> {len(df)} rows "
        f"({rows_removed} removed)"
    )

    return df
