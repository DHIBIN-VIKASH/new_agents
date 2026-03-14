# Systematic Review Extraction & Validation Agent

*Note: A verification agent continuously monitors logs, identifies discrepancies, and directs them to human reviewers. Dual independent reviewers validate AI outputs for deduplication, screening, and extraction. Discrepancies flagged by the verification agent are resolved through consensus adjudication. Audit trails document the origin of each data element, the agent responsible, and any human intervention. All records processed by the system are verified for validity, with human reviewers confirming that no fabricated or hallucinated data are introduced.*

This tool automates the extraction of data from scientific PDF articles and validates the accuracy of that data. It primarily utilizes the **Google Gemini API** for efficient extraction, while providing a Playwright-based browser fallback. It features a self-healing pipeline that automatically detects discrepancies and re-extracts data from failed articles.

## Key Features
- **Automated Extraction:** Extracts complex data fields including Study Design, Sample Size, Comorbidities, and Outcomes.
- **Smart Validation:** Compares extracted data against the original PDF text.
    - **CRITICAL Errors:** (Data mismatch >1%, swapped cohorts) trigger re-extraction.
    - **MINOR Errors:** (Formatting, synonyms) are flagged but allowed to PASS.
- **Self-Healing:** Automatically re-processes articles that fail validation.
- **Reporting:** Generates detailed reports on what data was changed (`healing_comparison_report.xlsx`) and what discrepancies remain (`validation_discrepancies.xlsx`).
    - *Note: The main `extracted_studies.xlsx` remains clean and free of validation metadata.*

> [!NOTE]
> Running the extraction and validation agents requires the user to have or input an API key. Google allows a certain amount of free credits for every user, which is more than sufficient for these extraction and validation purposes; you do not need to worry about costs for typical review workloads.

## Setup
1.  **Environment:** Ensure Python 3.x is installed.
2.  **Dependencies:** Install required packages.
    ```bash
    pip install pandas openpyxl tqdm colorama google-generativeai playwright
    playwright install
    ```
3.  **API Key (Default):** Obtain a free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
4.  **Browser (Fallback):** For the browser-based method, ensure you are logged into Gemini in your Chrome/Edge profile.

## Usage

### 1. Full Pipeline (API Default - Recommended)
Run the master orchestration script using your API key. This will perform **API-based validation, self-healing, and extraction**. It is significantly faster and more stable.
```bash
python do_it_all.py --key "YOUR_API_KEY_HERE"
```

### 2. Browser-Based Pipeline (Alternative - Manual Fallback)
If you prefer to use the browser-based interaction (requires login and is slower):
```bash
python do_it_all.py --browser chrome
```

### 3. File Inputs/Outputs
- **Input:** `Articles/` directory containing PDF references.
- **Input Template:** `template_extracted_studies.xlsx` (Optional).
- **Output:** `extracted_studies.xlsx` (The final data).
- **Logs:**
    - `validation_discrepancies.xlsx`: Detailed findings from the validation agent.
    - `healing_comparison_report.xlsx`: Snapshot of values corrected during self-healing.

## Validation Logic
The agent uses a tiered system to judge accuracy:
- **PASS:** Data is 100% correct OR has only **MINOR** issues (rounding <1%, "Male" vs "Men").
- **FAIL:** Data has **CRITICAL** issues (wrong numbers, missing data).
- **FAIL:** Data has **CRITICAL** issues (wrong numbers, missing data).
- **Feedback:** Detailed feedback is logged in sections `validation_discrepancies.xlsx`. The main output file is kept clean.
