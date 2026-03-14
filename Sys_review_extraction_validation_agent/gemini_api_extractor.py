import os
import time
import json
import pandas as pd
import argparse
import google.generativeai as genai
from google.api_core import exceptions
from datetime import datetime

# Configuration
ARTICLES_DIR = 'Articles'
OUTPUT_FILE = 'extracted_studies.xlsx'
MODEL_NAME = "models/gemini-2.0-flash"

# Column Definitions (Matches the paper and the original Playwright version)
STUDY_CHARACTERISTICS = [
    ("Study ID", "First author + year (e.g., Barkyoumb 2025)"),
    ("Journal", "Source of publication"),
    ("Country/Region", "Study location(s)"),
    ("Study Design", "Retrospective cohort, RCT, meta-analysis, etc."),
    ("Database/Setting", "National claims, single-center, multicenter, etc."),
    ("Sample Size (Total)", "Number of patients included"),
    ("GLP-1 RA Cohort Size", "Number of patients exposed"),
    ("Control Cohort Size", "Number of patients not exposed"),
    ("Age (mean ± SD)", "Baseline age"),
    ("Sex (% male/female)", "Gender distribution"),
    ("BMI (mean ± SD)", "Baseline BMI"),
    ("Diabetes Status (%)", "% with T2DM"),
    ("Other Comorbidities", "Hypertension, CAD, CKD, smoking, etc."),
    ("GLP-1 Agent(s)", "Semaglutide, liraglutide, tirzepatide, etc."),
    ("Exposure Definition", "Pre-op, peri-op, post-op; duration window"),
    ("Dosing Regimen", "Weekly vs daily, dose escalation"),
    ("Surgical Procedure", "ACDF, PCF, TLIF, PLIF, lumbar fusion, decompression"),
    ("Levels Fused", "Single vs multilevel"),
    ("Follow-up Duration", "90 days, 6 months, 1 year, 2 years, etc."),
    ("Matching/Adjustment", "Propensity score, covariates controlled"),
    ("Risk of Bias", "ROBINS-I, NOS, etc.")
]

OUTCOMES = [
    ("Surgical Site Infection (SSI)", "Yes/No, % incidence"),
    ("Wound Complications", "Dehiscence, delayed healing"),
    ("Venous Thromboembolism (VTE)", "DVT/PE incidence"),
    ("Mortality", "30-day, 90-day, 1-year"),
    ("Readmission", "30-day, 90-day, 1-year"),
    ("Reoperation", "Same-level vs adjacent-level"),
    ("Pseudarthrosis", "Radiographic or clinical nonunion"),
    ("Fusion Success", "Solid fusion rates"),
    ("Implant/Hardware Failure", "Breakage, loosening"),
    ("Operative Time", "Mean ± SD"),
    ("Blood Loss", "Mean ± SD"),
    ("Length of Stay (LOS)", "Median/mean days"),
    ("Emergency Department Visits", "Within 90 days"),
    ("Medical Complications", "Anemia, AKI, renal failure, pneumonia"),
    ("Glycemic Control", "HbA1c change, peri-op glucose variability"),
    ("Cardiovascular Events", "MI, stroke"),
    ("Neurological Outcomes", "Dysphagia, mobility deficits"),
    ("Nutritional/Muscle Outcomes", "Lean mass loss, sarcopenia"),
    ("Adverse Drug Events", "Pancreatitis, thyroid cancer, GI symptoms"),
    ("Other Notes", "Any unique findings (e.g., SEL regression, neuroprotection)")
]

ALL_COLUMNS = [c[0] for c in STUDY_CHARACTERISTICS] + [c[0] for c in OUTCOMES if c[0] != "Study ID"]

