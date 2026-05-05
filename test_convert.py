import pytest
import pandas as pd
import math
from convert import expand_and_clean_metric, _clean_value, parse_scoreboard

def test_expand_and_clean_metric():
    """Test acronym expansion and symbol translation logic."""
    # Test symbols
    assert expand_and_clean_metric("Cancelled Ax %") == "cancelled_assessments_percentage"
    assert expand_and_clean_metric("# of Rx") == "count_of_prescriptions"
    # Test prefixes stripped (since they will be nested)
    assert expand_and_clean_metric("PT Total Revenue") == "total_revenue"
    assert expand_and_clean_metric("RMT Ax") == "assessments"
    # Test acronym expansion
    assert expand_and_clean_metric("NBO") == "new_bookings_online"
    # Test tautology fix
    assert expand_and_clean_metric("PVA (4 wk avg)") == "patient_visit_average_4_wk"

def test_clean_value():
    """Test pandas NaN and empty string cleanup."""
    assert _clean_value(" Target = 75% ") == "Target = 75%"
    assert _clean_value(float('nan')) is None
    assert _clean_value(None) is None
    assert _clean_value("nan") is None
    assert _clean_value("   ") is None

def test_parse_scoreboard_columnar_integration(tmp_path):
    """
    Integration test: Creates a mock Excel file and verifies the 
    Columnar / Object-of-Arrays architecture.
    """
    # Create a mock dataframe mimicking the exact 6-row header structure
    # Including a "PT" prefix to trigger the discipline routing
    data = [
        ["PHONE PERFORMANCE", "PHONE PERFORMANCE", "PT PERFORMANCE"], # Row 0: Category
        ["\\", "Total Revenue", "PT Total Revenue"],           # Row 1: Metric
        [None, "Financial", "Financial"],                      # Row 2: Focus
        [None, "EMR", "EMR"],                                  # Row 3: Source
        [None, "J", "BETH"],                                   # Row 4: Role
        [None, "Target = 10k", "Target = 5k"],                 # Row 5: Target
        ["2026-02-16", 40454.28, 15000.50],                    # Row 6: Data Week 1
        ["2026-02-09", 42360.64, 16200.00],                    # Row 7: Data Week 2
    ]
    df = pd.DataFrame(data)
    
    # Save to a temporary excel file
    test_file = tmp_path / "mock_scoreboard.xlsx"
    df.to_excel(test_file, index=False, header=False)
    
    # Run the main parser function
    result = parse_scoreboard(test_file)
    
    # 1. Assert Top-Level Architecture
    assert "metadata" in result
    assert "dates" in result
    assert "time_series" in result
    
    # 2. Assert Dates Array
    assert len(result["dates"]) == 2
    assert result["dates"] == ["2026-02-16", "2026-02-09"]
    
    # 3. Assert Columnar Nesting
    ts = result["time_series"]
    assert "clinic_wide_metrics" in ts
    assert "disciplines" in ts
    assert "physiotherapy" in ts["disciplines"]
    
    # 4. Assert Parallel Arrays (Data values match dates index)
    global_rev = ts["clinic_wide_metrics"]["total_revenue"]
    assert len(global_rev) == 2
    assert global_rev[0] == 40454.28
    
    pt_rev = ts["disciplines"]["physiotherapy"]["total_revenue"]
    assert len(pt_rev) == 2
    assert pt_rev[1] == 16200.00