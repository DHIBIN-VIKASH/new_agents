
import os
import subprocess
import pandas as pd
import argparse
import time

# Configuration
EXTRACTOR_SCRIPT = 'gemini_extractor.py'
VALIDATION_SCRIPT = 'validation_agent.py'
DISCREPANCY_FILE = 'validation_discrepancies.xlsx'
OUTPUT_FILE = 'extracted_studies.xlsx'
ARTICLES_DIR = 'Articles'
HEALING_REPORT = 'healing_comparison_report.xlsx'

def run_script(script_name, args=[]):
    """Runs a python script as a subprocess."""
    print(f"\n>>> Running {script_name} with args: {args}...")
    cmd = ['python', script_name] + args
    try:
        # We use subprocess.run so we can see the output in real-time if possible
        # or at least wait for it to finish.
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}: {e}")
        return False
    return True

def get_failed_files():
    """Reads the discrepancy log and returns a list of files that failed validation."""
    if not os.path.exists(DISCREPANCY_FILE):
        return []
    
    df = pd.read_excel(DISCREPANCY_FILE)
    if 'Source File' not in df.columns or 'Status' not in df.columns:
        return []
    
    # Get unique filenames where Status is FAIL
    failed_files = df[df['Status'] == 'FAIL']['Source File'].unique().tolist()
    return [str(f) for f in failed_files if pd.notnull(f)]

def cleanup_failed_entries(failed_files):
    """Removes the failed entries from the main output file and returns them for comparison."""
    if not os.path.exists(OUTPUT_FILE) or not failed_files:
        return None
    
    df = pd.read_excel(OUTPUT_FILE)
    # Capture the "Before" state
    failed_rows = df[df['Source File'].isin(failed_files)].copy()
    
    # Remove rows where Source File is in failed_files
    initial_len = len(df)
    df = df[~df['Source File'].isin(failed_files)]
    
    if len(df) < initial_len:
        print(f"Cleaned up {initial_len - len(df)} failed entries from {OUTPUT_FILE} to prepare for re-extraction.")
        df.to_excel(OUTPUT_FILE, index=False)
    
    return failed_rows

def generate_healing_report(before_df, current_output_file, failed_files):
    """Compares the old failed data with the new re-extracted data and saves a report."""
    if before_df is None or before_df.empty or not os.path.exists(current_output_file):
        return

    after_df = pd.read_excel(current_output_file)
    after_df = after_df[after_df['Source File'].isin(failed_files)]
    
    comparison_data = []
    
    # Ensure both have Source File as index for easier lookup
    before_df = before_df.set_index('Source File')
    after_df = after_df.set_index('Source File')
    
    for filename in failed_files:
        if filename in before_df.index and filename in after_df.index:
            old_row = before_df.loc[[filename]].iloc[0]
            new_row = after_df.loc[[filename]].iloc[0]
            
            # Compare all columns common to both
            common_cols = [c for c in before_df.columns if c in after_df.columns and c not in ['Result', 'Sl.no']]
            
            for col in common_cols:
                old_val = str(old_row[col]) if pd.notnull(old_row[col]) else "NULL"
                new_val = str(new_row[col]) if pd.notnull(new_row[col]) else "NULL"
                
                if old_val != new_val:
                    comparison_data.append({
                        'Article': filename,
                        'Field': col,
                        'Original Value': old_val,
                        'Healed Value': new_val,
                        'Status': 'FIXED'
                    })
    
    if comparison_data:
        report_df = pd.DataFrame(comparison_data)
        report_df.to_excel(HEALING_REPORT, index=False)
        print(f"Detailed healing report generated: {HEALING_REPORT}")
    else:
        print("No changes detected during healing pass.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--browser", default="chrome", help="Browser to use")
    parser.add_argument("--limit", default=None, help="Limit the number of articles to process")
    args = parser.parse_args()

    limit_args = ['--limit', args.limit] if args.limit else []

    # Clear previous logs to ensure we only heal NEW failures
    if os.path.exists(DISCREPANCY_FILE):
        try:
            os.remove(DISCREPANCY_FILE)
            print(f"Cleared old log: {DISCREPANCY_FILE}")
        except:
            pass
    
    # PHASE 1: Initial Validation
    print("\n=== PHASE 1: INITIAL VALIDATION ===")
    run_script(VALIDATION_SCRIPT, ['--browser', args.browser] + limit_args)
    
    # PHASE 2: Self-Healing Loop
    print("\n=== PHASE 2: SELF-HEALING (RE-EXTRACT FAILURES) ===")
    failed_files = get_failed_files()
    
    if not failed_files:
        print("No validation failures found. Pipeline complete!")
        # Final Log even if no failures
        print("\n" + "="*30)
        print("         FINAL LOG")
        print("="*30)
        print("Status: SUCCESS")
        print("Files Processed: " + (args.limit if args.limit else "All"))
        print("Discrepancies: 0")
        print("="*30)
        return

    print(f"Found {len(failed_files)} files with discrepancies: {failed_files}")
    
    # Prepare for re-extraction by removing old failed data and capturing a snapshot
    before_healing_snapshot = cleanup_failed_entries(failed_files)
    
    print(f"Re-triggering extraction for {len(failed_files)} files...")
    run_script(EXTRACTOR_SCRIPT, ['--browser', args.browser, '--files'] + failed_files)
    
    # PHASE 3: Final Validation Check
    print("\n=== PHASE 3: FINAL VALIDATION OF HEALED DATA ===")
    run_script(VALIDATION_SCRIPT, ['--browser', args.browser, '--files'] + failed_files)
    
    # Generate Comparison Report
    generate_healing_report(before_healing_snapshot, OUTPUT_FILE, failed_files)
    
    print("\nMaster Orchestration Complete.")
    
    # FINAL LOG
    print("\n" + "="*30)
    print("         FINAL LOG")
    print("="*30)
    print("Status: COMPLETED")
    print("Initial Failures: " + str(len(failed_files)))
    print("Healing Attempted: YES")
    
    if os.path.exists(HEALING_REPORT):
        print(f"Changes Logged: {HEALING_REPORT}")
    else:
        print("Changes Logged: None (No data diffs found)")
        
    print(f"Validation Log: {DISCREPANCY_FILE}")
    print("="*30)

if __name__ == "__main__":
    main()
