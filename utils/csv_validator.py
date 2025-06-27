import pandas as pd
from datetime import datetime

REQUIRED_COLUMNS = ["employee_id", "name", "role", "doj", "location", "department"]

def validate_hr_csv(file_path: str):
    try:
        df = pd.read_csv(file_path)

        # Check column headers
        if list(df.columns) != REQUIRED_COLUMNS:
            raise ValueError(f"CSV headers must be: {REQUIRED_COLUMNS}")

        # Validate data types
        df['employee_id'] = df['employee_id'].astype(int)
        df['doj'] = pd.to_datetime(df['doj'], format="%Y-%m-%d")

        return df

    except Exception as e:
        raise ValueError(f"CSV validation failed: {str(e)}")
