import requests
import datetime
import pandas as pd
import base64
import sqlalchemy
from io import StringIO

from utils.db_connection import get_mysql_engine
from config.config import GITHUB_API_URL, GITHUB_OWNER, GITHUB_REPO, GITHUB_TOKEN, GITHUB_CONTENTTS_PATH


def get_last_fetched_timestamp():
    """
    Fetches the last fetched timestamp from the metadata table
    This helps in incremental loading.
    """
    engine = get_mysql_engine()
    query = "SELECT last_run_timestamp FROM metadata WHERE process_name = 'github_fetch';"
    result = pd.read_sql(query, engine, parse_dates=['last_run_timestamp'])  # ✅ parse dates directly

    if result.empty:
        # Default to 30 days ago if no previous fetch
        return datetime.datetime.now() - datetime.timedelta(days=30)
    else:
        return result.iloc[0]['last_run_timestamp']


def fetch_new_commits(since_timestamp):
    """
    Fetch commits from GitHub API since the provided timestamp.
    """
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    url = GITHUB_API_URL.format(owner=GITHUB_OWNER, repo=GITHUB_REPO, path=GITHUB_CONTENTTS_PATH)

    params = {'since': since_timestamp.isoformat()}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()['content']
    else:
        raise Exception(f"Failed to fetch commits: {response.status_code} - {response.text}")


def save_commits_to_bronze(commits_data):
    """
    Save the new commits data into the Bronze layer (raw data in MySQL).
    """
    engine = get_mysql_engine()

    # Decode base64 GitHub content
    commits_df = pd.read_csv(StringIO(commits_data))

    # Add a load timestamp
    commits_df['loaded_at'] = datetime.datetime.now()

    # print("[Bronze] Data to be inserted:\n", commits_df.head())

    # Save to Bronze table
    commits_df.to_sql('bronze', con=engine, if_exists='replace', index=False)
    print(f"[Bronze] Saved {len(commits_df)} records to Bronze layer.")


def update_last_fetched_timestamp():
    """
    Update the timestamp in the metadata table after a successful fetch.
    """
    engine = get_mysql_engine()
    current_time = datetime.datetime.now()

    query = """
    INSERT INTO metadata (process_name, last_run_timestamp)
    VALUES (:process_name, :timestamp)
    ON DUPLICATE KEY UPDATE last_run_timestamp = :timestamp;
    """

    with engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(query),
            {"process_name": "github_fetch", "timestamp": current_time}
        )

    print(f"[Metadata] Updated last fetch timestamp to {current_time}.")


def extract_github_data():
    """
    Main function to extract GitHub data.
    """
    try:
        last_timestamp = get_last_fetched_timestamp()

        commits_data = fetch_new_commits(last_timestamp)
        if commits_data:
            decoded_content = base64.b64decode(commits_data).decode('utf-8')
            save_commits_to_bronze(decoded_content)
            update_last_fetched_timestamp()
        else:
            print("[Extractor] No new commits found.")

    except Exception as e:
        print(f"[Extractor] Error during extraction: {str(e)}")


if __name__ == "__main__":
    extract_github_data()
