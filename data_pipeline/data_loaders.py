from pathlib import Path

import json
import logging

import pandas as pd
import yaml


# Do not call logging.basicConfig() here.
# Use the logging configuration from Part 1.
logger = logging.getLogger(__name__)


def load_csv(filepath):
    """Load a CSV file into a DataFrame.
    filepath is a Path object.
    """
    data = pd.read_csv(filepath)
    logger.info(f"Loaded CSV file: {filepath} ({len(data)} rows)")
    return data


def load_json(filepath):
    """Load a JSON file into a Python object (dict or list).
    filepath is a Path object.
    """
    with open(filepath, "r") as file:
        data = json.load(file)

    logger.info(f"Loaded JSON file: {filepath}")
    return data


def load_yaml(filepath):
    """Load a YAML file into a Python object.
    filepath is a Path object.
    """
    with open(filepath, "r") as file:
        data = yaml.safe_load(file)

    logger.info(f"Loaded YAML file: {filepath}")
    return data


def load_data(filepath):
    """Load a file based on its extension.
    filepath is a string, such as 'fixtures/sample.csv'
    """
    path = Path(filepath)
    extension = path.suffix.lower()

    if extension == ".csv":
        return load_csv(path)
    elif extension == ".json":
        return load_json(path)
    elif extension == ".yaml":
        return load_yaml(path)
    else:
        logger.error(f"Unsupported file format: {extension}")
        raise ValueError(f"Unsupported file format: {extension}")
