import snowflake.connector
import os
from datetime import datetime

def get_connection():
    return snowflake.connector.connect(
        connection_name=os.getenv("SNOWFLAKE_CONNECTION_NAME") or "default"
    )

def get_snowflake_version(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT CURRENT_VERSION()")
    version = cursor.fetchone()[0]
    cursor.close()
    return version

def get_session_info(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE()
    """)
    row = cursor.fetchone()
    cursor.close()
    return {"user": row[0], "role": row[1], "warehouse": row[2], "database": row[3]}

def list_warehouses(conn):
    cursor = conn.cursor()
    cursor.execute("SHOW WAREHOUSES")
    warehouses = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return warehouses

if __name__ == "__main__":
    conn = get_connection()
    print(f"--- Snowflake Connection Report ---")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Version:   {get_snowflake_version(conn)}")
    print()

    info = get_session_info(conn)
    print(f"User:      {info['user']}")
    print(f"Role:      {info['role']}")
    print(f"Warehouse: {info['warehouse']}")
    print(f"Database:  {info['database']}")
    print()

    warehouses = list_warehouses(conn)
    print(f"Available Warehouses ({len(warehouses)}):")
    for wh in warehouses:
        print(f"  - {wh}")

    conn.close()
