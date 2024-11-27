import fitz  # PyMuPDF
import os
import tempfile
import subprocess
import re
def get_pdf_directory(directory_path=None):
    print('inside get pdf directory')
    """
    Returns the PDF directory path. Uses a default path if none is provided.
    """
    # default_directory = "C:/Users/dell/Documents/Data Extraction & Modeling/"
    print(directory_path,"skjahfjdgj")
    return directory_path 
# Define color mapping
color_map = {
    'yellow': (1, 1, 0),  # RGB for yellow
    'cyan': (0, 1, 1),    # RGB for cyan
}

def open_pdf_document(pdf_file_path):
    """Open the specified PDF file."""
    if not os.path.exists(pdf_file_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_file_path}")
    return fitz.open(pdf_file_path)

def extract_page_and_text(pdf_doc, page_idx):
    """Extract the specified page and its lines of text."""
    page_obj = pdf_doc.load_page(page_idx - 1)  # 0-based page index
    page_text_lines = page_obj.get_text("text").splitlines()
    return page_obj, page_text_lines

def highlight_full_sentence(page_obj, line_text, highlight_color):
    """Highlights the entire bounding box for the specified line text."""
    # Extract structured text
    text_data = page_obj.get_text("dict")
    blocks = text_data.get("blocks", [])

    for block in blocks:
        for line in block.get("lines", []):
            full_line_text = "".join([span["text"] for span in line.get("spans", [])]).strip()
            if line_text.strip() == full_line_text:
                # Combine bounding boxes of all spans in the line
                full_line_rects = [span["bbox"] for span in line.get("spans", [])]
                for rect in full_line_rects:
                    highlight = page_obj.add_highlight_annot(fitz.Rect(rect))
                    highlight.set_colors(stroke=highlight_color)
                    highlight.update()
                return  # Exit after highlighting the line to avoid duplicates

def highlight_lines_and_keywords(page_obj, page_text_lines, start_idx, end_idx, search_word, line_highlight_color='yellow', word_highlight_color='cyan'):
    line_color = color_map.get(line_highlight_color, (1, 1, 0))
    word_color = color_map.get(word_highlight_color, (0, 1, 1))

    # Highlight specified lines
    for idx in range(start_idx, end_idx + 1):
        if 1 <= idx <= len(page_text_lines):
            line = page_text_lines[idx - 1].strip()
            print(f"Highlighting line: {line}")
            highlight_full_sentence(page_obj, line, line_color)  # Highlight full line

    # Highlight the search word within the lines
    if search_word:
        for idx in range(start_idx, end_idx + 1):
            if 1 <= idx <= len(page_text_lines):
                line = page_text_lines[idx - 1].strip()
                if search_word in line:
                    # Only highlight the search word within the line, not the whole line
                    highlight_word_in_line(page_obj, line, search_word, word_color)  # Highlight word in line

# def highlight_lines_and_keywords(page_obj, page_text_lines, start_idx, end_idx, search_word, line_highlight_color='yellow', word_highlight_color='cyan'):
#     line_color = color_map.get(line_highlight_color, (1, 1, 0))
#     word_color = color_map.get(word_highlight_color, (0, 1, 1))

#     # Highlight specified lines
#     for idx in range(start_idx, end_idx + 1):
#         if 1 <= idx <= len(page_text_lines):
#             line = page_text_lines[idx - 1].strip()
#             print(f"Highlighting line: {line}")
#             highlight_full_sentence(page_obj, line, line_color)  # Use Approach 1
#         else:
#             print(f"Line {idx} is out of range for this page.")
    
#     # Highlight the search word within the lines
#     if search_word:
#         for idx in range(start_idx, end_idx + 1):
#             if 1 <= idx <= len(page_text_lines):
#                 line = page_text_lines[idx - 1].strip()
#                 if search_word in line:
                    # merge_and_highlight(page_obj, search_word, word_color)  # Use Approach 2
