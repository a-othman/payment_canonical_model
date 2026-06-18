import os
import pandas as pd
from pydantic import ValidationError
import json 
from pathlib import Path
from schema.canonical_model import CanonicalPayment
from adapters.transfers import *
from adapters.cards import *
from adapters.bill_payments import *
from utils.generators import generate_data

base_path = Path(__file__).parent.parent / "data"
INPUT_DIR = base_path / "raw"
OUTPUT_DIR = base_path / "output"



def route_and_map(filename: str, raw_row: dict) -> dict:
    """The Version Router: Directs raw data to the correct adapter."""
    if "card_v1" in filename: return map_card_v1(raw_row)
    elif "transfer_v1" in filename: return map_transfer_v1(raw_row)
    elif "bill_v1" in filename: return map_bill_v1(raw_row)
    elif "card_v2" in filename: return map_card_v2(raw_row)
    elif "transfer_v2" in filename: return map_transfer_v2(raw_row)
    elif "bill_v2" in filename: return map_bill_v2(raw_row)
    else: raise ValueError(f"Unknown source format for file: {filename}")

def run_pipeline(generate_data_flag=True):
    print("🚀 Starting Payment Ingestion Pipeline...")
    if generate_data_flag:
        generate_data()  # Generate synthetic data for testing
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    valid_records = []
    dead_letter_queue = []
    for filename in os.listdir(INPUT_DIR):
        if not filename.endswith(".csv"):
            continue
            
        filepath = os.path.join(INPUT_DIR, filename)
        print(f"Processing: {filename}...")      
        # Read CSV and handle NaNs
        df = pd.read_csv(filepath)
        df = df.where(pd.notnull(df), None)
        raw_records = df.to_dict(orient="records")        
        for idx, row in enumerate(raw_records):
            try:
                # 1. Map to Canonical Dictionary
                canonical_dict = route_and_map(filename, row)
                validated_record = CanonicalPayment(**canonical_dict) # 2. Pydantic Validation (The Firewall)
                valid_records.append(validated_record.model_dump()) # 3. Save Validated Record (converting to standard dictionary)
                
            except ValidationError as e:
                # Catch Pydantic Schema Violations (e.g., negative amounts, bad enums)
                dead_letter_queue.append({
                    "file": filename,
                    "row_index": idx,
                    "error_type": "SchemaValidationError",
                    "error_details": str(e.json()),
                    "raw_data": row
                })
            except Exception as e:
                # Catch raw mapping crashes (e.g., trying to float("N/A") in the adapter)
                dead_letter_queue.append({
                    "file": filename,
                    "row_index": idx,
                    "error_type": "AdapterMappingError",
                    "error_details": str(e),
                    "raw_data": row
                })

    if valid_records:
        df_valid = pd.DataFrame(valid_records)
        df_valid['source_metadata'] = df_valid['source_metadata'].apply(json.dumps) #serializing nested dict for parquet
        
        parquet_path = os.path.join(OUTPUT_DIR, "canonical_payments.parquet")
        df_valid.to_parquet(parquet_path, index=False)

        csv_path = os.path.join(OUTPUT_DIR, "canonical_payments.csv")
        df_valid.to_csv(csv_path, index=False)
        print(f"\n✅ SUCCESS: Saved {len(valid_records)} canonical records to {parquet_path}")

    if dead_letter_queue:
        dlq_path = os.path.join(OUTPUT_DIR, "dead_letter_queue.json")
        with open(dlq_path, "w") as f:
            json.dump(dead_letter_queue, f, indent=4)
        print(f"⚠️  CAUGHT: Saved {len(dead_letter_queue)} bad records to {dlq_path}")

    return valid_records, dead_letter_queue

if __name__ == "__main__":
    run_pipeline()