# ⚖️ Systematic Review Extraction & Validation Agent

![Gemini](https://img.shields.io/badge/AI--Powered-Gemini-blue)
![Python](https://img.shields.io/badge/Python-3.x-green)
![Status](https://img.shields.io/badge/Self--Healing-Enabled-brightgreen)

An advanced agentic pipeline that not only extracts data but **validates** it for perfection. It features a continuous monitoring system that identifies discrepancies and re-extracts data automatically—ensuring your final results are high-fidelity and publication-ready.

> [!IMPORTANT]
> **Self-Healing Pipeline**: This agent automatically detects errors in extraction (by cross-checking against the PDF text) and triggers a second extraction attempt to correct mistakes.

---

## ✨ Key Features

- **🤖 Automated Extraction**: Captures complex fields like Study Design, Sample Sizes, Comorbidities, and Outcomes.
- **⚖️ Smart Validation**: Compares extracted data against the source PDF text with human-level accuracy.
    - **CRITICAL Errors**: Triggers automatic re-extraction.
    - **MINOR Errors**: Logged for review but allowed to pass if scientifically equivalent.
- **♻️ Self-Healing**: Automatically repairs data entries that fail validation.
- **📊 Audit Logging**: Detailed discrepancy reports in `validation_discrepancies.xlsx`.

> [!NOTE]
> Running the extraction and validation agents requires the user to have or input an API key. Google allows a certain amount of free credits for every user, which is more than sufficient for these extraction and validation purposes; you do not need to worry about costs for typical review workloads.

---

## 🛠️ Setup

1.  **Dependencies**:
    ```bash
    pip install pandas openpyxl tqdm colorama google-generativeai playwright
    playwright install
    ```
2.  **API Key**: Obtain a free key from [Google AI Studio](https://aistudio.google.com/app/apikey).
3.  **Articles**: Place your research PDFs in the `Articles/` folder.

---

## 🚀 Usage

### ⚡ Full Pipeline (API Default - Recommended)
Runs the entire validation and self-healing loop using high-speed API calls.
```bash
python do_it_all.py --key "YOUR_API_KEY_HERE"
```

### 🌐 Manual Fallback (Browser-Based)
If you prefer to use the browser interactive mode:
```bash
python do_it_all.py --browser chrome
```

---

## 📋 Validation Tiers

The agent uses a tiered system to judge accuracy for professional scientific standards:

- ✅ **PASS**: Data is 100% correct OR only has **MINOR** issues (e.g., rounding <1%, "Male" vs "Men").
- ❌ **FAIL**: Data has **CRITICAL** issues (e.g., swapped cohorts, wrong numerical values, missing findings).
- 🛠️ **HEALED**: Articles that failed are re-extracted and re-validated.

---

## 📁 File Reference

- **`extracted_studies.xlsx`**: Your final, "healed" data results.
- **`validation_discrepancies.xlsx`**: Detailed findings from the validation agent.
- **`healing_comparison_report.xlsx`**: Snapshot of values corrected during the self-healing phase.

---
**Made with ❤️ for systematic review researchers**
