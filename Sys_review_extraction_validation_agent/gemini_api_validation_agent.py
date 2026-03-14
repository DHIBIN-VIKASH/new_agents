import os
import time
import json
import pandas as pd
import argparse
import google.generativeai as genai
from google.api_core import exceptions
from tqdm import tqdm
from colorama import init, Fore

# Initialize colorama
init(autoreset=True)

# Configuration
ARTICLES_DIR = 'Articles'
INPUT_FILE = 'extracted_studies.xlsx'
VALIDATION_LOG = 'validation_discrepancies.xlsx'
MODEL_NAME = "models/gemini-2.0-flash"

def create_validation_prompt(row_data):
    """Creates a prompt for Gemini to validate the extracted data."""
    meta_cols = ['Source File', 'Sl.no', 'Unnamed: 0']
    clean_data = {k: v for k, v in row_data.items() if k not in meta_cols and pd.notnull(v)}
    
    prompt = "I have extracted the following data from the attached PDF study. Please verify the accuracy of each field against the PDF content.\n\n"
    prompt += "### DATA TO VERIFY ###\n"
    prompt += json.dumps(clean_data, indent=2)
    prompt += "\n\n### INSTRUCTIONS ###\n"
    prompt += "1. Review the attached PDF carefully.\n"
    prompt += "2. For each field in the provided JSON, check if the value is correct.\n"
    prompt += "3. If a value is incorrect or incomplete, provide the correct information found in the PDF.\n"
    prompt += "4. If you find any discrepancies, return your findings in the following JSON format:\n"
    prompt += '{\n  "discrepancies": [\n    {\n      "field": "Field Name",\n      "extracted_value": "Value provided in prompt",\n      "correct_value": "Correct value from PDF",\n      "severity": "CRITICAL", // or "MINOR"\n      "description": "Explanation of the discrepancy"\n    }\n  ],\n  "status": "FAIL"\n}\n'
    prompt += "\n### SEVERITY CRITERIA ###\n"
    prompt += "- MINOR: Formatting issues (e.g. '50 %' vs '50%'), synonyms (e.g. 'Male' vs 'Men'), or rounding differences less than 1%.\n"
    prompt += "- CRITICAL: Different numbers (>1% variance), swapped data, missing data that exists in text, or hallucinations.\n"
    prompt += "5. If all information is 100% correct, return status: 'PASS'.\n"
    prompt += "6. If there is even a MINOR discrepancy, set status to 'FAIL'.\n"
    prompt += "\nReturn ONLY the JSON object. No markdown formatting."
    return prompt

def validate_with_api(pdf_path, prompt, model):
    """Uploads file and validates data using Gemini API."""
    try:
        sample_file = genai.upload_file(path=pdf_path, display_name=os.path.basename(pdf_path))
        while sample_file.state.name == "PROCESSING":
            time.sleep(1)
            sample_file = genai.get_file(sample_file.name)
            
        if sample_file.state.name == "FAILED":
            return None

        generation_config = genai.GenerationConfig(response_mime_type="application/json")
        response = model.generate_content([sample_file, prompt], generation_config=generation_config)
        
        try:
            genai.delete_file(sample_file.name)
        except:
            pass

        return json.loads(response.text)
            
    except exceptions.ResourceExhausted:
         time.sleep(30)
         return "RETRY"
    except Exception as e:
        print(f"API Error: {e}")
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", help="Gemini API Key", required=True)
    parser.add_argument("--limit", help="Limit number of rows", default=None)
    parser.add_argument("--files", help="Specific files", nargs="+", default=None)
    args = parser.parse_args()

    genai.configure(api_key=args.key)
    model = genai.GenerativeModel(MODEL_NAME)

    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    df = pd.read_excel(INPUT_FILE)
    if args.files:
        df = df[df['Source File'].isin(args.files)]
    elif args.limit:
        df = df.head(int(args.limit))

    print(f"Starting API validation for {len(df)} rows...")
    validation_results = []

    for index, row in tqdm(df.iterrows(), total=len(df)):
        source_file = row['Source File']
        pdf_path = os.path.join(ARTICLES_DIR, source_file)
        
        if not os.path.exists(pdf_path):
            continue

        prompt = create_validation_prompt(row.to_dict())
        result = validate_with_api(pdf_path, prompt, model)
        
        if result == "RETRY":
            result = validate_with_api(pdf_path, prompt, model)

        if result and result != "RETRY":
            result['Source File'] = source_file
            validation_results.append(result)
            
            # Incremental Log Save
            flattened = []
            for res in validation_results:
                sf = res.get('Source File')
                status = res.get('status', 'FAIL')
                if not res.get('discrepancies'):
                    flattened.append({'Source File': sf, 'Status': status, 'Field': None, 'Description': 'None'})
                else:
                    for d in res['discrepancies']:
                        flattened.append({
                            'Source File': sf,
                            'Status': status,
                            'Field': d.get('field'),
                            'Extracted Value': d.get('extracted_value'),
                            'Correct Value': d.get('correct_value'),
                            'Description': d.get('description'),
                            'Severity': d.get('severity')
                        })
            pd.DataFrame(flattened).to_excel(VALIDATION_LOG, index=False)
            time.sleep(4)

    print("API Validation Complete.")

if __name__ == "__main__":
    main()
