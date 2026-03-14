"""
Cross-Stage Verification Agent

Monitors audit logs from deduplication, screening, and extraction stages.
Classifies discrepancies as MINOR or CRITICAL, generates consolidated reports,
and creates a human adjudication queue.

Outputs:
  - verification_report.xlsx      (consolidated discrepancy report)
  - human_adjudication_queue.xlsx (items requiring human review)
  - audit_trail.json              (complete trace of every decision)
"""

import os
import json
import pandas as pd
import argparse
from datetime import datetime


# Default paths for audit logs from each stage
DEDUP_LOG = "dedup_audit_log.json"
SCREENING_LOG = "screening_audit_log.json"
EXTRACTION_LOG = "extraction_audit_log.json"

# Output files
VERIFICATION_REPORT = "verification_report.xlsx"
ADJUDICATION_QUEUE = "human_adjudication_queue.xlsx"
AUDIT_TRAIL = "audit_trail.json"


def load_json_log(filepath):
    """Load a JSON audit log file."""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"  Warning: Could not read {filepath}: {e}")
        return None


def verify_deduplication(dedup_log):
    """
    Verify deduplication stage outputs.
    Checks for flagged items and low-confidence removals.
    """
    findings = []
    adjudication_items = []

    if not dedup_log:
        return findings, adjudication_items

    summary = dedup_log.get("summary", {})
    flagged = dedup_log.get("flagged_for_human_review", [])
    decisions = dedup_log.get("decisions", [])

    print(f"  Deduplication: {summary.get('total_input', 0)} input → "
          f"{summary.get('total_unique', 0)} unique, "
          f"{summary.get('total_duplicates_removed', 0)} removed, "
          f"{summary.get('total_flagged_for_review', 0)} flagged")

    # All flagged items go to human adjudication
    for item in flagged:
        findings.append({
            "Stage": "Deduplication",
            "Type": "Uncertain Match",
            "Severity": "MINOR",
            "Detail": f"Low-confidence match ({item.get('confidence', 'N/A')}) between "
                      f"'{item.get('record_title', 'N/A')[:60]}' and "
                      f"'{item.get('matched_title', 'N/A')[:60]}'",
            "Resolution": "Retained both — needs human review"
        })
        adjudication_items.append({
            "Stage": "Deduplication",
            "Action Required": "Confirm if these are duplicates or distinct records",
            "Record 1": item.get("record_title", ""),
            "Record 2": item.get("matched_title", ""),
            "Confidence": item.get("confidence", ""),
            "Method": item.get("method", ""),
            "Severity": "MINOR"
        })

    return findings, adjudication_items


def verify_screening(screening_log):
    """
    Verify screening stage outputs.
    Checks for disagreements between dual passes.
    """
    findings = []
    adjudication_items = []

    if not screening_log:
        return findings, adjudication_items

    summary = screening_log.get("summary", {})
    flagged = screening_log.get("flagged", [])
    dual_pass = screening_log.get("dual_pass", False)

    print(f"  Screening: {summary.get('total_articles', 0)} articles → "
          f"{summary.get('included', 0)} included, "
          f"{summary.get('excluded', 0)} excluded, "
          f"{summary.get('flagged_for_review', 0)} flagged")

    for item in flagged:
        severity = "CRITICAL"  # Screening disagreements are always critical
        findings.append({
            "Stage": "Screening",
            "Type": "Pass Disagreement",
            "Severity": severity,
            "Detail": f"'{item.get('Title', 'N/A')[:60]}' — "
                      f"Pass 1: {item.get('Pass1_Decision')}, "
                      f"Pass 2: {item.get('Pass2_Decision')}",
            "Resolution": "Needs human adjudication"
        })
        adjudication_items.append({
            "Stage": "Screening",
            "Action Required": "Decide Include or Exclude",
            "Article": item.get("Title", ""),
            "Key": item.get("Key", ""),
            "Pass1_Decision": item.get("Pass1_Decision", ""),
            "Pass1_Reason": item.get("Pass1_Reason", ""),
            "Pass2_Decision": item.get("Pass2_Decision", ""),
            "Pass2_Reason": item.get("Pass2_Reason", ""),
            "Severity": severity
        })

    return findings, adjudication_items


def verify_extraction(extraction_log):
    """
    Verify extraction stage outputs.
    Checks for field-level discrepancies and missing data justifications.
    """
    findings = []
    adjudication_items = []

    if not extraction_log:
        return findings, adjudication_items

    summary = extraction_log.get("summary", {})
    discrepancies = extraction_log.get("discrepancies", [])
    justifications = extraction_log.get("justifications", [])

    print(f"  Extraction: {summary.get('files_processed', 0)} files, "
          f"{summary.get('total_discrepancies', 0)} discrepancies "
          f"({summary.get('critical_discrepancies', 0)} critical), "
          f"{summary.get('justification_logs', 0)} null-field justifications")

    for disc in discrepancies:
        severity = disc.get("Severity", "MINOR")
        findings.append({
            "Stage": "Extraction",
            "Type": "Field Discrepancy",
            "Severity": severity,
            "Detail": f"{disc.get('Source File', 'N/A')} → {disc.get('Field', 'N/A')}: "
                      f"Pass 1='{str(disc.get('Pass1_Value', ''))[:40]}', "
                      f"Pass 2='{str(disc.get('Pass2_Value', ''))[:40]}'",
            "Resolution": disc.get("Resolution", "")
        })

        if severity == "CRITICAL":
            adjudication_items.append({
                "Stage": "Extraction",
                "Action Required": "Review and select correct value",
                "Source File": disc.get("Source File", ""),
                "Field": disc.get("Field", ""),
                "Pass1_Value": disc.get("Pass1_Value", ""),
                "Pass2_Value": disc.get("Pass2_Value", ""),
                "Severity": severity
            })

    # Log justifications as findings (informational)
    for just in justifications:
        findings.append({
            "Stage": "Extraction",
            "Type": "Missing Data Justification",
            "Severity": "INFO",
            "Detail": f"Field '{just.get('field', 'N/A')}': {just.get('justification', 'N/A')}",
            "Resolution": "Documented — no action needed unless data exists"
        })

    return findings, adjudication_items


