"""
Automated Screening Code Generator using Playwright and Gemini
Interacts with gemini.google.com to generate custom screening logic.
"""

import os
import time
import json
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright
from criteria_parser import parse_criteria


# Configuration
GEMINI_URL = "https://gemini.google.com/app"
DEFAULT_OUTPUT = "screen_articles_custom.py"


def create_gemini_prompt(criteria: dict, reference_code: str) -> str:
    """Create the prompt for Gemini to generate screening code."""
    
    prompt = f"""You are an expert Python developer specializing in systematic review automation.

I need you to generate a Python function called `screen_articles(json_path)` that screens academic articles based on custom criteria.

**REFERENCE CODE (for structure and logic patterns):**
```python
{reference_code}
```

**USER'S CUSTOM CRITERIA:**
```json
{json.dumps(criteria, indent=2)}
```

**REQUIREMENTS:**
1. Generate a complete, working `screen_articles(json_path)` function
2. Use the SAME sophisticated logic patterns from the reference code:
   - Hierarchical decision trees
   - Contextual exception handling (e.g., if keyword A is in title AND keyword B, treat differently)
   - Title vs abstract weighting
   - Complex boolean logic for competing diagnoses
3. Adapt the logic to use the user's custom criteria keywords
4. Maintain the same input/output format:
   - Input: JSON file with articles (each has 'key', 'title', 'abstract')
   - Output: List of dicts with 'Key', 'Title', 'Decision', 'Reason'
5. Include detailed reasoning for each decision
6. Add comments explaining the logic

**IMPORTANT:**
- Do NOT just do simple keyword matching
- Implement nuanced logic similar to the reference code
- Handle edge cases and exceptions
- Make the code production-ready

Generate ONLY the Python code for the `screen_articles` function and any helper functions needed. Do not include import statements or the main block - just the function(s)."""
    
    return prompt


def extract_code_from_gemini(page, prompt_text, max_wait=90):
    """
    Send prompt to Gemini and extract the generated code.
    
    Args:
        page: Playwright page object
        prompt_text: The prompt to send
        max_wait: Maximum seconds to wait for response
    
    Returns:
        str: Extracted Python code or None
    """
    print("Navigating to Gemini...")
    page.goto(GEMINI_URL)
    time.sleep(5)
    
    # Check if logged in
    try:
        print("Checking login status...")
        page.locator("div[contenteditable='true'], textarea").wait_for(state="visible", timeout=5000)
        print("✅ Login confirmed. Proceeding...")
    except:
        print("⚠️ Login verification failed. Please log in to Gemini.")
        print("Waiting 45 seconds for manual login...")
        time.sleep(45)
    
    # Send prompt
    try:
        print("Sending prompt to Gemini...")
        text_area = page.locator("div[contenteditable='true'], textarea")
        text_area.first.fill(prompt_text)
        time.sleep(1)
        
        # Press Enter to send
        text_area.first.press("Enter")
        print("✅ Prompt sent. Waiting for response...")
        
        # Wait for response to start
        time.sleep(10)
        
        # Wait for response to complete (check for stop generating button to disappear)
        print("Waiting for Gemini to finish generating...")
        wait_time = 0
        while wait_time < max_wait:
            # Check if still generating
            stop_button = page.locator("button:has-text('Stop generating'), button[aria-label*='Stop']")
            if stop_button.count() == 0:
                # Response likely complete
                time.sleep(5)  # Extra buffer
                break
            time.sleep(5)
            wait_time += 5
            print(f"  Still generating... ({wait_time}s)")
        
        print("✅ Response received. Extracting code...")
        
        # Extract response
        response_elements = page.locator("model-response, .model-response-text, message-content, [data-test-id*='response']")
        
        if response_elements.count() > 0:
            # Get the last response (most recent)
            last_response = response_elements.all()[-1].inner_text()
        else:
            # Fallback: try to get all text from main content area
            print("Using fallback extraction method...")
            main_content = page.locator("main, .conversation-container, .chat-history")
            if main_content.count() > 0:
                last_response = main_content.first.inner_text()
            else:
                last_response = page.content()
        
        # Extract Python code from response
        code = extract_python_code(last_response)
        
        if code:
            print(f"✅ Successfully extracted {len(code)} characters of code")
            return code
        else:
            print("⚠️ Could not find Python code in response")
            print("Response preview:")
            print(last_response[:500])
            return None
            
    except Exception as e:
        print(f"❌ Error during Gemini interaction: {e}")
        import traceback
        traceback.print_exc()
        return None


