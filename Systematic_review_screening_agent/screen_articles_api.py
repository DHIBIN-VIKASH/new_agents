"""
Dual-Pass Screening Agent using Gemini API

Implements the dual-pass screening strategy from the paper:
  1. Pass 1: Screen all articles using Gemini API with criteria
  2. Pass 2: Screen all articles again independently (no prior context)
  3. Finalize only when both passes agree
  4. Articles with disagreement are flagged for human review
  
Outputs:
  - screening_results.csv          (finalized decisions)
  - screening_flagged.csv          (disagreements for human review)
  - screening_audit_log.json       (all decisions, reasoning, pass comparison)
"""

import os
import json
import csv
import time
import argparse
from datetime import datetime
from pathlib import Path

try:
    import google.generativeai as genai
    from google.api_core import exceptions as gapi_exceptions
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

from criteria_parser import parse_criteria


# Configuration
MODEL_NAME = "models/gemini-2.0-flash"
DEFAULT_OUTPUT = "screening_results.csv"
FLAGGED_OUTPUT = "screening_flagged.csv"
AUDIT_LOG = "screening_audit_log.json"


def create_screening_prompt(criteria: dict, article: dict) -> str:
    """Create a prompt for Gemini to screen a single article."""
    prompt = """You are an expert systematic review screener. Based on the criteria below, determine whether the following article should be INCLUDED or EXCLUDED from the systematic review.

### SCREENING CRITERIA ###
"""
    if criteria.get('description'):
        prompt += f"Description: {criteria['description']}\n\n"

    if criteria.get('inclusion'):
        prompt += "**Inclusion Criteria:**\n"
        for category, keywords in criteria['inclusion'].items():
            prompt += f"  - {category}: {', '.join(keywords)}\n"
        prompt += "\n"

    if criteria.get('exclusion'):
        prompt += "**Exclusion Criteria:**\n"
        for category, keywords in criteria['exclusion'].items():
            prompt += f"  - {category}: {', '.join(keywords)}\n"
        prompt += "\n"

    if criteria.get('rules'):
        prompt += "**Additional Rules:**\n"
        for rule_name, rule_val in criteria['rules'].items():
            prompt += f"  - {rule_name}: {rule_val}\n"
        prompt += "\n"

    prompt += f"""### ARTICLE TO SCREEN ###
Title: {article.get('title', 'N/A')}
Abstract: {article.get('abstract', 'N/A')}

### INSTRUCTIONS ###
1. Carefully evaluate the title and abstract against ALL inclusion AND exclusion criteria.
2. An article must meet ALL inclusion criteria and NONE of the exclusion criteria to be included.
3. If the abstract is missing or empty, make a conservative decision based on the title alone — lean towards INCLUDE if the title is relevant.
4. Return your decision as a JSON object with EXACTLY this format:

{{"decision": "Include" or "Exclude", "reason": "Detailed explanation of why this article was included or excluded, referencing specific criteria"}}

Return ONLY the JSON object, no other text."""

    return prompt


def screen_single_article(model, article: dict, criteria: dict, max_retries=3) -> dict:
    """Screen a single article using the Gemini API. Returns decision dict."""
    prompt = create_screening_prompt(criteria, article)

    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.1  # Low temperature for consistency
                )
            )

            text = response.text.strip()
            # Clean markdown if present
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            data = json.loads(text)
            return {
                "decision": data.get("decision", "Exclude"),
                "reason": data.get("reason", "No reason provided")
            }

        except gapi_exceptions.ResourceExhausted:
            print(f"    Rate limited. Waiting 30s... (attempt {attempt + 1})")
            time.sleep(30)
        except json.JSONDecodeError:
            print(f"    JSON parse error. Retrying... (attempt {attempt + 1})")
            time.sleep(2)
        except Exception as e:
            print(f"    API error: {e}. Retrying... (attempt {attempt + 1})")
            time.sleep(5)

    return {"decision": "Exclude", "reason": "API_ERROR: Failed after retries"}


