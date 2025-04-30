import pandas as pd
from utils.db_connection import get_mysql_engine

def save_commits_to_silver(df):
    # Save to silver table
    engine = get_mysql_engine()
    df.to_sql('silver', con=engine, if_exists='replace', index=False)
    print(f"[Silver] Saved {len(df)} records to Silver layer.")


def transforma_data(df):
    print("Shape of df: ", df.shape)
    print("Total No of Null Values In df Before Transformation: ",df.isnull().sum().sum())
    # No. of Unique Value In Column
    print("No of Unique Values in DealerName Column: ", df["DealerName"].nunique())
    # Find Mode 
    mode_val = df["DealerName"].mode()[0]
    # Fill Null Value With Mode Value
    df["DealerName"] = df["DealerName"].fillna(mode_val)
    print("Total No of Null Values In df After Transformation: ",df.isnull().sum().sum())

    save_commits_to_silver(df)

def load_data_from_bronze():
    engine = get_mysql_engine()
    query = "select * from bronze"
    df = pd.read_sql(query, engine)
    transforma_data(df)



if __name__=="__main__":
    load_data_from_bronze()