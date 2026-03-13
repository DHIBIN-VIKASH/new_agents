# Systematic Review Screening Agent

An intelligent, AI-powered tool for automating the title and abstract screening process in systematic reviews. This tool uses **browser automation with Gemini AI** to generate custom screening logic tailored to your specific research criteria.

## 🌟 Features

- **🤖 AI-Powered Customization**: Uses Google's Gemini (via browser automation) to generate sophisticated screening logic from your criteria
- **📄 Multiple Input Formats**: Define criteria in `.txt`, `.docx`, or `.json` formats
- **🧠 Intelligent Logic**: Generates nuanced decision trees with contextual exception handling, not just simple keyword matching
- **📊 BibTeX Support**: Parses `.bib` files exported from PubMed, Scopus, Web of Science, and other databases
- **📝 Detailed Reasoning**: Provides clear explanations for every inclusion/exclusion decision
- **🔄 PRISMA-Ready**: Outputs CSV files compatible with PRISMA workflow documentation
- **🌐 No API Key Required**: Uses browser automation - just log in to Gemini once

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- Google account (for Gemini access)
- Chrome or Edge browser

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/Systematic_review_screening_agent.git
   cd Systematic_review_screening_agent
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers**:
   ```bash
   playwright install chromium
   ```

### Basic Usage

#### Step 1: Prepare Your Criteria File

Create a criteria file defining your inclusion/exclusion rules. See [Criteria File Formats](#criteria-file-formats) below.

Example (`my_criteria.txt`):
```
[DESCRIPTION]
Screening for studies on diabetes treatment in elderly patients

[INCLUSION_KEYWORDS]
Primary Topic: Diabetes, Type 2 Diabetes, T2DM
Population: Elderly, Geriatric, Aged, Senior
Intervention: Treatment, Therapy, Management

[EXCLUSION_KEYWORDS]
Study Types: Systematic Review, Meta-Analysis
Other Conditions: Type 1 Diabetes, Pediatric
```

#### Step 2: Generate Custom Screening Code

The script will open a browser, log in to Gemini (first time only), and automatically generate the code:

```bash
python generate_screening_code.py my_criteria.txt
```

**First-time setup:**
- Browser will open to gemini.google.com
- Log in with your Google account (one-time)
- The script will automatically send the prompt and extract the generated code
- Generated code is saved as `screen_articles_custom.py`

#### Step 3: Prepare Your Articles

Place your BibTeX file (exported from your database) in the project folder as `articles.bib`.

#### Step 4: Parse and Screen

```bash
# Parse BibTeX to JSON
python parse_bib.py

# Run screening with your custom logic
python screen_articles_custom.py
```

#### Step 5: Review Results

Open `screening_results.csv` to see your screening results with decisions and reasoning.

## 📋 Criteria File Formats

### Text Format (.txt)

Simple, human-readable format:

```
[DESCRIPTION]
Brief description of your screening criteria

[INCLUSION_KEYWORDS]
Category Name: keyword1, keyword2, keyword3
Another Category: keyword4, keyword5

[EXCLUSION_KEYWORDS]
Study Types: Systematic Review, Meta-Analysis
Unwanted Topics: keyword6, keyword7

[MATCHING_RULES]
Case Sensitive: No
Primary Topic in Title Required: Yes
```

### JSON Format (.json)

Structured format for programmatic use:

```json
{
  "description": "Your screening criteria description",
  "inclusion": {
    "primary_topic": ["keyword1", "keyword2"],
    "population": ["keyword3", "keyword4"]
  },
  "exclusion": {
    "study_types": ["Systematic Review", "Meta-Analysis"],
    "unwanted_topics": ["keyword5", "keyword6"]
  },
  "rules": {
    "case_sensitive": false,
    "primary_in_title_required": true
  }
}
```

### Word Format (.docx)

Structured document with:
- **Heading 1**: Section names (Inclusion Criteria, Exclusion Criteria, Description)
- **Heading 2**: Category names (Primary Topic, Population, etc.)
- **Bullet points**: Individual keywords

See `examples/` folder for complete examples.

## 🔧 Advanced Usage

### Using the Original Hardcoded Version

If you want to use the original hardcoded screening logic (for Giant Cell Tumor in Cervical Spine):

```bash
python parse_bib.py
python screen_articles.py
```

### Customizing Generated Code

After generating `screen_articles_custom.py`, you can manually edit it to fine-tune the logic if needed.

### Testing Your Criteria

Use the example files to test your setup:

```bash
python generate_screening_code.py examples/example_criteria.txt screen_test.py
```

## 📁 Project Structure

```
Systematic_review_screening_agent/
├── parse_bib.py                 # BibTeX parser
├── screen_articles.py           # Original hardcoded screening logic (reference)
├── criteria_parser.py           # Criteria file parser
├── generate_screening_code.py  # LLM-based code generator
├── requirements.txt             # Python dependencies
├── LICENSE                      # MIT License
├── README.md                    # This file
└── examples/                    # Example criteria files
    ├── example_criteria.txt
    ├── example_criteria.json
    └── example_criteria.docx
```

## 🎯 How It Works

1. **Criteria Parsing**: Your criteria file is parsed into a structured format
2. **AI Code Generation**: Gemini API analyzes your criteria and the reference code to generate sophisticated screening logic
3. **Smart Screening**: The generated code applies nuanced decision-making:
   - Hierarchical exclusion rules
   - Contextual exception handling
   - Title vs. abstract weighting
   - Complex boolean logic for competing topics
4. **Detailed Output**: Each article gets a decision (Include/Exclude) with clear reasoning

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Google Gemini API](https://ai.google.dev/)
- Inspired by the need for efficient systematic review screening
- Original use case: Giant Cell Tumor research in cervical spine

## 📧 Support

If you encounter any issues or have questions:
- Open an issue on GitHub
- Check the `examples/` folder for reference implementations

## ⚠️ Important Notes

- **Browser Automation**: Uses Playwright to interact with gemini.google.com - no API costs!
- **First-Time Login**: You'll need to log in to Gemini once; the browser profile is saved for future use
- **Review Generated Code**: Always review the AI-generated screening logic before using it for important research
- **Manual Verification**: This tool assists with screening but doesn't replace expert judgment. Always verify critical decisions
- **Browser Compatibility**: Works with Chrome or Edge browsers

## 🔮 Future Enhancements

- [ ] Support for RIS and other citation formats
- [ ] Web interface for easier use
- [ ] Batch processing for multiple criteria sets
- [ ] Integration with reference management tools
- [ ] Export to Rayyan, Covidence, and other screening platforms

---

**Made with ❤️ for systematic reviewers worldwide**
