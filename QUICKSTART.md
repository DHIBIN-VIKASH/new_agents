# Quick Start Guide

## For First-Time Users

### 1. Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Create Your Criteria File

Copy and modify `examples/example_criteria.txt`:

```
[DESCRIPTION]
Your research topic description

[INCLUSION_KEYWORDS]
Primary Topic: keyword1, keyword2, keyword3
Population: keyword4, keyword5

[EXCLUSION_KEYWORDS]
Study Types: Systematic Review, Meta-Analysis
```

### 3. Generate Custom Screening Code

```bash
python generate_screening_code.py my_criteria.txt
```

**What happens:**
- Browser opens to gemini.google.com
- First time: Log in with your Google account
- Script automatically sends prompt to Gemini
- Waits for AI to generate the code
- Extracts and saves code as `screen_articles_custom.py`
- Browser profile is saved for next time (no re-login needed)

### 4. Screen Your Articles

```bash
# Place your .bib file as articles.bib
python parse_bib.py
python screen_articles_custom.py
```

### 5. Review Results

Open `screening_results.csv` to see your screening decisions!

## Using the Original Example

To test with the included example (Giant Cell Tumor screening):

```bash
python parse_bib.py
python screen_articles.py
```

## Troubleshooting

**"Playwright not found"**
- Run: `playwright install chromium`

**"python-docx not found"** 
- Run: `pip install -r requirements.txt`

**Browser doesn't open**
- Try specifying browser: `python generate_screening_code.py my_criteria.txt --browser msedge`

**Generated code doesn't match expectations**
- Review and manually edit `screen_articles_custom.py`
- Refine your criteria file to be more specific
- Try running the generation again

**Login issues**
- Make sure you're logged in to Google in your default browser
- The script uses a persistent browser profile to save your login

## Need Help?

- Check `README.md` for detailed documentation
- See `examples/` folder for reference files
- Open an issue on GitHub
