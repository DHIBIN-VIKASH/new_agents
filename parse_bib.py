import re
import json
import os

def parse_bib(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by entries
    entries = re.split(r'@article\{', content)[1:]
    parsed_entries = []
    
    for entry in entries:
        lines = entry.split('\n')
        key = lines[0].strip().rstrip(',')
        
        entry_data = {'key': key}
        
        # Simple regex for fields
        fields = ['title', 'abstract', 'journal', 'year', 'author', 'doi']
        for field in fields:
            match = re.search(rf'{field}=\{{(.*?)\}}', entry, re.DOTALL | re.IGNORECASE)
            if match:
                entry_data[field] = match.group(1).strip().replace('\n', ' ')
            else:
                entry_data[field] = ""
        
        parsed_entries.append(entry_data)
    
    return parsed_entries

if __name__ == "__main__":
    file_path = 'articles.bib'
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
    else:
        data = parse_bib(file_path)
        with open('parsed_articles.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"Parsed {len(data)} articles saved to parsed_articles.json")