def extract_python_code(text: str) -> str:
    """
    Extract Python code from Gemini's response.
    Looks for code blocks marked with ```python or ```
    """
    # Try to find code block with python marker
    if '```python' in text:
        parts = text.split('```python')
        if len(parts) > 1:
            code_part = parts[1].split('```')[0]
            return code_part.strip()
    
    # Try to find any code block
    if '```' in text:
        parts = text.split('```')
        if len(parts) >= 3:
            # Get the first code block
            code_part = parts[1]
            # Remove language identifier if present
            lines = code_part.split('\n')
            if lines[0].strip() in ['python', 'py']:
                code_part = '\n'.join(lines[1:])
            return code_part.strip()
    
    # If no code blocks found, try to extract function definition
    if 'def screen_articles' in text:
        # Find the start of the function
        start_idx = text.find('def screen_articles')
        if start_idx != -1:
            # Extract from function start to end of text
            # This is a rough extraction
            return text[start_idx:].strip()
    
    return None


def create_complete_module(generated_function: str, criteria: dict, criteria_file: str) -> str:
    """Create a complete Python module with the generated function."""
    
    module_code = f'''"""
Custom Screening Module
Auto-generated from criteria file: {criteria_file}

Criteria Description:
{criteria.get('description', 'No description provided')}

Generated using Gemini AI via browser automation.
"""

import json
import csv

{generated_function}

if __name__ == "__main__":
    results = screen_articles('parsed_articles.json')
    with open('screening_results.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["Key", "Title", "Decision", "Reason"])
        writer.writeheader()
        writer.writerows(results)
    
    print("Screening complete. Results saved to screening_results.csv")
    for res in results:
        print(f"[{{res['Decision']}}] {{res['Title'][:50]}}... - {{res['Reason']}}")
'''
    
    return module_code


def main(criteria_file: str, output_file: str = None, browser_channel: str = "chrome"):
    """
    Main function to generate screening code using Gemini browser automation.
    
    Args:
        criteria_file: Path to criteria file (.txt, .docx, or .json)
        output_file: Path to save generated module
        browser_channel: Browser to use (chrome, msedge)
    """
    # Parse criteria
    print(f"\n{'='*70}")
    print("AUTOMATED SCREENING CODE GENERATOR")
    print(f"{'='*70}\n")
    
    print(f"📋 Parsing criteria from: {criteria_file}")
    try:
        criteria = parse_criteria(criteria_file)
        print(f"✅ Criteria parsed successfully!")
    except Exception as e:
        print(f"❌ Error parsing criteria: {e}")
        return
    
    # Read reference code
    reference_code_path = Path(__file__).parent / 'screen_articles.py'
    if not reference_code_path.exists():
        print(f"❌ Reference code not found: {reference_code_path}")
        return
    
    with open(reference_code_path, 'r', encoding='utf-8') as f:
        reference_code = f.read()
    
    # Create prompt
    print("\n🤖 Creating prompt for Gemini...")
    prompt = create_gemini_prompt(criteria, reference_code)
    print(f"✅ Prompt created ({len(prompt)} characters)")
    
    # Set output file
    if output_file is None:
        output_file = DEFAULT_OUTPUT
    output_path = Path(output_file).absolute()
    
    # Launch browser and interact with Gemini
    print(f"\n🌐 Launching {browser_channel} browser...")
    
    with sync_playwright() as p:
        profile_name = f"{browser_channel}_profile_screening"
        user_data_dir = Path.cwd() / profile_name
        
        print(f"Using profile: {user_data_dir}")
        
        try:
            browser = p.chromium.launch_persistent_context(
                str(user_data_dir),
                headless=False,
                channel=browser_channel,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--start-maximized",
                    "--no-sandbox",
                    "--disable-infobars"
                ],
                ignore_default_args=["--enable-automation"],
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Get or create page
            if len(browser.pages) > 0:
                page = browser.pages[0]
            else:
                page = browser.new_page()
            
            # Add anti-detection script
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Extract code from Gemini
            generated_code = extract_code_from_gemini(page, prompt)
            
            if generated_code:
                # Create complete module
                print("\n📝 Creating complete module...")
                complete_module = create_complete_module(generated_code, criteria, criteria_file)
                
                # Save to file
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(complete_module)
                
                print(f"\n{'='*70}")
                print("✅ SUCCESS!")
                print(f"{'='*70}")
                print(f"📄 Custom screening module saved to: {output_path}")
                print(f"\nNext steps:")
                print(f"1. Review the generated code: {output_path}")
                print(f"2. Parse your BibTeX file: python parse_bib.py")
                print(f"3. Run screening: python {output_file}")
                print(f"\n🌐 Browser will remain open for 10 seconds...")
                time.sleep(10)
            else:
                print("\n❌ Failed to extract code from Gemini response")
                print("🌐 Browser will remain open for manual inspection...")
                time.sleep(30)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("\n👋 Closing browser...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate custom screening code using Gemini AI browser automation",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "criteria_file",
        help="Path to criteria file (.txt, .docx, or .json)"
    )
    parser.add_argument(
        "--output",
        help=f"Output file path (default: {DEFAULT_OUTPUT})",
        default=None
    )
    parser.add_argument(
        "--browser",
        help="Browser channel to use (chrome, msedge)",
        default="chrome"
    )
    
    args = parser.parse_args()
    main(args.criteria_file, args.output, args.browser)
