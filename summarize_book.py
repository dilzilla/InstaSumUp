import re
import openai
import os
import PyPDF2
import tkinter as tk
from tkinter import filedialog

# Load OpenAI API key from an environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')
if not openai.api_key:
    raise ValueError("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")

def convert_pdf_to_text(file_path):
    """Convert the entire PDF file to a single text string."""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            book_text = ""
            for page_num in range(len(pdf_reader.pages)):
                page_text = pdf_reader.pages[page_num].extract_text() or ""
                book_text += f"\n\n[Page {page_num + 1} Start]\n\n" + page_text
            return book_text
    except PyPDF2.errors.PdfReadError as e:
        print(f"Error reading PDF file: {e}")
        return None

def extract_toc(book_text):
    """Extract the table of contents from the book text using regular expressions."""
    toc_regex = r"(?:PART|CHAPTER)\s+(?:\d+|[IVXLCDM]+)(?:\s*[-:]\s*|\s+).*?"
    toc_matches = re.findall(toc_regex, book_text, re.IGNORECASE)
    toc_structure = []
    for match in toc_matches:
        if match.lower().startswith('part'):
            toc_structure.append(('part', match.strip()))
        elif match.lower().startswith('chapter'):
            toc_structure.append(('chapter', match.strip()))
    return toc_structure

def extract_sections_from_text(book_text, toc_structure):
    """Extract parts and chapters' text based on the provided TOC structure."""
    sections = {}
    for i, (section_type, section_title) in enumerate(toc_structure):
        if i < len(toc_structure) - 1:
            next_section_title = toc_structure[i + 1][1]
            section_regex = re.compile(fr"({re.escape(section_title)}.*?)(?={re.escape(next_section_title)}|\Z)", re.DOTALL | re.IGNORECASE)
        else:
            section_regex = re.compile(fr"({re.escape(section_title)}.*)", re.DOTALL | re.IGNORECASE)
        
        match = section_regex.search(book_text)
        if match:
            section_text = match.group(1).strip()
            sections[(section_type, section_title)] = section_text
        else:
            print(f"Warning: {section_type.capitalize()} '{section_title}' not found in the book text. Skipping {section_type}.")
    return sections

def summarize_text_with_gpt(text, prompt):
    """Summarize text using GPT-3.5-turbo."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.5,
            max_tokens=500,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"Failed to summarize text: {e}")
        return None

def save_summary(file_name, summary):
    """Save the summary to a text file."""
    with open(file_name, 'w', encoding='utf-8') as file:
        file.write(summary)

def combine_section_summaries(sections):
    """Combine all section summaries into a single text."""
    combined_text = "\n\n".join(sections.values())
    return combined_text

def generate_overall_summary(combined_text, overall_prompt, chunk_size=16384):
    """Generate an overall summary of the combined section summaries."""
    overall_summaries = []

    combined_chunks = [combined_text[i:i+chunk_size] for i in range(0, len(combined_text), chunk_size)]

    for i, chunk in enumerate(combined_chunks, 1):
        messages = [
            {"role": "system", "content": overall_prompt},
            {"role": "user", "content": chunk}
        ]

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.5,
            max_tokens=1000,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )

        overall_summary = response.choices[0].message['content'].strip()
        overall_summaries.append(overall_summary)
        print(f"Overall Summary Chunk {i} saved.")

    combined_overall_summary = "\n\n".join(overall_summaries)
    return combined_overall_summary

def perform_summarization(sections):
    section_prompt = "Please summarize this section, avoiding repetitive phrases like 'this text'. Focus on the main points and present them clearly. Title each page with the correct title of the section you are summarizing. Combine all of your understanding of this section into 350 words in a section called SUMMARY. Output the 10 most important points of the content in this section as a list with no more than 50 words per point into a section called MAIN POINTS:."

    section_summaries = {}
    for (section_type, section_title), section_text in sections.items():
        print(f"Summarizing {section_type}: {section_title}")
        summary = summarize_text_with_gpt(section_text, section_prompt)
        file_name = re.sub('[^A-Za-z0-9]+', '_', section_title)[:50] + "_Summary.txt"
        save_summary(file_name, summary)
        section_summaries[(section_type, section_title)] = summary
        print(f"Summary saved for {section_title}")

    combined_section_summaries = combine_section_summaries(section_summaries)

    overall_prompt = "Please provide a concise overall summary of the book, highlighting the key themes, main ideas, and significant takeaways."

    overall_summary = generate_overall_summary(combined_section_summaries, overall_prompt)
    save_summary("Overall_Summary.txt", overall_summary)
    print("Overall Summary saved.")

def select_file():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    return file_path

if __name__ == "__main__":
    book_path = select_file()

    if not book_path:
        print("No file selected. Exiting program.")
        exit(1)

    print("Converting PDF to text, please wait...")
    full_book_text = convert_pdf_to_text(book_path)
    if full_book_text is None:
        print("Failed to convert PDF to text.")
        exit(1)

    print("Extracting table of contents...")
    toc_structure = extract_toc(full_book_text)

    print("Extracting sections based on the TOC...")
    sections = extract_sections_from_text(full_book_text, toc_structure)

    perform_summarization(sections)