# Systematic Review Multi-Agent Pipeline

A unified orchestrator for conducting systematic reviews using specialized AI agents. This pipeline automates the process from deduplication to final data verification.

## 🚀 Overview

This repository contains a suite of agents designed to work together to perform high-quality systematic reviews:

1.  **Deduplication Agent**: Removes duplicate records from search results.
2.  **Screening Agent**: Dual-pass title and abstract screening using Gemini AI.
3.  **Extraction Agent**: Dual-pass structured data extraction from full-text articles.
4.  **Verification Agent**: Cross-checks results and identifies items needing human adjudication.

## 📁 Repository Structure

- `run_pipeline.py`: The main entry point to orchestrate all phases.
- `Systematic_review_DeDuplication_agent/`: Logic for record cleaning.
- `Systematic_review_screening_agent/`: AI-powered screening logic.
- `Systematic_review_extraction_agent/`: Structured data extraction.
- `Sys_review_extraction_validation_agent/`: Verification and audit logging.

## 🛠️ Getting Started

### Prerequisites
- Python 3.8+
- Gemini API Key

### Installation
```bash
git clone <your-repo-url>
cd new_agents
pip install -r Systematic_review_DeDuplication_agent/requirements.txt
pip install -r Systematic_review_screening_agent/requirements.txt
pip install -r Systematic_review_extraction_agent/requirements.txt
pip install -r Sys_review_extraction_validation_agent/requirements.txt
```

### Usage
Run the full pipeline:
```bash
python run_pipeline.py --key YOUR_GEMINI_API_KEY --criteria criteria.txt --articles articles.json --template template.docx
```

## 📄 License
This project is licensed under the MIT License - see the individual agent folders for details.