def create_prompt():
    prompt = "You are an expert scientific data extractor. Extract the following information from the attached PDF study.\n"
    prompt += "Return the result as a valid JSON object where keys are the 'Column Label' and values are the extracted text/numbers. If information is strictly missing, use null.\n"
    prompt += "Do not hallucinate data. If you are unsure, extraction is better left as null.\n\n"
    
    prompt += "--- Study Characteristics ---\n"
    for label, desc in STUDY_CHARACTERISTICS:
        prompt += f"- {label}: {desc}\n"
    
    prompt += "\n--- Outcomes ---\n"
    for label, desc in OUTCOMES:
        if label == "Study ID": continue 
        prompt += f"- {label}: {desc}\n"
    
    prompt += "\nRule: Convert as many possible percentage numbers into whole numbers (as ratios/mean ± std etc.) where denominators are available.\n"
    prompt += "\nReturn ONLY the JSON object. No markdown formatting, no preamble."
    return prompt

def extract_with_api(pdf_path, prompt, model):
    print(f"[{os.path.basename(pdf_path)}] Uploading to Gemini...")
    try:
        sample_file = genai.upload_file(path=pdf_path, display_name=os.path.basename(pdf_path))
        while sample_file.state.name == "PROCESSING":
            time.sleep(1)
            sample_file = genai.get_file(sample_file.name)
            
        if sample_file.state.name == "FAILED":
            return None

        print(f"[{os.path.basename(pdf_path)}] Generating extraction...")
        generation_config = genai.GenerationConfig(response_mime_type="application/json")
        response = model.generate_content([sample_file, prompt], generation_config=generation_config)
        
        try:
            genai.delete_file(sample_file.name)
        except:
            pass

        data = json.loads(response.text)
        data['Source File'] = os.path.basename(pdf_path)
        return data
            
    except exceptions.ResourceExhausted:
         print(f"[{os.path.basename(pdf_path)}] Quota exceeded. Waiting...")
         time.sleep(30)
         return "RETRY"
    except Exception as e:
        print(f"[{os.path.basename(pdf_path)}] API Error: {e}")
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", help="Gemini API Key", required=True)
    parser.add_argument("--limit", help="Limit number of files", default=None)
    parser.add_argument("--files", help="Specific files", nargs="+", default=None)
    args = parser.parse_args()

    genai.configure(api_key=args.key)
    model = genai.GenerativeModel(MODEL_NAME)
    prompt = create_prompt()

    if args.files:
        files_to_process = [os.path.join(ARTICLES_DIR, f) for f in args.files if os.path.exists(os.path.join(ARTICLES_DIR, f))]
    else:
        files_to_process = [os.path.join(ARTICLES_DIR, f) for f in os.listdir(ARTICLES_DIR) if f.lower().endswith('.pdf')]
        
        if os.path.exists(OUTPUT_FILE):
            try:
                processed = set(pd.read_excel(OUTPUT_FILE)['Source File'].dropna().tolist())
                files_to_process = [f for f in files_to_process if os.path.basename(f) not in processed]
            except:
                pass

    if args.limit:
        files_to_process = files_to_process[:int(args.limit)]

    print(f"Starting API extraction for {len(files_to_process)} files...")

    for pdf_path in files_to_process:
        data = extract_with_api(pdf_path, prompt, model)
        if data == "RETRY":
            data = extract_with_api(pdf_path, prompt, model)
            
        if data and data != "RETRY":
            df = pd.DataFrame([data])
            for c in ALL_COLUMNS:
                if c not in df.columns: df[c] = None
            
            cols = ['Source File'] + [c for c in ALL_COLUMNS if c in df.columns]
            df = df[cols]

            if os.path.exists(OUTPUT_FILE):
                existing = pd.read_excel(OUTPUT_FILE)
                df = pd.concat([existing, df], ignore_index=True)
            
            df.to_excel(OUTPUT_FILE, index=False)
            print(f"  💾 Saved {os.path.basename(pdf_path)}")
            time.sleep(4)
        else:
            print(f"  ❌ Failed {os.path.basename(pdf_path)}")

if __name__ == "__main__":
    main()
