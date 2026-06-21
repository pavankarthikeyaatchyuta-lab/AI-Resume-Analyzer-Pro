# AI Resume Analyzer Pro

AI Resume Analyzer Pro is a Streamlit app that analyzes resumes against a target role or pasted job description, generates ATS-style feedback, visualizes scoring, and creates an improved resume version in multiple download formats.

## Features

- Upload resume files in `PDF` or `DOCX`
- Analyze resumes for a target job role using Groq
- Paste a full job description into the same input field if needed
- View `Resume Score`, `ATS Score`, and `Job Suitability Score`
- See separate feedback blocks for:
  - Top Suggestions
  - Missing Keywords
  - Skill Gap Analysis
  - Improved Bullet Points
  - Additional Notes
- Visualize scores with:
  - Vertical Bar
  - Horizontal Bar
  - Pie Chart
  - Radar Chart
  - Gauge Dashboard
- Generate an improved resume version
- Download outputs as `PDF`, `DOCX`, and `TXT`

## Backend Improvements

- Uses structured JSON output from Groq for more reliable analysis parsing
- Falls back to the legacy text parser if JSON parsing fails
- Caches repeated analyses for the same resume file and job role
- Adds light job-description matching support for long pasted JDs
- Includes unit tests for core parsing and formatting helpers

## Project Structure

```text
AI_Resume_Analyzer_Pro/
|-- app.py
|-- frontend.py
|-- requirements.txt
|-- README.md
|-- tests/
|   `-- test_app_logic.py
|-- .gitignore
```

## Tech Stack

- Python
- Streamlit
- Groq API
- pdfplumber
- python-docx
- Plotly
- ReportLab

## Setup

### 1. Clone or open the project folder

```powershell
cd C:\Users\pavan\Downloads\AI-Resume-Analyzer-Pro
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
```

### 3. Activate the virtual environment

```powershell
.venv\Scripts\activate
```

### 4. Install dependencies

```powershell
pip install -r requirements.txt
```

### 5. Add your Groq API key

You can use either:

- Streamlit secrets
- Environment variables

Recommended Streamlit secret file:

```toml
# .streamlit/secrets.toml
GROQ_API_KEY = "your_groq_api_key_here"
```

PowerShell example:

```powershell
$env:GROQ_API_KEY="your_groq_api_key_here"
```

## Run the App

```powershell
streamlit run app.py
```

Then open the local URL shown by Streamlit, usually:

```text
http://localhost:8501
```

## Run Tests

```powershell
python -m pytest -q
```

## How to Use

1. Upload a resume in `PDF` or `DOCX` format.
2. Enter the target job role, or paste a full job description.
3. Click `Analyze Resume`.
4. Review the analysis blocks and charts.
5. Open the `Improved Resume` tab to generate a rewritten version.
6. Download the generated files if needed.

## Notes

- A valid `GROQ_API_KEY` is required for analysis and resume generation.
- Scanned PDFs with no extractable text may not work correctly.
- Output quality depends on the resume content and target role provided.
- The app is designed to keep the UI unchanged while improving backend reliability.

### Streamlit or package errors

Reinstall dependencies:

```powershell
pip install -r requirements.txt
```

### API key error

Make sure `GROQ_API_KEY` is set before running the app.
