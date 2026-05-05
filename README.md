# clara-excel-tojson

Clara Take-Home: Excel to JSON Data Pipeline

Overview

This script ingests a messy clinic scoreboard (Excel) and transforms it into a production-ready JSON payload specifically optimized for LLMs and AI Agents.

How to Run It

Install dependencies: pip install -r requirements.txt

Ensure Scoreboard Test.xlsx is in the root directory.

Execute the pipeline: python convert.py

The result will be written to output.json.

Architecture & JSON Shape

I chose a Decoupled, Nested, and Sparse architecture.

Why?

Decoupled: Static targets/formulas are separated into a metadata dictionary at the top. This keeps the weekly_data array light and purely numerical.

Nested: Flattening the Excel headers created hallucination risks (e.g., pva_1 vs pva_2). The JSON uses semantic nesting to group metrics explicitly by discipline (disciplines -> physiotherapy -> patient_visit_average).

Sparse: Explicit null values waste massive amounts of LLM context window tokens. The parser strips nulls; if a key isn't present for a given week, the agent assumes 0 or null.

Snippet:

{
  "date": "2026-02-16",
  "clinic_wide_metrics": {
    "total_revenue_all_services": 40454.28
  },
  "disciplines": {
    "physiotherapy": {
      "assessments": 10,
      "patient_visit_average": 6.06
    }
  }
}


Handling the Messy Bits (Trade-offs)

Merged Cells & Flattened Context: Pandas naturally destroys context under merged cells (like PT vs RMT sections). I implemented a stateful column router that scans left-to-right, detects discipline shifts (e.g., encountering "PT Total Revenue"), and dynamically nests subsequent duplicate metrics into the correct discipline bucket.

Extreme Abbreviations: "AX", "TX", and "NBO" save space in Excel but severely degrade LLM reasoning. I added a regex-based expansion mapping during parsing (ax -> assessments, nbo -> new_bookings_online) to maximize semantic clarity for the AI.

Dirty Data & Strict Typing: The raw file contains data artifacts (e.g., dates listed as "6", or revenue containing backticks `). To ensure an AI Agent wouldn't crash if using a Code Interpreter to sum columns, I implemented strict pd.to_numeric casting. Any string artifacts evaluate to NaN and are dropped from the sparse payload.

With Another Two Hours...

Pydantic Validation: I would implement explicit Pydantic models for the JSON output to guarantee absolute schema integrity before writing to disk.

Dynamic CLI: I would wrap the execution in argparse to allow developers to pass dynamic input/output paths via command line arguments.

Unit Tests: I would expand pytest coverage to explicitly test the stateful grouping logic and abbreviation expansion map.