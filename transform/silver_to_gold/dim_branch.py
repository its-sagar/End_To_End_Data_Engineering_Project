import pandas as pd
from sqlalchemy import create_engine
from utils.db_connection import get_mysql_engine


def create_dim_branch():
    """
    Incrementally create/update the Dim_Branch table based on branch-related data.
    """

    engine = get_mysql_engine()

    # Step 1: Read source data
    source_query = "SELECT Branch_ID, BranchName as Branch_Name FROM bronze;"
    source_df = pd.read_sql(source_query, engine)
    print(f"[Info] Read {len(source_df)} records from Bronze layer for branch dimension.")

    # Step 2: Remove duplicates
    source_df = source_df.drop_duplicates(subset=['Branch_ID']).reset_index(drop=True)

    # Step 3: Read existing dim_branch table
    try:
        dim_branch_df = pd.read_sql("SELECT * FROM dim_branch;", engine)
        print(f"[Info] Found {len(dim_branch_df)} existing records in Dim_Branch.")
    except Exception as e:
        print("[Info] Dim_Branch table does not exist. Will create a new one.")
        dim_branch_df = pd.DataFrame(columns=['dim_branch_key', 'Branch_ID', 'Branch_Name'])

    # Step 4: Identify new records
    existing_branch_ids = dim_branch_df['Branch_ID'].tolist()
    new_records_df = source_df[~source_df['Branch_ID'].isin(existing_branch_ids)].copy()

    # Step 5: Generate surrogate keys for new records
    if not new_records_df.empty:
        start_key = 1 if dim_branch_df.empty else dim_branch_df['dim_branch_key'].max() + 1
        new_records_df.insert(0, 'dim_branch_key', range(start_key, start_key + len(new_records_df)))

    # Step 6: Identify updated records (Branch_ID exists but Branch_Name changed)
    updated_records_df = pd.merge(
        source_df, dim_branch_df[['Branch_ID', 'Branch_Name']],
        on='Branch_ID', how='inner', suffixes=('_new', '_old')
    )
    updated_records_df = updated_records_df[updated_records_df['Branch_Name_new'] != updated_records_df['Branch_Name_old']]
    updated_ids = updated_records_df['Branch_ID'].tolist()

    if updated_ids:
        print(f"[Info] Found {len(updated_ids)} updated branch records.")
        for bid in updated_ids:
            new_name = source_df.loc[source_df['Branch_ID'] == bid, 'Branch_Name'].values[0]
            dim_branch_df.loc[dim_branch_df['Branch_ID'] == bid, 'Branch_Name'] = new_name

    # Step 7: Concatenate new records
    if not new_records_df.empty:
        dim_branch_df = pd.concat([dim_branch_df, new_records_df], ignore_index=True)

    # Step 8: Save the final table
    dim_branch_df.to_sql('dim_branch', con=engine, if_exists='replace', index=False)
    print(f"[Success] dim_branch table updated with {len(dim_branch_df)} total records.")

if __name__ == "__main__":
    create_dim_branch()
