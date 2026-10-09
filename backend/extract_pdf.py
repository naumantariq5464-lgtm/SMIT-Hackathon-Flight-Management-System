from pypdf import PdfReader
reader = PdfReader(r'd:\SMIT Hackathon\flight_management_system_feature_list.pdf')
with open('pdf_content.txt', 'w', encoding='utf-8') as f:
    for page in reader.pages:
        f.write(page.extract_text() + '\n')