def run_screening_pass(model, articles: list, criteria: dict, pass_label: str) -> list:
    """Run a single screening pass over all articles."""
    print(f"\n{'='*60}")
    print(f"  SCREENING {pass_label}")
    print(f"{'='*60}")

    results = []
    for i, article in enumerate(articles):
        key = article.get('key', f'article_{i}')
        title_short = article.get('title', 'N/A')[:60]
        print(f"  [{i+1}/{len(articles)}] {title_short}...")

        result = screen_single_article(model, article, criteria)
        result['key'] = key
        result['title'] = article.get('title', '')
        results.append(result)

        # Rate limit safety: ~4s between requests for 15 RPM
        time.sleep(4)

    included = sum(1 for r in results if r['decision'] == 'Include')
    excluded = sum(1 for r in results if r['decision'] == 'Exclude')
    print(f"\n  {pass_label} Results: {included} included, {excluded} excluded")

    return results


def compare_passes(pass1_results: list, pass2_results: list) -> tuple:
    """
    Compare two screening passes. Returns (finalized, flagged).
    Only finalize when both passes agree. Disagreements are flagged.
    """
    # Index pass2 by key for lookup
    pass2_by_key = {r['key']: r for r in pass2_results}

    finalized = []
    flagged = []

    for p1 in pass1_results:
        key = p1['key']
        p2 = pass2_by_key.get(key)

        if not p2:
            # Pass 2 missing this article — flag it
            flagged.append({
                "Key": key,
                "Title": p1['title'],
                "Pass1_Decision": p1['decision'],
                "Pass1_Reason": p1['reason'],
                "Pass2_Decision": "MISSING",
                "Pass2_Reason": "Not processed in Pass 2",
                "Flag_Reason": "Missing in Pass 2"
            })
            continue

        if p1['decision'] == p2['decision']:
            # Agreement — finalize
            finalized.append({
                "Key": key,
                "Title": p1['title'],
                "Decision": p1['decision'],
                "Reason": f"[Pass 1] {p1['reason']} | [Pass 2] {p2['reason']}"
            })
        else:
            # Disagreement — flag for human review
            flagged.append({
                "Key": key,
                "Title": p1['title'],
                "Pass1_Decision": p1['decision'],
                "Pass1_Reason": p1['reason'],
                "Pass2_Decision": p2['decision'],
                "Pass2_Reason": p2['reason'],
                "Flag_Reason": "Passes disagreed"
            })

    return finalized, flagged


