# fact_sales.py

import pandas as pd
from sqlalchemy import create_engine, text
from utils.db_connection import get_mysql_engine

def create_fact_sales():
    """
    Create fact_sales table by linking dimension keys and measures.
    """

    engine = get_mysql_engine()

    # Step 1: Read source data (bronze)
    source_query = "SELECT * FROM bronze;"
    source_df = pd.read_sql(source_query, engine)
    print(f"[Info] Read {len(source_df)} records from Bronze layer for fact_sales.")

    # Step 2: Read dimension tables
    dim_branch_df = pd.read_sql('SELECT Branch_ID, dim_branch_key FROM dim_branch;', engine)
    dim_dealer_df = pd.read_sql('SELECT Dealer_ID, dim_dealer_key FROM dim_dealer;', engine)
    dim_model_df  = pd.read_sql('SELECT Model_ID, dim_model_key FROM dim_model;', engine)
    dim_date_df   = pd.read_sql('SELECT Date_ID, dim_date_key FROM dim_date;', engine)

    # Step 3: Merge source data with dimension keys
    fact_df = source_df.merge(dim_branch_df, on='Branch_ID', how='left') \
                       .merge(dim_dealer_df, on='Dealer_ID', how='left') \
                       .merge(dim_model_df, on='Model_ID', how='left') \
                       .merge(dim_date_df, on='Date_ID', how='left')

    # Step 4: Select final columns
    fact_sales_df = fact_df[['dim_branch_key', 'dim_dealer_key', 'dim_model_key', 'dim_date_key',
                             'Revenue', 'Units_Sold', 'loaded_at']]

    # Step 5: Save fact_sales
    fact_sales_df.to_sql('fact_sales', con=engine, if_exists='replace', index=False)
    print(f"[Success] Created fact_sales table with {len(fact_sales_df)} records.")

if __name__ == "__main__":
    create_fact_sales()
