import pandas as pd
import json
import re
import math

def to_snake_case(text):
    """
    Converts messy Excel headers into clean, predictable snake_case keys.
    Handles newlines, special characters, and random spacing.
    """
    if pd.isna(text) or not str(text).strip():
        return None
    
    text = str(text).strip()
    text = text.replace('\n', ' ').replace('-', ' ')
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    text = re.sub(r'[\s]+', '_', text).lower()
    
    return text

def _clean_value(val):
    """Helper to convert pandas NaNs and empty spaces to standard Python None."""
    if pd.isna(val) or str(val).strip() in ['', 'nan', 'None']:
        return None
    return str(val).strip()

def parse_scoreboard(file_path):
    """
    Ingests the Excel file, extracts metadata, and formats the weekly data.
    """
    # Read without headers to manually process the multi-row structure
    df = pd.read_excel(file_path, header=None, engine='openpyxl')
    
    metadata = {}
    col_idx_to_key = {}
    
    # Forward-fill row 0 (Categories) using a pure Python list to avoid Pandas dtype errors.
    # (Pandas will throw an error if we try to ffill a string into a column it inferred as float64)
    raw_categories = df.iloc[0].tolist()
    categories = []
    current_category = None
    
    for cat in raw_categories:
        if pd.notna(cat) and str(cat).strip() not in ['', 'nan', 'None']:
            current_category = cat
        categories.append(current_category)
    
    # --- STEP 1: PARSE HEADERS & METADATA ---
    for col_idx in range(len(df.columns)):
        metric_name = df.iloc[1, col_idx]
        
        # Skip purely empty spacer columns
        if pd.isna(metric_name) or not str(metric_name).strip():
            continue 
            
        # The first column contains Dates. Excel often leaves the header blank or uses a slash.
        if col_idx == 0 and (pd.isna(metric_name) or str(metric_name).strip() == '\\'):
            key = "date"
        else:
            key = to_snake_case(metric_name)
        
        # Deduplication safeguard
        original_key = key
        counter = 1
        while key in metadata or key in col_idx_to_key.values():
            key = f"{original_key}_{counter}"
            counter += 1
            
        col_idx_to_key[col_idx] = key
        
        # Build metadata (excluding the date column)
        if key != 'date':
            metadata[key] = {
                "original_name": str(metric_name).strip().replace('\n', ' '),
                "category": _clean_value(categories[col_idx]), # Fixed: using our safe Python list
                "focus": _clean_value(df.iloc[2, col_idx]),
                "source": _clean_value(df.iloc[3, col_idx]),
                "role": _clean_value(df.iloc[4, col_idx]),
                "target_or_formula": _clean_value(df.iloc[5, col_idx])
            }

    # --- STEP 2: PARSE TIME-SERIES DATA ---
    data_start_row = 6
    time_series_data = []
    
    for index, row in df.iloc[data_start_row:].iterrows():
        # Stop processing if the date column is completely empty (end of data)
        if pd.isna(row[0]):
            continue
            
        week_data = {}
        for col_idx, key in col_idx_to_key.items():
            val = row[col_idx]
            
            if key == 'date':
                # Safely format Pandas Timestamps to ISO strings
                if isinstance(val, pd.Timestamp):
                    week_data[key] = val.strftime('%Y-%m-%d')
                else:
                    week_data[key] = str(val).strip()
            else:
                # Convert numpy types to native Python types for clean JSON serialization
                if pd.isna(val):
                    week_data[key] = None
                elif isinstance(val, (int, float)):
                    # Handle python's strictness with NaN floats
                    week_data[key] = float(val) if not math.isnan(val) else None
                else:
                    week_data[key] = str(val).strip()
                    
        time_series_data.append(week_data)
        
    return {
        "metadata": metadata,
        "weekly_data": time_series_data
    }

if __name__ == "__main__":
    input_file = 'Scoreboard Test.xlsx'
    output_file = 'output.json'
    
    print(f"Reading {input_file}...")
    try:
        result = parse_scoreboard(input_file)
        
        # --- STEP 3: EXPORT JSON ---
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
            
        print(f"Success! Extracted {len(result['metadata'])} metrics.")
        print(f"Processed {len(result['weekly_data'])} weeks of data.")
        print(f"Output saved to -> {output_file}")
        
    except Exception as e:
        print(f"Error processing file: {e}")