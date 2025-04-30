import pandas as pd
from sqlalchemy import create_engine
from utils.db_connection import get_mysql_engine

def create_dim_model():
    """
    Incrementally create/update the Dim_Model table based on model-related data.
    """

    engine = get_mysql_engine()

    # Step 1: Read source data
    source_query = "SELECT Model_ID, Product_Name as Model_Category FROM bronze;"
    source_df = pd.read_sql(source_query, engine)
    print(f"[Info] Read {len(source_df)} records from Bronze layer for model dimension.")

    # Step 2: Remove duplicates
    source_df = source_df.drop_duplicates(subset=['Model_ID']).reset_index(drop=True)

    # Step 3: Read existing dim_model table
    try:
        dim_model_df = pd.read_sql("SELECT * FROM dim_model;", engine)
        print(f"[Info] Found {len(dim_model_df)} existing records in Dim_Model.")
    except Exception as e:
        print("[Info] Dim_Model table does not exist. Will create a new one.")
        dim_model_df = pd.DataFrame(columns=['dim_model_key', 'Model_ID', 'Model_Category'])

    # Step 4: Identify new records
    existing_model_ids = dim_model_df['Model_ID'].tolist()
    new_records_df = source_df[~source_df['Model_ID'].isin(existing_model_ids)].copy()

    # Step 5: Generate surrogate keys for new records
    if not new_records_df.empty:
        start_key = 1 if dim_model_df.empty else dim_model_df['dim_model_key'].max() + 1
        new_records_df.insert(0, 'dim_model_key', range(start_key, start_key + len(new_records_df)))

    # Step 6: Identify updated records (Model_ID exists but Model_Category changed)
    updated_records_df = pd.merge(
        source_df, dim_model_df[['Model_ID', 'Model_Category']],
        on='Model_ID', how='inner', suffixes=('_new', '_old')
    )
    updated_records_df = updated_records_df[updated_records_df['Model_Category_new'] != updated_records_df['Model_Category_old']]
    updated_ids = updated_records_df['Model_ID'].tolist()

    if updated_ids:
        print(f"[Info] Found {len(updated_ids)} updated model records.")
        for mid in updated_ids:
            new_cat = source_df.loc[source_df['Model_ID'] == mid, 'Model_Category'].values[0]
            dim_model_df.loc[dim_model_df['Model_ID'] == mid, 'Model_Category'] = new_cat

    # Step 7: Concatenate new records
    if not new_records_df.empty:
        dim_model_df = pd.concat([dim_model_df, new_records_df], ignore_index=True)

    # Step 8: Save the final table
    dim_model_df.to_sql('dim_model', con=engine, if_exists='replace', index=False)
    print(f"[Success] dim_model table updated with {len(dim_model_df)} total records.")

if __name__ == "__main__":
    create_dim_model()

