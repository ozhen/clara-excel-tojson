Clara Take-Home: Excel to JSON Data Pipeline

Overview

This script ingests a messy clinic scoreboard (Excel) and transforms it into a production-ready JSON payload. Rather than just creating a technically lossless data dump, this pipeline is specifically engineered and optimized for LLM and AI Agent consumption via Code Interpreters.

How to Run It

Install dependencies: pip install -r requirements.txt

Ensure Scoreboard Test.xlsx is in the root directory.

Execute the pipeline: python convert.py

The result will be written to output.json.

AI-Optimized Architecture & JSON Shape

I chose a Decoupled, Nested, and Sparse architecture.

Decoupled: Static targets/formulas are separated into a metadata dictionary. This keeps the weekly_data array lightweight, strictly numerical, and token-efficient.

Nested (Symmetric Naming): Flattening the Excel headers created hallucination risks (e.g., pva_1 vs pva_2). By using a stateful router to nest metrics by discipline (disciplines -> physiotherapy -> total_revenue), AI Agents can write predictable, looping Python scripts using symmetric keys across all departments.

Sparse Payload: Explicit null values waste massive amounts of LLM context window tokens. The parser strips nulls; if a key isn't present for a given week, the Agent's tool simply assumes 0 or null using .get('metric', 0.0).

Example Snippet:

{
  "date": "2026-02-16",
  "clinic_wide_metrics": {
    "total_revenue_all_services": 40454.28
  },
  "disciplines": {
    "physiotherapy": {
      "assessments": 10,
      "patient_visit_average_4_wk": 6.06
    },
    "massage_therapy": {
      "assessments": 2,
      "patient_visit_average_4_wk": 2.5
    }
  }
}


Handling the Messy Bits (Data Cleaning)

To ensure Agentic tools (like LangChain or OpenAI functions) don't crash or hallucinate when reading this data, I implemented the following standardizations:

Symbol Collisions: Excel columns like "Cancelled Ax" (Count) and "Cancelled Ax %" (Ratio) become identical when special characters are stripped, causing Pandas _1 suffix collisions. The script translates # to count and % to percentage before generating keys.

Extreme Abbreviations: "AX", "TX", and "NBO" save space in Excel but severely degrade LLM semantic reasoning. I added a regex-based expansion map (ax -> assessments, nbo -> new_bookings_online) to maximize context for the AI.

Dirty Data & Strict Typing: The raw file contains string artifacts in numeric columns (e.g., dates listed as "6", or revenue containing backticks `). I implemented strict pd.to_numeric casting. Any string artifacts evaluate to NaN and are cleanly dropped from the sparse payload.

With Another Two Hours...

Pydantic Validation: I would implement explicit Pydantic models for the JSON output to guarantee absolute schema integrity before writing to disk.

Date-Based Agentic Tools: I would write a suite of Python tools alongside this JSON that allow an AI Agent to query the payload via robust target_date string matching rather than just relying on array index positioning.

Unit Tests: I would expand pytest coverage to explicitly test the stateful grouping logic and acronym expansion map.

Appendix: AI Tooling Workflow

To ensure this JSON schema was truly optimized for Clara's AI-driven use cases, I utilized an LLM as a Senior Staff Engineering reviewer to pressure-test the data architecture prior to submission.

"Act as a Senior Staff Software Engineer specializing in LLMs and AI Agents. I am building a data pipeline for a clinic dashboard. My pipeline extracts messy Excel data and outputs it into this JSON payload. Our AI agents will need to read this JSON to generate business insights. Review the key names, structure, and data types in this JSON. Are they semantically clear for an LLM to parse? Point out any confusing structures, potential token-wasting, or areas where the LLM might hallucinate due to poor naming."

Result: This prompt identified the hallucination risk of Pandas _1 suffixes and the semantic ambiguity of abbreviations like NBO and TX, leading me to refactor the parser into the nested, fully-expanded architecture submitted above.

"I want to create a Python tool/function that an AI Agent can call to answer user questions like: 'What was our total Chiro revenue compared to PT revenue last week?' Based strictly on the JSON schema provided, write the Python function the agent would use to calculate this. In your analysis, tell me if my JSON structure makes this operation easy or unnecessarily difficult for the agent."

Result: This confirmed that the symmetric nested structure allows an LLM tool to utilize predictable dictionary lookups (e.g., .get('total_revenue')) across any discipline array without relying on fragile string-matching, proving the schema is production-ready for code-interpreting agents.