def merge_and_highlight(page_obj, phrase_to_highlight, highlight_color):
    """
    Highlights the exact phrase, even if it is fragmented across multiple spans.
    """
    # Clean up the phrase by removing any extra spaces or invisible characters
    phrase_to_highlight = re.sub(r'\s+', ' ', phrase_to_highlight).strip()  # Replace multiple spaces with single
    phrase_to_highlight = re.sub(r'[^\x00-\x7F]+', '', phrase_to_highlight)  # Remove non-ASCII characters

    # Search for the phrase in the PDF document
    matches = page_obj.search_for(phrase_to_highlight)

    if matches:
        for match in matches:
            highlight = page_obj.add_highlight_annot(fitz.Rect(match))
            highlight.set_colors(stroke=highlight_color)
            highlight.update()
        print(f"Highlighted: {phrase_to_highlight}")
    else:
        print(f"No exact matches found for '{phrase_to_highlight}'.")

def highlight_line_with_spans(page_obj, line_text, highlight_color):
    """Highlights all spans in a line to cover fragmented sentences."""
    text_data = page_obj.get_text("dict")
    blocks = text_data.get("blocks", [])
    
    for block in blocks:
        for line in block.get("lines", []):
            full_line_text = "".join([span["text"] for span in line.get("spans", [])]).strip()
            if line_text in full_line_text:
                # Highlight each span in the line
                for span in line.get("spans", []):
                    highlight = page_obj.add_highlight_annot(fitz.Rect(span["bbox"]))
                    highlight.set_colors(stroke=highlight_color)
                    highlight.update()
                return

def highlight_phrase(page_obj, phrase_to_highlight, highlight_color, is_line_highlight):
    """Improved phrase highlighting to account for fragmented text."""
    phrase_to_highlight = phrase_to_highlight.strip()
    matches = page_obj.search_for(phrase_to_highlight)
    
    if not matches:
        print(f"No matches found for '{phrase_to_highlight}'. Trying with box search.")
        # Fall back to manual bounding box approximation
        for word in phrase_to_highlight.split():
            word_matches = page_obj.search_for(word)
            for match in word_matches:
                highlight = page_obj.add_highlight_annot(match)
                highlight.set_colors(stroke=highlight_color)
                highlight.update()
    else:
        for match in matches:
            highlight = page_obj.add_highlight_annot(match)
            highlight.set_colors(stroke=highlight_color)
            highlight.update()
            
def highlight_word_in_line(page_obj, line, search_word, word_highlight_color):
    """Highlights the specific word within the line."""
    word_start_idx = line.find(search_word)
    if word_start_idx != -1:
        # Locate the word within the line
        rect = page_obj.search_for(search_word)[0]  # Get the bounding box of the word
        highlight = page_obj.add_highlight_annot(rect)  # Add highlight to the word's bounding box
        highlight.set_colors(stroke=word_highlight_color)  # Set color for word highlight
        highlight.update()
def add_focus_link_to_highlighted_area(page_obj, highlight_rect):
    """
    Adds a link annotation to focus on the highlighted area.
    """
    try:
        # Create a 'view area' link annotation on the highlighted rectangle
        link_rect = fitz.Rect(*highlight_rect)
        page_obj.add_link(
            rect=link_rect,
            pagenum=page_obj.number,  # Target the same page
            kind=fitz.LINK_GOTO,      # Link type: Go to the area
        )
        print("Focus link added to the highlighted area.")
    except Exception as e:
        print(f"Error adding focus link: {e}")
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import DictionaryObject, NumberObject, NameObject, ArrayObject
      
