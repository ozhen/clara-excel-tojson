Clara Take-Home: Excel to JSON Data Pipeline

Overview

This script ingests a messy clinic scoreboard (Excel) and transforms it into a production-ready JSON payload. Rather than just creating a technically lossless data dump, this pipeline is specifically engineered and optimized for LLM and AI Agent consumption via Code Interpreters.

How to Run It

Install dependencies: pip install -r requirements.txt

Ensure Scoreboard Test.xlsx is in the root directory.

Execute the pipeline: python convert.py

The result will be written to output.json.

AI-Optimized Architecture & JSON Shape

I chose a Decoupled, Nested, and Columnar architecture.

Decoupled: Static targets/formulas are separated into a metadata dictionary. This keeps the data payload strictly numerical and token-efficient.

Nested (Symmetric Naming): Flattening Excel headers creates hallucination risks. Metrics are semantically nested by discipline (disciplines -> physiotherapy -> total_revenue), allowing AI Agents to use predictable, symmetric keys.

Columnar Time-Series (Zero JSON Tax): Rather than a row-based array of objects (which repeats string keys infinitely and destroys LLM context limits at scale), the data is pivoted into a Columnar format. A master dates array serves as the parallel index for the time_series object of arrays, natively supporting pandas.DataFrame instantiation by Code Interpreting agents.

Example Snippet:

{
  "metadata": {
    "total_revenue": { "description": "...", "format": "currency" }
  },
  "dates": ["2026-02-16", "2026-02-09", "2026-02-02"],
  "time_series": {
    "clinic_wide_metrics": {
      "total_revenue_all_services": [40454.28, 42360.64, 39000.00]
    },
    "disciplines": {
      "physiotherapy": {
        "assessments": [10, 8, 12],
        "patient_visit_average_4_wk": [6.06, 5.90, 6.10]
      }
    }
  }
}


Handling the Messy Bits (Data Cleaning)

To ensure Agentic tools don't crash or hallucinate, I implemented the following standardizations:

Symbol Collisions: Translated # to count and % to percentage before generating keys to prevent Pandas _1 suffix collisions on identical base names.

Extreme Abbreviations: Added a regex-based expansion map (ax -> assessments, nbo -> new_bookings_online) to maximize semantic context for the AI.

Dirty Data & Strict Typing: Implemented strict pd.to_numeric casting. String artifacts (e.g., dates listed as "6", or revenue containing backticks) evaluate to NaN and are passed as null to maintain array index symmetry.

With Another Two Hours...

Pydantic Validation: I would implement explicit Pydantic models for the JSON output to guarantee absolute schema integrity before writing to disk.

Agentic Tool Integration: I would write a suite of Python tools alongside this JSON that allow an AI Agent to load this columnar data directly into a Pandas DataFrame for complex statistical queries.

Unit Tests: I would expand pytest coverage to explicitly test the stateful grouping logic and columnar pivot operations.

Appendix: AI Tooling Workflow

To ensure this JSON schema was truly optimized for Clara's AI-driven use cases, I utilized an LLM as a Senior Staff Engineering reviewer to pressure-test the data architecture prior to submission.

"Act as a Senior Staff Software Engineer specializing in LLMs and AI Agents. I am building a data pipeline for a clinic dashboard. My pipeline extracts messy Excel data and outputs it into this JSON payload. Our AI agents will need to read this JSON to generate business insights. Review the key names, structure, and data types in this JSON. Are they semantically clear for an LLM to parse? Point out any confusing structures, potential token-wasting, or areas where the LLM might hallucinate due to poor naming."

Result: Identified hallucination risks from Pandas suffixes and abbreviation ambiguity, leading to the nested and expanded architecture.

"I want to create a Python tool/function that an AI Agent can call to answer user questions like: 'What was our total Chiro revenue compared to PT revenue last week?' Based strictly on the JSON schema provided, write the Python function the agent would use to calculate this. In your analysis, tell me if my JSON structure makes this operation easy or unnecessarily difficult for the agent."

Result: Confirmed that symmetric nesting allows robust dictionary lookups without fragile string-matching.

"Right now, this JSON contains just a few weeks of data. In production, this array will contain 104 weeks (2 years) of data, with over 100 keys per week. Evaluate this payload size against modern LLM context windows. Would you recommend keeping this as a flat JSON array of weekly objects, or should I restructure/pivot it before feeding it to the prompt? Give me a concrete architectural recommendation."

Result: Highlighted the "JSON Tax" of repeating keys in a row-based array over 104 weeks. Advised a full pivot to a Columnar (Object of Arrays) structure indexed by a parallel dates array to drastically reduce token bloat and optimize for Pandas DataFrame injection.