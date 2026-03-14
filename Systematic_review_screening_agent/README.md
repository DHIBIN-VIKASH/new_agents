# 🔍 Systematic Review Screening Agent

![Gemini](https://img.shields.io/badge/AI--Powered-Gemini-blue)
![Python](https://img.shields.io/badge/Python-3.7%2B-green)
![License](https://img.shields.io/badge/License-MIT-orange)

An intelligent, AI-powered tool for automating title and abstract screening in systematic reviews. This agent uses **dual-pass strategy** to ensure consistency and applies complex inclusion/exclusion criteria with human-like reasoning.

> [!NOTE]
> **Dual-Pass Strategy**: Each article is screened twice independently. Decisions are only finalized when both passes agree, ensuring high reliability for scientific publications.

---

## ✨ Features

- **🤖 AI-Powered Reasoning**: Uses Google Gemini to generate sophisticated screening logic tailored to your protocol.
- **📄 Multi-Format Support**: Define rules in `.txt`, `.docx`, or `.json` formats.
- **🧠 Complex Logic**: Goes beyond keywords—understands contextual exceptions and nuanced decision trees.
- **📊 BibTeX Support**: Seamlessly parses `.bib` exports from PubMed, Scopus, and Cochrane.
- **📝 Decision Justification**: Provides a detailed rationale for every inclusion or exclusion.
- **🔄 PRISMA-Ready**: Outputs CSV files perfectly structured for PRISMA flowchart documentation.

---

## 🚀 Getting Started

### 📋 Prerequisites
- **Python 3.7+**
- **Google Account** (for Gemini access)
- **BibTeX File**: Your search results exported as `articles.bib`

### 📦 Installation
```bash
git clone https://github.com/DHIBIN-VIKASH/Systematic_review_screening_agent.git
cd Systematic_review_screening_agent
pip install -r requirements.txt
playwright install chromium
```

---

## 📖 Usage Workflow

### 1️⃣ Define Your Criteria
Create a `criteria.txt` file (or use .docx/.json).
```text
[INCLUSION]
- Population: Patients with Type 2 Diabetes
- Intervention: GLP-1 Receptor Agonists
[EXCLUSION]
- Animal studies
- Case reports with n < 5
```

### 2️⃣ Generate Custom Screening Agent
This script will use Gemini to "write" the screening logic specifically for your review.
```bash
python generate_screening_code.py criteria.txt
```
*Note: This generates `screen_articles_custom.py`.*

### 3️⃣ Parse and Screen
```bash
# Convert BibTeX to JSON
python parse_bib.py

# Run the screening logic (Dual-Pass)
python screen_articles_custom.py
```

### ⚡ API-Based Screening (Optional)
For highly efficient large-scale screening:
```bash
python screen_articles_api.py --key "YOUR_API_KEY"
```

---

## 📁 Project Structure

```text
Systematic_review_screening_agent/
├── generate_screening_code.py  # AI Logic Generator
├── screen_articles_api.py      # High-speed API screen
├── screen_articles_custom.py   # Your criteria-specific agent
├── parse_bib.py                # BibTeX to JSON converter
├── examples/                   # Sample criteria files
└── requirements.txt            # Dependencies
```

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
**Made with ❤️ for systematic reviewers worldwide**
