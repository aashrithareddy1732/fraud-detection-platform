import csv
from io import StringIO


def read_csv_records(content: bytes) -> list[dict]:
    """Parse uploaded CSV bytes; schema validation belongs to the next pipeline stage."""
    return list(csv.DictReader(StringIO(content.decode("utf-8-sig"))))
