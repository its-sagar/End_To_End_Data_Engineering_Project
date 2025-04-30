import pandas as pd
from utils.db_connection import get_mysql_engine
from sqlalchemy import inspect


def check_table_exist(engine, table_name):
    inspector = inspect(engine)
    print(inspector.get_table_names)
    return table_name in inspector.get_table_names()

def load_sink_data():
    engine = get_mysql_engine()
    table_name = "dim_model"
    if check_table_exist(engine=engine, table_name=table_name):
        quary = "select dim_model_key, Model_ID, Product_Category as Model_Category from dim_model"
        df_sink = pd.read_sql(quary, engine)
    else:
        quary = '''
                    select 1 as dim_model_key, Model_ID, Product_Name as Model_Category 
                    from silver
                    where 1 = 0
                '''
        df_sink = pd.read_sql(quary, engine)
    print(df_sink)

def load_data_from_silver():
    engine = get_mysql_engine()
    query = "select distinct Model_ID, Product_Name as Model_Category from silver"
    df_src = pd.read_sql(query, engine)
    print(df_src)
    load_sink_data()

if __name__=="__main__":
    load_data_from_silver()