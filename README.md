# 🏥 Systematic Review Multi-Agent Pipeline

![AI-Powered](https://img.shields.io/badge/AI--Powered-Gemini-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-green)
![License](https://img.shields.io/badge/License-MIT-orange)

A unified orchestrator for conducting systematic reviews using specialized AI agents. This pipeline automates the entire evidence synthesis workflow—from database record deduplication to final data verification—ensuring accuracy, speed, and PRISMA compliance.

---

## 🚀 The Multi-Agent Workflow

This framework is composed of four specialized agents that work in sequence to deliver high-quality systematic reviews:

### 1. 🧹 [Deduplication Agent](./Systematic_review_DeDuplication_agent)
- Operates on search results from multiple databases (PubMed, Scopus, etc.).
- Uses hierarchical matching (DOI, PMID, Fuzzy Title) to remove overlapping records.

### 2. 🔍 [Screening Agent](./Systematic_review_screening_agent)
- Performs dual-pass title and abstract screening.
- Applies inclusion/exclusion criteria using autonomous reasoning to identify eligible studies.

### 3. 📄 [Extraction Agent](./Systematic_review_extraction_agent)
- Extracts complex data fields from full-text PDF articles.
- Utilizes cross-agent redundancy (dual-pass) to ensure data reliability.

### 4. ⚖️ [Extraction & Validation Agent](./Sys_review_extraction_validation_agent)
- Monitors logs and flags discrepancies for human adjudication.
- Features a self-healing pipeline to re-extract data from failed validations.

---

## 📁 Repository Structure

```text
root/
├── run_pipeline.py                 # Main orchestration entry point
├── Systematic_review_DeDuplication_agent/  # Record cleaning logic
├── Systematic_review_screening_agent/      # AI screening logic
├── Systematic_review_extraction_agent/     # Data extraction logic
└── Sys_review_extraction_validation_agent/  # Verification & self-healing
```

---

## 🛠️ Getting Started

### 📋 Prerequisites
- **Python 3.8+**
- **Gemini API Key** (Required for the recommended high-speed workflow)

### 📦 Installation
Clone the repository and install the dependencies for each agent:
```bash
git clone <your-repo-url>
cd new_agents
# Install core dependencies (example)
pip install -r Sys_review_extraction_validation_agent/requirements.txt
```

### ⚡ Usage
Run the unified pipeline orchestrator:
```bash
python run_pipeline.py --key YOUR_GEMINI_API_KEY --criteria criteria.txt --articles articles.json --template template.docx
```

---

> [!TIP]
> **API & Costs**: Running these agents primarily utilizes the **Google Gemini API**. Google provides free credits to every user, which is typically more than sufficient for scientific systematic reviews. You do not need to worry about significant costs for standard workloads.

## 📄 License
This project is licensed under the MIT License. Each agent folder contains its own license details where applicable.
