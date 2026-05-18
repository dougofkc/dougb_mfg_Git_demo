import snowflake.connector
import os

def get_snowflake_version():
    conn = snowflake.connector.connect(
        connection_name=os.getenv("SNOWFLAKE_CONNECTION_NAME") or "default"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT CURRENT_VERSION()")
    version = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return version

if __name__ == "__main__":
    print(f"Connected to Snowflake version: {get_snowflake_version()}")
