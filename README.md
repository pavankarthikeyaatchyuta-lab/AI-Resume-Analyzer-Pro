# AI Resume Analyzer Pro

AI Resume Analyzer Pro is a Streamlit app that analyzes resumes against a target role, generates ATS-style feedback, visualizes scoring, and creates an improved resume version in multiple download formats.

## Features

- Upload resume files in `PDF` or `DOCX`
- Analyze resumes for a target job role using Groq
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

## Project Structure

```text
AI_Resume_Analyzer_Pro/
|-- app.py
|-- frontend.py
|-- requirements.txt
|-- README.md
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
cd C:\Users\pavan\OneDrive\Desktop\AI_Resume_Analyzer_Pro
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

## How to Use

1. Upload a resume in `PDF` or `DOCX` format.
2. Enter the target job role.
3. Click `Analyze Resume`.
4. Review the analysis blocks and charts.
5. Open the `Improved Resume` tab to generate a rewritten version.
6. Download the generated files if needed.

## Notes

- A valid `GROQ_API_KEY` is required for analysis and resume generation.
- Scanned PDFs with no extractable text may not work correctly.
- Output quality depends on the resume content and target role provided.

## GitHub Push Steps

If Git is installed on your machine, use these commands from the project folder:

```powershell
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

If you already created the GitHub repository in the browser, replace:

```text
https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
```

with your actual repository URL.

## Troubleshooting

### Git is not recognized

Install Git for Windows from:

`https://git-scm.com/download/win`

Then reopen PowerShell and run:

```powershell
git --version
```

### Streamlit or package errors

Reinstall dependencies:

```powershell
pip install -r requirements.txt
```

### API key error

Make sure `GROQ_API_KEY` is set before running the app.
