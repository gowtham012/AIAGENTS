import PyPDF2
import re

def extract_all_keywords(pdf_path):
    """
    Extract all keywords from the "Technical Proficiencies" section of the resume.
    It captures text between "Technical Proficiencies" and "Professional Experience",
    then extracts lines formatted as "Category: item1, item2, ..." and splits them into individual keywords.
    """
    # Read the entire PDF text.
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    
    # Extract the block of text from "Technical Proficiencies" until "Professional Experience"
    tech_block_match = re.search(r"Technical Proficiencies(.*?)Professional Experience", text, re.DOTALL | re.IGNORECASE)
    if tech_block_match:
        tech_block = tech_block_match.group(1)
    else:
        tech_block = text  # Fallback: use the entire text if the section boundaries aren't found.
    
    # Use a regex pattern to capture each category and its associated list.
    # For example: "Languages: Python, Java, C++, C#, Solidity, Shell Scripting, HTML, CSS, JavaScript, TypeScript, SQL"
    pattern = r"([\w\s&/()\-]+):\s*([^\n]+)"
    matches = re.findall(pattern, tech_block)
    
    keywords = set()
    for category, items in matches:
        # Split the items by commas or semicolons.
        for item in re.split(r",|;", items):
            kw = item.strip()
            if kw:
                keywords.add(kw)
    
    return sorted(keywords)

if __name__ == "__main__":
    pdf_path = "gowtham1.pdf"
    all_keywords = extract_all_keywords(pdf_path)
    print("All extracted keywords from Technical Proficiencies:")
    for kw in all_keywords:
        print(kw)
    print(f"Total keywords extracted: {len(all_keywords)}")