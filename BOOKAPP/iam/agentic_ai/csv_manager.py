import pandas as pd

def read_csv(file_path):
    return pd.read_csv(file_path)

def write_csv(file_path, data):
    df = pd.DataFrame(data)
    df.to_csv(file_path,index=False)


import csv
from typing import List, Dict, Any

def save_rows_to_csv(rows: List[Dict[str, Any]], file_path: str):
    """
    Save list of dicts to CSV file
    """
    if not rows:
        return None

    keys = rows[0].keys()
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
    return file_path
