import snowflake.connector
import os
from datetime import datetime, timedelta

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

def get_manufacturing_kpis(conn, start_date=None, end_date=None):
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

    kpis = {
        "production_throughput": {
            "query": f"""
                SELECT line_id, SUM(units_produced) as throughput
                FROM manufacturing.production_log
                WHERE production_date BETWEEN '{start_date}' AND '{end_date}'
                GROUP BY line_id
                ORDER BY throughput DESC
            """,
            "label": "Production Throughput by Line"
        },
        "defect_rates": {
            "query": f"""
                SELECT shift, 
                       ROUND(SUM(defect_count)::FLOAT / NULLIF(SUM(units_produced), 0) * 100, 2) as defect_rate_pct
                FROM manufacturing.quality_metrics
                WHERE inspection_date BETWEEN '{start_date}' AND '{end_date}'
                GROUP BY shift
                ORDER BY shift
            """,
            "label": "Defect Rate (%) by Shift"
        },
        "equipment_uptime": {
            "query": f"""
                SELECT equipment_id,
                       ROUND(SUM(uptime_minutes)::FLOAT / SUM(scheduled_minutes) * 100, 2) as uptime_pct
                FROM manufacturing.equipment_status
                WHERE status_date BETWEEN '{start_date}' AND '{end_date}'
                GROUP BY equipment_id
                ORDER BY uptime_pct ASC
            """,
            "label": "Equipment Uptime (%)"
        }
    }

    results = {}
    cursor = conn.cursor()
    for key, kpi in kpis.items():
        try:
            cursor.execute(kpi["query"])
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            results[key] = {"label": kpi["label"], "columns": columns, "rows": rows}
        except Exception as e:
            results[key] = {"label": kpi["label"], "error": str(e)}
    cursor.close()
    return results

def print_kpi_table(kpi_result):
    if "error" in kpi_result:
        print(f"  Error: {kpi_result['error']}")
        return
    if not kpi_result["rows"]:
        print("  No data available")
        return
    col_widths = [max(len(str(col)), max(len(str(row[i])) for row in kpi_result["rows"]))
                  for i, col in enumerate(kpi_result["columns"])]
    header = " | ".join(col.ljust(col_widths[i]) for i, col in enumerate(kpi_result["columns"]))
    print(f"  {header}")
    print(f"  {'-' * len(header)}")
    for row in kpi_result["rows"]:
        line = " | ".join(str(val).ljust(col_widths[i]) for i, val in enumerate(row))
        print(f"  {line}")

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
    print()

    print(f"--- Manufacturing KPIs (last 7 days) ---")
    kpi_results = get_manufacturing_kpis(conn)
    for key, result in kpi_results.items():
        print(f"\n{result['label']}:")
        print_kpi_table(result)

    conn.close()
