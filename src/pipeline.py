import os
import pandas as pd

from adapters.transfers import *
from adapters.cards import *
from adapters.bill_payments import *



INPUT_DIR = "/Users/ahmedothman/Desktop/mal/data/raw"

def route_and_map(filename: str, raw_row: dict) -> dict:
    """The Version Router: Directs raw data to the correct adapter based on filename."""
    if "card_v1" in filename:
        return map_card_v1(raw_row)
    elif "transfer_v1" in filename:
        return map_transfer_v1(raw_row)
    elif "bill_v1" in filename:
        return map_bill_v1(raw_row)
    elif "card_v2" in filename:
        return map_card_v2(raw_row)
    elif "transfer_v2" in filename:
        return map_transfer_v2(raw_row)
    elif "bill_v2" in filename:
        return map_bill_v2(raw_row)
    else:
        raise ValueError(f"Unknown source format for file: {filename}")

def run_pipeline():
    print("🚀 Starting Payment Ingestion Pipeline...")
    
    # These lists will be used heavily in Phase 3
    valid_records = []
    dead_letter_queue = []

    for filename in os.listdir(INPUT_DIR):
        if not filename.endswith(".csv"):
            continue
            
        filepath = os.path.join(INPUT_DIR, filename)
        print(f"Processing: {filename}")
        
        # Read CSV using pandas (converts NaNs to None for easier mapping)
        df = pd.read_csv(filepath)
        df= df.where(pd.notnull(df), None)
        raw_records = df.to_dict(orient="records")
        
        for idx, row in enumerate(raw_records):
            try:
                # 1. Map to Canonical Dictionary
                canonical_dict = route_and_map(filename, row)
                
                # [PLACEHOLDER] 2. Pydantic Validation will go here in Phase 3!
                
                valid_records.append(canonical_dict)
                
            except Exception as e:
                # Catch mapping errors (e.g., trying to float() a string like "N/A")
                dead_letter_queue.append({
                    "file": filename,
                    "row_index": idx,
                    "raw_data": row,
                    "error": str(e)
                })

    print(f"\n✅ Mapping Complete: {len(valid_records)} processed successfully.")
    print(f"⚠️ Errors Caught: {len(dead_letter_queue)}")

if __name__ == "__main__":
    run_pipeline()