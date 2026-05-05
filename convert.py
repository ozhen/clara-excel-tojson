import pandas as pd
import json
import re
import math

def expand_and_clean_metric(text):
    """
    Expands domain-specific abbreviations for LLM readability and converts to snake_case.
    """
    text = str(text).lower().strip()
    
    # Translate symbols to semantic words before the regex strips them
    text = text.replace('%', ' percentage ')
    text = text.replace('#', ' count ')
    
    # Remove redundant prefixes (they will be nested in the JSON)
    text = re.sub(r'^(pt|rmt|chiro|pelvic health)\s+', '', text)
    
    # Expand medical/clinic abbreviations
    replacements = {
        r'\bax\b': 'assessments',
        r'\btx\b': 'treatments',
        r'\bpva\b': 'patient_visit_average',
        r'\bar\b': 'accounts_receivable',
        r'\bnbo\b': 'new_bookings_online',
        r'\bdnb\b': 'did_not_book',
        r'\bf/u\b': 'follow_up',
        r'\bmd\b': 'doctor',
        r'\bvv\b': 'virtual_visit',
        r'\brx\b': 'prescriptions',
        r'\btp\b': 'treatment_plan',
        r'\bahs\b': 'alberta_health_services',
        r'\bnar\b': 'new_assessment_revenue',
        r'\bnps\b': 'net_promoter_score',
        r'\bappts\b': 'appointments'
    }
    
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)

    # Convert to standard snake_case
    text = text.replace('\n', ' ').replace('-', ' ')
    text = re.sub(r'[^a-z0-9\s_]', '', text)
    text = re.sub(r'[\s_]+', '_', text).strip('_')
    
    # Remove tautological redundancies
    text = text.replace('patient_visit_average_4_wk_avg', 'patient_visit_average_4_wk')
    
    return text

def _clean_value(val):
    if pd.isna(val) or str(val).strip() in ['', 'nan', 'None']:
        return None
    return str(val).strip()

def parse_scoreboard(file_path):
    print(f"Reading {file_path}...")
    df = pd.read_excel(file_path, header=None, engine='openpyxl')
    
    metadata = {"clinic_wide_metrics": {}, "disciplines": {}}
    schema_map = {} 
    
    categories = [cat if pd.notna(cat) and str(cat).strip() not in ['', 'nan'] else None for cat in df.iloc[0].tolist()]
    
    # --- STEP 1: PARSE HEADERS & BUILD SEMANTIC ROUTING ---
    current_group = "clinic_wide_metrics"
    current_subgroup = None
    seen_paths = set()
    
    for col_idx in range(1, len(df.columns)):
        raw_name = df.iloc[1, col_idx]
        if pd.isna(raw_name) or not str(raw_name).strip():
            continue 
            
        raw_str = str(raw_name).strip().lower()
        
        if "pt total revenue" in raw_str:
            current_group, current_subgroup = "disciplines", "physiotherapy"
        elif "rmt total revenue" in raw_str:
            current_group, current_subgroup = "disciplines", "massage_therapy"
        elif "chiro" in raw_str and "total revenue" in raw_str:
            current_group, current_subgroup = "disciplines", "chiropractic"
        elif "pelvic health" in raw_str and "total revenue" in raw_str:
            current_group, current_subgroup = "disciplines", "pelvic_health"

        clean_key = expand_and_clean_metric(raw_name)
        
        schema_path = f"{current_group}.{current_subgroup}.{clean_key}"
        original_key = clean_key
        counter = 1
        while schema_path in seen_paths:
            clean_key = f"{original_key}_{counter}"
            counter += 1
            schema_path = f"{current_group}.{current_subgroup}.{clean_key}"
            
        seen_paths.add(schema_path)
        
        schema_map[col_idx] = {
            "group": current_group,
            "subgroup": current_subgroup,
            "key": clean_key
        }
        
        meta_obj = {
            "original_name": str(raw_name).strip().replace('\n', ' '),
            "category": _clean_value(categories[col_idx]),
            "target_or_formula": _clean_value(df.iloc[5, col_idx])
        }
        
        if current_subgroup:
            if current_subgroup not in metadata["disciplines"]:
                metadata["disciplines"][current_subgroup] = {}
            metadata["disciplines"][current_subgroup][clean_key] = meta_obj
        else:
            metadata["clinic_wide_metrics"][clean_key] = meta_obj

    # --- STEP 2: INITIALIZE COLUMNAR TIME-SERIES ARRAYS ---
    dates = []
    time_series = {"clinic_wide_metrics": {}, "disciplines": {}}
    
    # Pre-build the nested array structure based on our schema map
    for col_idx, schema in schema_map.items():
        if schema["subgroup"]:
            if schema["subgroup"] not in time_series["disciplines"]:
                time_series["disciplines"][schema["subgroup"]] = {}
            time_series["disciplines"][schema["subgroup"]][schema["key"]] = []
        else:
            time_series["clinic_wide_metrics"][schema["key"]] = []

    # --- STEP 3: POPULATE PARALLEL ARRAYS ---
    for index, row in df.iloc[6:].iterrows():
        raw_date = row[0]
        if pd.isna(raw_date):
            continue
            
        try:
            parsed_date = pd.to_datetime(raw_date)
            if pd.isna(parsed_date) or parsed_date.year < 2000: 
                continue
            date_str = parsed_date.strftime('%Y-%m-%d')
        except Exception:
            continue
            
        # Append to the master index
        dates.append(date_str)
        
        for col_idx, schema in schema_map.items():
            val = row[col_idx]
            parsed_val = None # Default to None to preserve parallel array length
            
            if not pd.isna(val):
                try:
                    f_val = float(val)
                    if not math.isnan(f_val):
                        parsed_val = int(f_val) if f_val.is_integer() else f_val
                except (ValueError, TypeError):
                    pass 

            # Append the value (or None) to the correct array
            if schema["subgroup"]:
                time_series["disciplines"][schema["subgroup"]][schema["key"]].append(parsed_val)
            else:
                time_series["clinic_wide_metrics"][schema["key"]].append(parsed_val)
                
    return {"metadata": metadata, "dates": dates, "time_series": time_series}

if __name__ == "__main__":
    input_file = 'Scoreboard Test.xlsx'
    output_file = 'output.json'
    try:
        result = parse_scoreboard(input_file)
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Success! Output saved to -> {output_file}")
    except Exception as e:
        print(f"Error: {e}")