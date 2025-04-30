# dim_date.py

import pandas as pd
from sqlalchemy import create_engine, text
from utils.db_connection import get_mysql_engine

def create_dim_date():
    """
    Incrementally create/update the Dim_Date table based on bronze data.
    """

    engine = get_mysql_engine()

    # Step 1: Read source data
    source_query = "SELECT Date_ID, Day, Month, Year FROM bronze;"
    source_df = pd.read_sql(source_query, engine)
    print(f"[Info] Read {len(source_df)} records from Bronze layer for date dimension.")

    # Step 2: Drop duplicates
    source_df = source_df.drop_duplicates(subset=['Date_ID']).reset_index(drop=True)

    # Step 3: Read existing Dim_Date table if exists
    try:
        dim_date_df = pd.read_sql('SELECT * FROM dim_date;', engine)
        print(f"[Info] Found {len(dim_date_df)} existing records in Dim_Date table.")
    except Exception:
        print("[Info] Dim_Date table does not exist. Will create a new one.")
        dim_date_df = pd.DataFrame(columns=['dim_date_key', 'Date_ID', 'Day', 'Month', 'Year'])

    # Step 4: Find new records
    existing_date_ids = dim_date_df['Date_ID'].tolist()
    new_records_df = source_df[~source_df['Date_ID'].isin(existing_date_ids)].copy()

    if new_records_df.empty:
        print("[Info] No new dates to add. Dimension table is up-to-date.")
        return

    # Step 5: Generate surrogate keys
    if dim_date_df.empty:
        start_key = 1
    else:
        start_key = dim_date_df['dim_date_key'].max() + 1

    new_records_df.insert(0, 'dim_date_key', range(start_key, start_key + len(new_records_df)))

    # Step 6: Concatenate
    final_dim_date_df = pd.concat([dim_date_df, new_records_df], ignore_index=True)

    # Step 7: Save
    final_dim_date_df.to_sql('dim_date', con=engine, if_exists='replace', index=False)
    print(f"[Success] Updated dim_date table with {len(final_dim_date_df)} total records.")

if __name__ == "__main__":
    create_dim_date()