def main(api_key: str, articles_path: str, criteria_file: str,
         output_file: str = None, single_pass: bool = False):
    """
    Main dual-pass screening function.

    Args:
        api_key: Gemini API key
        articles_path: Path to JSON file of parsed articles
        criteria_file: Path to screening criteria file (.txt, .docx, .json)
        output_file: Output path for finalized results
        single_pass: If True, run only one pass (skip dual-pass comparison)
    """
    if not HAS_GENAI:
        print("Error: google-generativeai package not installed.")
        print("Install with: pip install google-generativeai")
        return

    # Configure API
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME)

    # Parse criteria
    print(f"\n{'='*70}")
    print("DUAL-PASS SCREENING AGENT")
    print(f"{'='*70}\n")

    print(f"📋 Parsing criteria from: {criteria_file}")
    try:
        criteria = parse_criteria(criteria_file)
        print(f"✅ Criteria parsed successfully!")
    except Exception as e:
        print(f"❌ Error parsing criteria: {e}")
        return

    # Load articles
    print(f"📄 Loading articles from: {articles_path}")
    try:
        with open(articles_path, 'r', encoding='utf-8') as f:
            articles = json.load(f)
        print(f"✅ Loaded {len(articles)} articles")
    except Exception as e:
        print(f"❌ Error loading articles: {e}")
        return

    if output_file is None:
        output_file = DEFAULT_OUTPUT

    # PASS 1
    pass1_results = run_screening_pass(model, articles, criteria, "PASS 1")

    if single_pass:
        # Single pass mode — just save directly
        finalized = [{
            "Key": r['key'], "Title": r['title'],
            "Decision": r['decision'], "Reason": r['reason']
        } for r in pass1_results]
        flagged = []
        print("\n⚠️ Single-pass mode: skipping Pass 2 comparison")
    else:
        # PASS 2 (independent, no context from Pass 1)
        print("\n⏳ Waiting 10 seconds before Pass 2 to ensure independence...")
        time.sleep(10)
        pass2_results = run_screening_pass(model, articles, criteria, "PASS 2")

        # Compare
        print(f"\n{'='*60}")
        print("  COMPARING PASSES")
        print(f"{'='*60}")
        finalized, flagged = compare_passes(pass1_results, pass2_results)

    # Save finalized results
    if finalized:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["Key", "Title", "Decision", "Reason"])
            writer.writeheader()
            writer.writerows(finalized)
        print(f"\n✅ Finalized results saved to: {output_file}")
    else:
        print("\n⚠️ No finalized results to save.")

    # Save flagged results
    if flagged:
        with open(FLAGGED_OUTPUT, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "Key", "Title", "Pass1_Decision", "Pass1_Reason",
                "Pass2_Decision", "Pass2_Reason", "Flag_Reason"
            ])
            writer.writeheader()
            writer.writerows(flagged)
        print(f"⚠️ Flagged results saved to: {FLAGGED_OUTPUT}")

    # Save audit log
    included = sum(1 for r in finalized if r['Decision'] == 'Include')
    excluded = sum(1 for r in finalized if r['Decision'] == 'Exclude')

    audit = {
        "timestamp": datetime.now().isoformat(),
        "criteria_file": criteria_file,
        "articles_file": articles_path,
        "model": MODEL_NAME,
        "dual_pass": not single_pass,
        "summary": {
            "total_articles": len(articles),
            "finalized": len(finalized),
            "included": included,
            "excluded": excluded,
            "flagged_for_review": len(flagged)
        },
        "pass1_results": pass1_results if not single_pass else None,
        "pass2_results": pass2_results if not single_pass else None,
        "finalized": finalized,
        "flagged": flagged
    }
    with open(AUDIT_LOG, 'w', encoding='utf-8') as f:
        json.dump(audit, f, indent=2, ensure_ascii=False)
    print(f"📝 Audit log saved to: {AUDIT_LOG}")

    # Final summary
    print(f"\n{'='*60}")
    print("  SCREENING SUMMARY")
    print(f"{'='*60}")
    print(f"  Total articles:       {len(articles)}")
    print(f"  Finalized:            {len(finalized)}")
    print(f"    - Included:         {included}")
    print(f"    - Excluded:         {excluded}")
    print(f"  Flagged for review:   {len(flagged)}")
    if not single_pass:
        agreement_rate = len(finalized) / len(articles) * 100 if articles else 0
        print(f"  Agreement rate:       {agreement_rate:.1f}%")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Dual-pass article screening using Gemini API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python screen_articles_api.py --key YOUR_KEY criteria.txt articles.json
  python screen_articles_api.py --key YOUR_KEY criteria.txt articles.json --single-pass
        """
    )
    parser.add_argument("criteria_file", help="Path to criteria file (.txt, .docx, .json)")
    parser.add_argument("articles_file", help="Path to parsed articles JSON file")
    parser.add_argument("--key", help="Gemini API Key", required=True)
    parser.add_argument("--output", help=f"Output file (default: {DEFAULT_OUTPUT})", default=None)
    parser.add_argument("--single-pass", action="store_true",
                        help="Run only one pass (skip dual-pass comparison)")

    args = parser.parse_args()
    main(args.key, args.articles_file, args.criteria_file, args.output, args.single_pass)
