import re
import openai
import os
import PyPDF2

# Load your OpenAI API key from an environment variable for better security
openai.api_key = os.environ.get('OPENAI_API_KEY')

if not openai.api_key:
    raise ValueError("No OpenAI API key found. Set the OPENAI_API_KEY environment variable.")

def load_book(file_path):
    """Load the book text from a PDF file."""
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        book_text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            extracted_text = page.extract_text()
            if extracted_text:  # Check if text was successfully extracted
                book_text += extracted_text
            else:
                print(f"Warning: No text extracted from page {page_num}")  # Example of handling potential issues
    return book_text

def split_into_chapters_improved(book_text):
    """Split the book text into chapters based on the "Chapter \d+:" pattern."""
    chapters = []
    current_chapter = ""
    chapter_pattern = re.compile(r"Chapter \d+:", re.IGNORECASE)

    for line in book_text.splitlines():
        if chapter_pattern.search(line):
            if current_chapter:
                chapters.append(current_chapter.strip())
            current_chapter = line + "\n"
        else:
            current_chapter += line + "\n"

    if current_chapter:
        chapters.append(current_chapter.strip())

    return chapters

def load_custom_prompt(prompt_file_path):
    """Load a custom prompt from a file."""
    with open(prompt_file_path, 'r', encoding='utf-8') as file:
        return file.read().strip()

def summarize_chapter_with_gpt(chapter_text, custom_prompt):
    """Summarize a chapter using the OpenAI GPT API."""
    # Placeholder implementation
    return f"Summary for: {chapter_text[:150]}..."

def save_summary(file_name, summary):
    """Save the summary to a text file."""
    with open(file_name, 'w', encoding='utf-8') as file:
        file.write(summary)

def combine_chapter_summaries(chapters):
    """Combine all chapter summaries into a single text."""
    combined_text = "\n\n".join(chapters)
    return combined_text

def generate_overall_summary(combined_text, chunk_size=8192):
    """Generate an overall summary of the book using the OpenAI GPT model."""
    # Placeholder implementation
    return f"Overall summary: {combined_text[:100]}..."
    
def main():
    # Update these paths with the actual paths to your PDF and prompt file on your system
    book_path = '/Users/dylanwhite/Desktop/The_Compound_Effect_-_Darren_Hardy.pdf'
    prompt_file_path = '/Users/dylanwhite/Desktop/summary_prompt.txt'

    custom_prompt = load_custom_prompt(prompt_file_path)
    book_text = load_book(book_path)
    chapters = split_into_chapters_improved(book_text)

    if not chapters:
        print("No chapters found in the book text.")
        return

    chapter_summaries = []
    for i, chapter in enumerate(chapters, 1):
        print(f"Processing Chapter {i}...")
        chapter_summary = summarize_chapter_with_gpt(chapter, custom_prompt)
        if chapter_summary is None:
            print(f"Warning: No summary generated for Chapter {i}. Skipping...")
            continue
        chapter_summaries.append(chapter_summary)
        save_summary(f"Chapter_{i}_Summary.txt", chapter_summary)
        print(f"Chapter {i} Summary saved.")

    combined_chapter_summaries = combine_chapter_summaries(chapter_summaries)
    overall_summary = generate_overall_summary(combined_chapter_summaries)
    if overall_summary is None:
        print("Warning: No overall summary generated.")
    else:
        save_summary("Overall_Summary.txt", overall_summary)
        print("Overall Summary saved.")

if __name__ == "__main__":
    main()