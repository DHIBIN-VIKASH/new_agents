# Configuration File for Systematic Review Screening Agent

# =============================================================================
# GEMINI API CONFIGURATION
# =============================================================================
# Get your API key from: https://makersuite.google.com/app/apikey
# Set as environment variable: GEMINI_API_KEY=your-key-here

# =============================================================================
# USAGE INSTRUCTIONS
# =============================================================================
# 1. Create your criteria file (see examples/ folder)
# 2. Generate custom screening code:
#    python generate_screening_code.py your_criteria.txt
# 3. Parse your BibTeX file:
#    python parse_bib.py
# 4. Run screening:
#    python screen_articles_custom.py

# =============================================================================
# CRITERIA FILE LOCATION
# =============================================================================
# Default criteria file (optional - can be specified via command line)
DEFAULT_CRITERIA_FILE = "examples/example_criteria.txt"

# =============================================================================
# OUTPUT SETTINGS
# =============================================================================
# Output file for screening results
OUTPUT_FILE = "screening_results.csv"

# Verbose output (show detailed matching information)
VERBOSE = True

# =============================================================================
# ADVANCED SETTINGS
# =============================================================================
# Gemini model to use for code generation
GEMINI_MODEL = "gemini-2.0-flash-exp"

# Temperature for code generation (0.0 = deterministic, 1.0 = creative)
GENERATION_TEMPERATURE = 0.3

# Maximum tokens for generated code
MAX_OUTPUT_TOKENS = 8192
