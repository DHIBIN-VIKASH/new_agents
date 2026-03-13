"""
Criteria Parser Module
Parses screening criteria from text, Word, or JSON files.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any


def parse_text_criteria(file_path: str) -> Dict[str, Any]:
    """
    Parse criteria from a text file.
    
    Expected format:
    [SECTION_NAME]
    Category: keyword1, keyword2, keyword3
    
    Example:
    [INCLUSION_KEYWORDS]
    Primary Topic: Giant Cell Tumor, Osteoclastoma
    Anatomical Location: Cervical, C1, C2
    
    [EXCLUSION_KEYWORDS]
    Study Types: Systematic Review, Meta-Analysis
    """
    criteria = {
        'inclusion': {},
        'exclusion': {},
        'rules': {},
        'description': ''
    }
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    current_section = None
    
    for line in content.split('\n'):
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Check for section headers
        if line.startswith('[') and line.endswith(']'):
            section_name = line[1:-1].strip().lower()
            if 'inclusion' in section_name:
                current_section = 'inclusion'
            elif 'exclusion' in section_name:
                current_section = 'exclusion'
            elif 'rule' in section_name or 'config' in section_name:
                current_section = 'rules'
            elif 'description' in section_name:
                current_section = 'description'
            continue
        
        # Parse key-value pairs
        if ':' in line and current_section in ['inclusion', 'exclusion']:
            key, value = line.split(':', 1)
            key = key.strip().lower().replace(' ', '_')
            # Split by comma and clean up
            keywords = [kw.strip() for kw in value.split(',') if kw.strip()]
            criteria[current_section][key] = keywords
        
        # Parse rules
        elif ':' in line and current_section == 'rules':
            key, value = line.split(':', 1)
            key = key.strip().lower().replace(' ', '_')
            value = value.strip()
            # Convert to appropriate type
            if value.lower() in ['yes', 'true', '1']:
                criteria['rules'][key] = True
            elif value.lower() in ['no', 'false', '0']:
                criteria['rules'][key] = False
            else:
                criteria['rules'][key] = value
        
        # Parse description
        elif current_section == 'description':
            criteria['description'] += line + ' '
    
    return criteria


def parse_docx_criteria(file_path: str) -> Dict[str, Any]:
    """
    Parse criteria from a Word document.
    
    Expected structure:
    - Heading 1: Section names (Inclusion Criteria, Exclusion Criteria)
    - Heading 2: Category names (Primary Topic, Anatomical Location)
    - Bullet points or paragraphs: Keywords
    """
    try:
        from docx import Document
    except ImportError:
        raise ImportError("python-docx is required for Word document parsing. Install with: pip install python-docx")
    
    criteria = {
        'inclusion': {},
        'exclusion': {},
        'rules': {},
        'description': ''
    }
    
    doc = Document(file_path)
    current_section = None
    current_category = None
    
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        
        # Check heading level
        if para.style.name.startswith('Heading 1'):
            if 'inclusion' in text.lower():
                current_section = 'inclusion'
            elif 'exclusion' in text.lower():
                current_section = 'exclusion'
            elif 'rule' in text.lower() or 'config' in text.lower():
                current_section = 'rules'
            elif 'description' in text.lower():
                current_section = 'description'
            current_category = None
        
        elif para.style.name.startswith('Heading 2') and current_section in ['inclusion', 'exclusion']:
            current_category = text.lower().replace(' ', '_')
            criteria[current_section][current_category] = []
        
        elif current_section in ['inclusion', 'exclusion'] and current_category:
            # Extract keywords from bullet points or comma-separated text
            if ',' in text:
                keywords = [kw.strip() for kw in text.split(',') if kw.strip()]
            else:
                keywords = [text]
            criteria[current_section][current_category].extend(keywords)
        
        elif current_section == 'description':
            criteria['description'] += text + ' '
    
    return criteria


def parse_json_criteria(file_path: str) -> Dict[str, Any]:
    """Parse criteria from a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        criteria = json.load(f)
    
    # Ensure required structure
    if 'inclusion' not in criteria:
        criteria['inclusion'] = {}
    if 'exclusion' not in criteria:
        criteria['exclusion'] = {}
    if 'rules' not in criteria:
        criteria['rules'] = {}
    if 'description' not in criteria:
        criteria['description'] = ''
    
    return criteria


def parse_criteria(file_path: str) -> Dict[str, Any]:
    """
    Parse screening criteria from a file.
    Automatically detects file type and uses appropriate parser.
    
    Args:
        file_path: Path to criteria file (.txt, .docx, or .json)
    
    Returns:
        Dictionary containing parsed criteria
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Criteria file not found: {file_path}")
    
    extension = path.suffix.lower()
    
    if extension == '.txt':
        return parse_text_criteria(file_path)
    elif extension == '.docx':
        return parse_docx_criteria(file_path)
    elif extension == '.json':
        return parse_json_criteria(file_path)
    else:
        raise ValueError(f"Unsupported file format: {extension}. Supported formats: .txt, .docx, .json")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python criteria_parser.py <criteria_file>")
        sys.exit(1)
    
    criteria_file = sys.argv[1]
    
    try:
        criteria = parse_criteria(criteria_file)
        print(json.dumps(criteria, indent=2))
    except Exception as e:
        print(f"Error parsing criteria: {e}")
        sys.exit(1)