def save_and_open_temp_pdf(pdf_doc, page_idx, focus_rect=None):
    """
    Saves the full PDF with highlights and sets the initial view to the specified page and focus area using PyPDF2.
    """
    temp_filename = None
    focused_filename = None
    try:
        # Generate a unique temporary filename
        temp_filename = os.path.join(tempfile.gettempdir(), f"highlighted_{os.getpid()}.pdf")
        
        # Save the entire document with highlights
        pdf_doc.save(temp_filename)
        pdf_doc.close()

        # Use PyPDF2 to set the initial view (OpenAction)
        with open(temp_filename, "rb") as pdf_file:
            pdf_reader = PdfReader(pdf_file)
            pdf_writer = PdfWriter()

            # Copy all pages to the writer
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)

            # Get a reference to the target page
            target_page_ref = pdf_writer.pages[page_idx - 1].indirect_reference

            # Manually create the OpenAction destination dictionary
            destination = ArrayObject([target_page_ref, NameObject("/Fit")])  # "/Fit" for full-page fit
            open_action = DictionaryObject({
                NameObject("/Type"): NameObject("/Action"),
                NameObject("/S"): NameObject("/GoTo"),
                NameObject("/D"): destination
            })

            # Set OpenAction in the PDF catalog
            pdf_writer._root_object.update({
                NameObject("/OpenAction"): open_action
            })

            # Save the modified PDF to a new file
            focused_filename = os.path.join(tempfile.gettempdir(), f"focused_{os.getpid()}.pdf")
            with open(focused_filename, "wb") as focused_file:
                pdf_writer.write(focused_file)

        # Open the modified PDF in the default viewer
        if os.name == 'nt':  # Windows
            os.startfile(focused_filename)
        elif os.name == 'posix':  # macOS or Linux
            subprocess.run(['open', focused_filename] if os.uname().sysname == 'Darwin' else ['xdg-open', focused_filename])
        else:
            raise OSError("Unsupported operating system for opening PDF automatically.")

        print(f"PDF saved and opened with focus on page {page_idx}: {focused_filename}")
    except Exception as e:
        print(f"Error saving or opening the PDF: {e}")
    finally:
        if temp_filename and os.path.exists(temp_filename):
            os.remove(temp_filename)  # Cleanup temporary file

rows=[]
# nKeywordID=[]

def get_all_dbvalue(rows):
    print("inside get dbvalues newwwwwww")
    print(rows,"rowrow")
    return rows
def process_pdf_highlighting(row, pdf_directory):
    print('starting')
    """Processes highlighting in the PDF based on CSV row details."""
    try:
        # Unpack row values
        nKeywordID, nFileNameID, nPageNumber, nStartLine, nEndLine, cData, cDataValue, var5, nFileName = row
        # print(f"Unpacked row: {row}")

        nFileName = os.path.join(pdf_directory, nFileName.strip())
        # print(f"Opening PDF file: {nFileName}")

        if not os.path.exists(nFileName):
            print(f"Error: The PDF file {nFileName} does not exist.")
            return

        # Open the PDF file with pdfplumber
        pdf_file=open_pdf_document(nFileName)
        # print("Successfully opened PDF.")
        page_obj, page_text_lines = extract_page_and_text(pdf_file, nPageNumber)
        # print(page_obj,"pageeeeee")
        # print(page_text_lines,'page text line')
        # print(page_obj,"inside process pdf")
        # print(nStartLine,"inside pdf highlight")
        # print(nEndLine,"inside pdf highlight")
        if page_obj:
            # highlight_lines_and_keywords(nFileName,page, lines, nStartLine, nEndLine, cDataValue, color='yellow')
            highlight_lines_and_keywords(page_obj,page_text_lines, nStartLine, nEndLine, cDataValue, line_highlight_color='yellow', word_highlight_color='cyan')
            # print("inside process pdf highlight")
        else:
            print("Failed to extract text from page.")
        # save_and_open_temp_pdf(pdf_file) 
        # print('inside open pdf')  
        matches = page_obj.search_for(cDataValue)
        print(matches,"matchessss")
        if matches:
            focus_rect = matches[0]  # Use the first match for focus
        else:
            focus_rect = None
            print(f"No matches found for focus on '{cDataValue}'.")

        highlighted_pdf_path = save_and_open_temp_pdf(pdf_file,nPageNumber,focus_rect)
        print(focus_rect,"newwwwww")
        print(pdf_file,"pdf_filepdf_file")
        return highlighted_pdf_path
    except ValueError as e:
        print("Unpacking error:", e)

directory_path=get_pdf_directory()
# pdf_document = open_pdf_document(input_pdf_path)
# page_obj, page_text_lines = extract_page_and_text(pdf_document, page_idx)
row=get_all_dbvalue(rows)
process_pdf_highlighting(row,directory_path)
print('starting 132123')
# highlight_lines_and_keywords(page_obj, page_text_lines, start_idx, end_idx, search_word, line_highlight_color='yellow', word_highlight_color='cyan')
    
    # Save and open the highlighted PDF temporarily
# save_and_open_temp_pdf(pdf_file)