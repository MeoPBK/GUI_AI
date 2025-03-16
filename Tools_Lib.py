import fitz
import re
#from bs4 import BeautifulSoup

# Extract text content from a PDF file with page separation.
def extract_text_from_pdf(pdf_path):
    # Args: pdf_path (str): Path to the PDF file
        
    print(f"Extracting text from {pdf_path}...")  # Print the path of the PDF being processed
    pdf = fitz.open(pdf_path)  # Open the PDF file using PyMuPDF
    pages = []  # Initialize an empty list to store the pages with text content
    
    # Iterate over each page in the PDF
    for page_num in range(len(pdf)):
        page = pdf[page_num]  # Get the current page
        text = page.get_text()  # Extract text from the current page
        
        # Skip pages with very little text (less than 50 characters)
        if len(text.strip()) > 50:
            # Append the page text and metadata to the list
            pages.append({
                "text": text,
                "metadata": {
                    "source": pdf_path,  # Source file path
                    "page": page_num + 1  # Page number (1-based index)
                }
            })
    
    print(f"Extracted {len(pages)} pages with content")  # Print the number of pages extracted
    return pages  # Return the list of pages with text content and metadata #         List[Dict]: List of pages with text content and metadata

def extract_info_fromHTML(html):
    soup = BeautifulSoup(html, "html.parser")
    paragraphs = [p.get_text() for p in soup.find_all("p")]
    print("UKULELE aiaiaia ".join(paragraphs))
    return " ".join(paragraphs)

def clean_response(response: str)->str: 
        # Usa una regex per trovare e rimuovere tutto ciò che è tra <think> e </think>
        cleaned_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        return cleaned_response.strip()  # Rimuove spazi bianchi extra