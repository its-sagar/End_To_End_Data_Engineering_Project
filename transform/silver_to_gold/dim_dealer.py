import pandas as pd
from sqlalchemy import create_engine
from utils.db_connection import get_mysql_engine

def create_dim_dealer():
    """
    Incrementally create/update the Dim_Dealer table based on dealer-related data.
    """

    engine = get_mysql_engine()

    # Step 1: Read source data
    source_query = "SELECT Dealer_ID, DealerName as Dealer_Name FROM bronze;"
    source_df = pd.read_sql(source_query, engine)
    print(f"[Info] Read {len(source_df)} records from Bronze layer for dealer dimension.")

    # Step 2: Remove duplicates
    source_df = source_df.drop_duplicates(subset=['Dealer_ID']).reset_index(drop=True)

    # Step 3: Read existing dim_dealer table
    try:
        dim_dealer_df = pd.read_sql("SELECT * FROM dim_dealer;", engine)
        print(f"[Info] Found {len(dim_dealer_df)} existing records in Dim_Dealer.")
    except Exception:
        print("[Info] Dim_Dealer table does not exist. Will create a new one.")
        dim_dealer_df = pd.DataFrame(columns=['dim_dealer_key', 'Dealer_ID', 'Dealer_Name'])

    # Step 4: Identify new records
    existing_dealer_ids = dim_dealer_df['Dealer_ID'].tolist()
    new_records_df = source_df[~source_df['Dealer_ID'].isin(existing_dealer_ids)].copy()

    # Step 5: Generate surrogate keys for new records
    if not new_records_df.empty:
        start_key = 1 if dim_dealer_df.empty else dim_dealer_df['dim_dealer_key'].max() + 1
        new_records_df.insert(0, 'dim_dealer_key', range(start_key, start_key + len(new_records_df)))

    # Step 6: Identify updated records (Dealer_ID exists but Dealer_Name changed)
    updated_records_df = pd.merge(
        source_df, dim_dealer_df[['Dealer_ID', 'Dealer_Name']],
        on='Dealer_ID', how='inner', suffixes=('_new', '_old')
    )
    updated_records_df = updated_records_df[updated_records_df['Dealer_Name_new'] != updated_records_df['Dealer_Name_old']]
    updated_ids = updated_records_df['Dealer_ID'].tolist()

    if updated_ids:
        print(f"[Info] Found {len(updated_ids)} updated dealer records.")
        for did in updated_ids:
            new_name = source_df.loc[source_df['Dealer_ID'] == did, 'Dealer_Name'].values[0]
            dim_dealer_df.loc[dim_dealer_df['Dealer_ID'] == did, 'Dealer_Name'] = new_name

    # Step 7: Concatenate new records
    if not new_records_df.empty:
        dim_dealer_df = pd.concat([dim_dealer_df, new_records_df], ignore_index=True)

    # Step 8: Save the final table
    dim_dealer_df.to_sql('dim_dealer', con=engine, if_exists='replace', index=False)
    print(f"[Success] dim_dealer table updated with {len(dim_dealer_df)} total records.")

if __name__ == "__main__":
    create_dim_dealer()
