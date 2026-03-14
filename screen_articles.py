import json
import csv

def screen_articles(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    results = []
    for art in articles:
        title = art.get('title', '').upper()
        abstract = art.get('abstract', '').upper()
        
        # Exact GCT keywords
        gct_keywords = ["GIANT CELL TUMOR", "GIANT-CELL TUMOR", "GIANT CELL TUMOUR", "GIANT-CELL TUMOUR", "OSTEOCLASTOMA"]
        
        # Check if GCT is the main topic (usually in title)
        is_gct_in_title = any(x in title for x in gct_keywords)
        is_gct_in_abstract = any(x in abstract for x in gct_keywords)
        
        # Check for other competing tumor types in title
        competing_diagnosis = any(x in title for x in ["OSTEOBLASTOMA", "ANEURYSMAL BONE CYST", "METASTASIS", "METASTASES", "LYMPHOMA", "CHORDOMA", "PLASMACYTOMA"])
        # Exception: if title has GCT AND metastases (like case 1)
        if is_gct_in_title and "METASTAS" in title:
            competing_diagnosis = False
            
        # Refined GCT check
        is_gct = is_gct_in_title or (is_gct_in_abstract and not competing_diagnosis)
        
        # Cervical Spine check
        cervical_keywords = ["CERVICAL", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "ATLANTOAXIAL"]
        is_cervical_in_title = any(x in title for x in cervical_keywords)
        is_cervical_in_abstract = any(x in abstract for x in cervical_keywords)
        is_cervical = is_cervical_in_title or is_cervical_in_abstract

        # ONLY BONE GCT
        # Exclude Synovial or Tenosynovial types
        is_non_bone = any(x in title for x in ["SYNOVIAL", "TENOSYNOVIAL"]) or \
                       any(x in abstract for x in ["SYNOVIAL", "TENOSYNOVIAL"])
        
        # Exclusion criteria - Types
        is_review = any(x in title for x in ["SYSTEMATIC REVIEW", "META-ANALYSIS", "NARRATIVE REVIEW", "LITERATURE REVIEW"]) or \
                    (title.startswith("REVIEW") or " REVIEW " in title or title.endswith("REVIEW"))
        
        # Decision logic
        decision = "Exclude"
        reason = ""
        
        if not is_gct:
            reason = "Not GCT/Osteoclastoma or primary topic is another tumor type"
        elif is_non_bone:
            reason = "Non-bone origin (Synovial/Tenosynovial)"
        elif not is_cervical:
            reason = "Not Cervical Spine"
        elif is_review:
            reason = "Review/Meta-Analysis/Systematic Review"
        else:
            decision = "Include"
            reason = "Original article on Cervical Bone GCT/Osteoclastoma"

        results.append({
            "Key": art['key'],
            "Title": art['title'],
            "Decision": decision,
            "Reason": reason
        })
    
    return results

if __name__ == "__main__":
    results = screen_articles('parsed_articles.json')
    with open('screening_results.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["Key", "Title", "Decision", "Reason"])
        writer.writeheader()
        writer.writerows(results)
    
    print("Screening complete. Results saved to screening_results.csv")
    for res in results:
        print(f"[{res['Decision']}] {res['Title'][:50]}... - {res['Reason']}")
