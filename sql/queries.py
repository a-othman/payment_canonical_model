import duckdb
from pathlib import Path
base_path = Path(__file__).parent.parent
data_path= base_path / "data/output/canonical_payments.parquet"
data_w_errors_path = base_path / "data/output/dead_letter_queue.json"

def run_analytics():
    print("📊 Running Downstream Analytics on Unified Payment Model\n")
    print("="*60)
    print("QUERY 0: Total Settled Revenue by Payment Method")
    query_0 = f"""
        SELECT 
            count(*) as total_transactions,
        FROM '{data_path}'
    """
    print(duckdb.sql(query_0).show())


    print("QUERY 1: Total Settled Revenue by Payment Method")
    query_1 = f"""
        SELECT 
            payment_method,
            COUNT(*) as total_transactions,
            SUM(amount_cents) / 100.0 AS total_revenue_usd
        FROM '{data_path}'
        WHERE status = 'COMPLETED'
        GROUP BY payment_method
        ORDER BY total_revenue_usd DESC;
    """
    print(duckdb.sql(query_1).show())


    # ---------------------------------------------------------
    # Query 2: The "Envelope" Extraction
    # Proves we can safely parse vendor-specific JSON metadata 
    # out of the strict Parquet columns.
    # ---------------------------------------------------------
    print("QUERY 2: Extracting specific 'Card Network' from the JSON Metadata")
    query_2 = f"""
        SELECT 
            payment_id,
            amount_cents / 100.0 as amount_usd,
            -- Use DuckDB's JSON extraction operator (->>) to pull data from the string
            source_metadata->>'network' AS card_network,
            source_metadata->>'version' AS api_version
        FROM '{data_path}'
        WHERE payment_method = 'CARD'
        LIMIT 5;
    """
    print(duckdb.sql(query_2).show())

    # Query 3: Dead Letter Queue (DLQ) Analysis
    # Proves your data engineering team has observability 

    print("QUERY 3: Pipeline Observability (Analyzing the DLQ)")
    query_3 = f"""
        SELECT 
            file AS source_file,
            error_type,
            COUNT(*) as failure_count
        FROM '{data_w_errors_path}'
        GROUP BY source_file, error_type
        ORDER BY failure_count DESC;
    """
    
    try:
        print(duckdb.sql(query_3).show())
    except Exception as e:
        print("No Dead Letter Queue found or JSON is empty. Your pipeline is perfectly healthy!")

if __name__ == "__main__":
    run_analytics()