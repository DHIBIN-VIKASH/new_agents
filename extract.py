import docx

def parse_docx(filename):
    doc = docx.Document(filename)
    text = [p.text for p in doc.paragraphs]
    with open('doc_text.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(text))

parse_docx('Agentic AI Updated.docx')
