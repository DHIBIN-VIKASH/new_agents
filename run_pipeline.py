"""
Unified Pipeline Orchestrator for Systematic Review Agents

Runs the complete multi-agent pipeline:
  Phase 1: Deduplication  → removes duplicate records
  Phase 2: Screening      → dual-pass title/abstract screening via Gemini API
  Phase 3: Extraction     → dual-pass structured data extraction via Gemini API
  Phase 4: Verification   → cross-stage verification and audit trail

Usage:
  python run_pipeline.py --key YOUR_GEMINI_API_KEY --criteria criteria.txt --template template.docx
  python run_pipeline.py --key YOUR_KEY --phase extraction --template template.docx
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


# Agent directories
DEDUP_DIR = os.path.join(os.path.dirname(__file__), "Systematic_review_DeDuplication_agent")
SCREENING_DIR = os.path.join(os.path.dirname(__file__), "Systematic_review_screening_agent")
EXTRACTION_DIR = os.path.join(os.path.dirname(__file__), "Systematic_review_extraction_agent")
VERIFICATION_DIR = os.path.join(os.path.dirname(__file__), "Sys_review_extraction_validation_agent")


def run_agent(script_path, args=None, cwd=None):
    """Run an agent script as a subprocess."""
    if args is None:
        args = []
    cmd = [sys.executable, script_path] + args
    print(f"\n>>> Running: {' '.join(cmd)}")
    if cwd:
        print(f"    Working directory: {cwd}")
    try:
        result = subprocess.run(cmd, check=True, cwd=cwd)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Agent failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Script not found: {script_path}")
        return False


def phase_deduplication(working_dir):
    """Phase 1: Run deduplication agent."""
    print(f"\n{'='*70}")
    print("PHASE 1: DEDUPLICATION")
    print(f"{'='*70}")

    script = os.path.join(DEDUP_DIR, "deduplicate_files.py")
    # Dedup agent runs in the working directory where the input files are
    success = run_agent(script, cwd=working_dir)

    if success:
        # Check if audit log was created
        audit_path = os.path.join(working_dir, "dedup_audit_log.json")
        if os.path.exists(audit_path):
            print(f"✅ Deduplication complete. Audit log: {audit_path}")
        else:
            print("⚠️ Deduplication finished but no audit log found.")
    return success


def phase_screening(api_key, criteria_file, articles_file, single_pass=False):
    """Phase 2: Run dual-pass screening agent."""
    print(f"\n{'='*70}")
    print("PHASE 2: TITLE & ABSTRACT SCREENING")
    print(f"{'='*70}")

    script = os.path.join(SCREENING_DIR, "screen_articles_api.py")
    args = [
        criteria_file,
        articles_file,
        "--key", api_key
    ]
    if single_pass:
        args.append("--single-pass")

    success = run_agent(script, args, cwd=SCREENING_DIR)
    return success


def phase_extraction(api_key, template_file, limit=None, single_pass=False):
    """Phase 3: Run dual-pass extraction agent."""
    print(f"\n{'='*70}")
    print("PHASE 3: STRUCTURED DATA EXTRACTION")
    print(f"{'='*70}")

    script = os.path.join(EXTRACTION_DIR, "gemini_api_extractor.py")
    args = ["--key", api_key, "--template", template_file]
    if limit:
        args.extend(["--limit", str(limit)])
    if single_pass:
        args.append("--single-pass")

    success = run_agent(script, args, cwd=EXTRACTION_DIR)
    return success


def phase_verification(dedup_log=None, screening_log=None, extraction_log=None):
    """Phase 4: Run cross-stage verification agent."""
    print(f"\n{'='*70}")
    print("PHASE 4: CROSS-STAGE VERIFICATION")
    print(f"{'='*70}")

    script = os.path.join(VERIFICATION_DIR, "verification_agent.py")
    args = []
    if dedup_log:
        args.extend(["--dedup", dedup_log])
    if screening_log:
        args.extend(["--screening", screening_log])
    if extraction_log:
        args.extend(["--extraction", extraction_log])

    success = run_agent(script, args, cwd=VERIFICATION_DIR)
    return success


def main():
    parser = argparse.ArgumentParser(
        description="Unified Systematic Review Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This orchestrator runs the complete multi-agent pipeline for systematic reviews.

Full pipeline:
  python run_pipeline.py --key YOUR_KEY --criteria criteria.txt --articles articles.json --template template.docx

Individual phases:
  python run_pipeline.py --phase dedup --working-dir ./my_review
  python run_pipeline.py --phase screening --key YOUR_KEY --criteria criteria.txt --articles articles.json
  python run_pipeline.py --phase extraction --key YOUR_KEY --template template.docx
  python run_pipeline.py --phase verification

Pipeline order: dedup → screening → extraction → verification
        """
    )

    # General arguments
    parser.add_argument("--key", help="Gemini API Key (required for screening and extraction)")
    parser.add_argument("--phase", help="Run specific phase only (dedup, screening, extraction, verification)",
                        choices=["dedup", "screening", "extraction", "verification"], default=None)
    parser.add_argument("--single-pass", action="store_true",
                        help="Use single-pass mode (skip dual-pass comparison)")

    # Deduplication arguments
    parser.add_argument("--working-dir", help="Working directory for deduplication (where input files are)",
                        default=".")

    # Screening arguments
    parser.add_argument("--criteria", help="Path to screening criteria file (.txt, .docx, .json)")
    parser.add_argument("--articles", help="Path to parsed articles JSON file")

    # Extraction arguments
    parser.add_argument("--template", help="Path to extraction template file (.docx or .xlsx)")
    parser.add_argument("--limit", help="Limit number of files for extraction", default=None)

    # Verification arguments
    parser.add_argument("--dedup-log", help="Path to deduplication audit log", default=None)
    parser.add_argument("--screening-log", help="Path to screening audit log", default=None)
    parser.add_argument("--extraction-log", help="Path to extraction audit log", default=None)

    args = parser.parse_args()

    print(f"\n{'='*70}")
    print("SYSTEMATIC REVIEW - MULTI-AGENT PIPELINE")
    print(f"{'='*70}")
    print(f"Mode: {'Single phase (' + args.phase + ')' if args.phase else 'Full pipeline'}")
    print(f"Dual-pass: {'No (single-pass)' if args.single_pass else 'Yes'}")

    # Run specific phase or full pipeline
    if args.phase == "dedup" or args.phase is None:
        phase_deduplication(args.working_dir)
        if args.phase == "dedup":
            return

    if args.phase == "screening" or args.phase is None:
        if not args.key:
            print("❌ Gemini API key required for screening (--key)")
            return
        if not args.criteria:
            print("❌ Criteria file required for screening (--criteria)")
            return
        if not args.articles:
            print("❌ Articles JSON file required for screening (--articles)")
            return
        phase_screening(args.key, args.criteria, args.articles, args.single_pass)
        if args.phase == "screening":
            return

    if args.phase == "extraction" or args.phase is None:
        if not args.key:
            print("❌ Gemini API key required for extraction (--key)")
            return
        if not args.template:
            print("❌ Template file required for extraction (--template)")
            return
        phase_extraction(args.key, args.template, args.limit, args.single_pass)
        if args.phase == "extraction":
            return

    if args.phase == "verification" or args.phase is None:
        phase_verification(args.dedup_log, args.screening_log, args.extraction_log)

    if args.phase is None:
        print(f"\n{'='*70}")
        print("PIPELINE COMPLETE")
        print(f"{'='*70}")
        print("\nAll phases executed. Review the verification report for any")
        print("items requiring human adjudication.")
        print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
