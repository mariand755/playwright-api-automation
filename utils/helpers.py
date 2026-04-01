import json
from pathlib import Path


def load_json(file_path):
    path = Path(file_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / path

    with open(path) as f:
        return json.load(f)


def get_schema(schema_name):
    schema_path = Path(__file__).resolve().parents[1] / "data" / "schemas" / schema_name
    return load_json(schema_path)