def main(dedup_log_path=None, screening_log_path=None, extraction_log_path=None):
    """
    Run cross-stage verification.
    Reads audit logs from all stages and generates consolidated reports.
    """
    dedup_log_path = dedup_log_path or DEDUP_LOG
    screening_log_path = screening_log_path or SCREENING_LOG
    extraction_log_path = extraction_log_path or EXTRACTION_LOG

    print(f"\n{'='*70}")
    print("CROSS-STAGE VERIFICATION AGENT")
    print(f"{'='*70}\n")

    all_findings = []
    all_adjudication = []

    # Stage 1: Deduplication
    print("📋 Reviewing Deduplication...")
    dedup_data = load_json_log(dedup_log_path)
    if dedup_data:
        findings, adjudication = verify_deduplication(dedup_data)
        all_findings.extend(findings)
        all_adjudication.extend(adjudication)
    else:
        print("  ⚠️ No deduplication audit log found. Skipping.")

    # Stage 2: Screening
    print("📋 Reviewing Screening...")
    screening_data = load_json_log(screening_log_path)
    if screening_data:
        findings, adjudication = verify_screening(screening_data)
        all_findings.extend(findings)
        all_adjudication.extend(adjudication)
    else:
        print("  ⚠️ No screening audit log found. Skipping.")

    # Stage 3: Extraction
    print("📋 Reviewing Extraction...")
    extraction_data = load_json_log(extraction_log_path)
    if extraction_data:
        findings, adjudication = verify_extraction(extraction_data)
        all_findings.extend(findings)
        all_adjudication.extend(adjudication)
    else:
        print("  ⚠️ No extraction audit log found. Skipping.")

    # Generate Verification Report
    if all_findings:
        report_df = pd.DataFrame(all_findings)
        report_df.to_excel(VERIFICATION_REPORT, index=False)
        print(f"\n📊 Verification report saved to: {VERIFICATION_REPORT}")
    else:
        print("\n✅ No findings across any stage.")

    # Generate Human Adjudication Queue
    if all_adjudication:
        adj_df = pd.DataFrame(all_adjudication)
        adj_df.to_excel(ADJUDICATION_QUEUE, index=False)
        print(f"📋 Human adjudication queue saved to: {ADJUDICATION_QUEUE}")
    else:
        print("✅ No items requiring human adjudication.")

    # Generate Audit Trail
    n_critical = sum(1 for f in all_findings if f.get("Severity") == "CRITICAL")
    n_minor = sum(1 for f in all_findings if f.get("Severity") == "MINOR")
    n_info = sum(1 for f in all_findings if f.get("Severity") == "INFO")

    audit_trail = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_findings": len(all_findings),
            "critical": n_critical,
            "minor": n_minor,
            "informational": n_info,
            "items_for_adjudication": len(all_adjudication),
            "stages_reviewed": {
                "deduplication": dedup_data is not None,
                "screening": screening_data is not None,
                "extraction": extraction_data is not None
            }
        },
        "findings": all_findings,
        "adjudication_queue": all_adjudication
    }
    with open(AUDIT_TRAIL, 'w', encoding='utf-8') as f:
        json.dump(audit_trail, f, indent=2, ensure_ascii=False)
    print(f"📝 Audit trail saved to: {AUDIT_TRAIL}")

    # Summary
    print(f"\n{'='*60}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*60}")
    print(f"  Total findings:         {len(all_findings)}")
    print(f"    - Critical:           {n_critical}")
    print(f"    - Minor:              {n_minor}")
    print(f"    - Informational:      {n_info}")
    print(f"  Human adjudication:     {len(all_adjudication)} items")
    if n_critical > 0:
        print(f"\n  ⚠️ {n_critical} CRITICAL items require human review!")
    else:
        print(f"\n  ✅ No critical issues found.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Cross-stage verification agent for systematic review pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This agent reads audit logs from deduplication, screening, and extraction
stages, then generates consolidated verification reports and a human
adjudication queue.

Examples:
  python verification_agent.py
  python verification_agent.py --dedup path/to/dedup_audit_log.json
  python verification_agent.py --screening screening_audit_log.json --extraction extraction_audit_log.json
        """
    )
    parser.add_argument("--dedup", help=f"Path to deduplication audit log (default: {DEDUP_LOG})",
                        default=None)
    parser.add_argument("--screening", help=f"Path to screening audit log (default: {SCREENING_LOG})",
                        default=None)
    parser.add_argument("--extraction", help=f"Path to extraction audit log (default: {EXTRACTION_LOG})",
                        default=None)

    args = parser.parse_args()
    main(args.dedup, args.screening, args.extraction)
