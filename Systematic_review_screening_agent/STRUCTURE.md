# Repository Structure

## Core Files

### Main Scripts
- **`parse_bib.py`** - Parses BibTeX files to JSON format
- **`screen_articles.py`** - Original hardcoded screening logic (reference implementation)
- **`criteria_parser.py`** - Parses criteria from .txt/.docx/.json files
- **`generate_screening_code.py`** - Playwright-based browser automation for code generation

### Configuration
- **`config.py`** - Configuration template with settings and usage instructions
- **`requirements.txt`** - Python dependencies (playwright, python-docx)

### Documentation
- **`README.md`** - Comprehensive project documentation
- **`QUICKSTART.md`** - Quick start guide for new users
- **`LICENSE`** - MIT License

### Repository Files
- **`.gitignore`** - Git exclusions (user data, generated files, browser profiles)
- **`.git/`** - Git repository

### Examples
- **`examples/example_criteria.txt`** - Text format example
- **`examples/example_criteria.json`** - JSON format example

## Generated Files (Excluded from Git)

These files are created during usage and excluded via .gitignore:

- `screen_articles_custom.py` - AI-generated screening module
- `gemini_prompt.txt` - Generated prompt for Gemini
- `parsed_articles.json` - Parsed BibTeX data
- `screening_results.csv` - Screening results
- `chrome_profile_screening/` - Browser profile directory
- `__pycache__/` - Python cache

## Total Repository Size

**10 core files** + **2 example files** = Clean, focused repository

## File Sizes

| File | Size | Purpose |
|------|------|---------|
| generate_screening_code.py | 12.8 KB | Main automation script |
| README.md | 7.9 KB | Documentation |
| criteria_parser.py | 6.7 KB | Criteria parsing |
| screen_articles.py | 3.4 KB | Reference implementation |
| QUICKSTART.md | 2.1 KB | Quick guide |
| config.py | 1.9 KB | Configuration |
| parse_bib.py | 1.3 KB | BibTeX parser |
| LICENSE | 1.1 KB | MIT License |
| .gitignore | 0.6 KB | Git exclusions |

## Repository Health

✅ All core functionality implemented  
✅ Comprehensive documentation  
✅ Example files provided  
✅ Proper .gitignore configuration  
✅ MIT License included  
✅ Clean directory structure  
✅ No unnecessary files  
✅ Ready for GitHub publication
