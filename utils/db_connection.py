from sqlalchemy import create_engine
from config.config import DB_USER, DB_PASSWORD, DB_HOST, DB_NAME
import pandas as pd

from urllib.parse import quote_plus

DB_PASSWORD = quote_plus(DB_PASSWORD)

def get_mysql_engine():
    connection_string = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    return create_engine(connection_string)
