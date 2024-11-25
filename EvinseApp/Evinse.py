# import os
# import PyPDF2
# import re
# import csv
# import nltk
# from nltk import word_tokenize, pos_tag
# from nltk.stem import WordNetLemmatizer
# from fuzzywuzzy import fuzz

# # Download necessary resources for PoS tagging (only needed once)
# nltk.download('punkt')
# nltk.download('averaged_perceptron_tagger')
# nltk.download('wordnet')

# # Initialize lemmatizer
# lemmatizer = WordNetLemmatizer()

# # Normalization function
# def normalize(text):
#     return text.lower().strip()

# # # Define synonyms for keywords
# synonyms = {
#     "b12": ["b12", "cobalamin"],
#     # "iron": ["iron", "ferrous"],
#     "vitamin D":['vitamin D'],
#     "Copper deficiency":['copper','Hypocupremia'],
#     "Selenium definciency":['Keshan disease'],
#     "Zinc deficiency":['zinc','Acrodermatitis enteropathica'],
#     "Calcium deficiency":['Hypocalcemia','Calcium'],
#     "Magnesium deficiency":['hypomagnesemia'],
#     "Ferritin deficiency":['holoferritin'],
#     "Iron deficiency":["iron", "ferrous"],
#     "Iodine deficiency":['underactive thyroid'],
#     "Vitamin A deficiency":['retinol'],
#     "Beta carotene  deficiency":[' Food Orange 5', 'Provitamin A'],
#      "Vitamin B1 deficiency":['Thiamine','thiamin'],
#      "Vitamin B2 deficiency":['Riboflavin'],
#      "Vitamin B12 deficiency":['Cobalamin'],
#      "Vitamin B6 deficiency":['Pyridoxine'],
#     "Vitamin C deficiency":['L-ascorbic acid'],
#     "Vitamin D deficiency":['calciferol', 'cholecalciferol', 'ergocalciferol', 'viosterol'],
#     "Vitamin E deficiency":['tocopherol'],
#     "Vitamin B9 deficiency":['Folic Acid'],


                            

#     # Add more synonyms as needed
# }

# # Get synonyms for a keyword
# def get_synonyms(keyword):
#     return synonyms.get(normalize(keyword), [normalize(keyword)])

# import pdfplumber

# def detect_tables(pdf_path, page_number):
#     with pdfplumber.open(pdf_path) as pdf:
#         page = pdf.pages[page_number - 1]  # Page numbers are zero-indexed
#         tables = page.extract_tables()
#         return len(tables) > 0
# def extract_text_from_pdf(pdf_path):
#     text_with_numbers = []
#     previous_header = None  # Initialize previous_header
#     previous_footer = None  # Initialize previous_footer
#     table_number = 0  # Initialize table number counter

#     with pdfplumber.open(pdf_path) as pdf:
#         for page_number in range(len(pdf.pages)):
#             # Detect if there are tables on this page
#             tables_detected = detect_tables(pdf_path, page_number + 1)

#             # Extract text from each page
#             page = pdf.pages[page_number]
#             text = page.extract_text()

#             if text:
#                 # Split text into lines for more control
#                 lines = text.split('\n')

#                 # Heuristic: Identify potential header and footer
#                 header = lines[0].strip()  # Assume first line is a header
#                 footer = lines[-1].strip()  # Assume last line is a footer

#                 # Skip header if it's similar to previous page's header
#                 if previous_header is not None and header == previous_header:
#                     lines = lines[1:]  # Remove the first line (header)

#                 # Skip footer if it's similar to previous page's footer
#                 if previous_footer is not None and footer == previous_footer:
#                     lines = lines[:-1]  # Remove the last line (footer)

#                 # Update previous header and footer for comparison on the next page
#                 previous_header = header
#                 previous_footer = footer

#                 # Join the remaining lines back into text for sentence splitting
#                 remaining_text = ' '.join(lines)

#                 # Use regex to split by full stop followed by space or capital letter
#                 sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', remaining_text)  # Split by sentence endings followed by space and capital letter
                
#                 # Determine the source (table or paragraph)
#                 if tables_detected:  # If a table is detected
#                     table_number += 1  # Increment the table number
#                     table_label = f"Table {table_number}"  # Create table label
#                 else:
#                     table_label = None  # No table label if no table is detected
                    
#                 source = 'table' if tables_detected else 'paragraph'

#                 for line_number, line in enumerate(sentences, start=1):
#                     cleaned_line = clean_text(line.strip())
#                     if cleaned_line:
#                         # Append table_label (or None) to the extracted data
#                         text_with_numbers.append((page_number + 1, line_number, cleaned_line, source, table_label))
#                         # print(f"Page: {page_number + 1}, Line: {line_number}, Text: {cleaned_line}, Source: {source}, Table Number: {table_label if tables_detected else 'N/A'}")

#     return text_with_numbers

# # Function to clean extracted text
# def clean_text(text):
#     # Step 1: Remove unwanted characters
#     text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Remove non-ASCII characters
    
#     # Step 2: Remove URLs (http://, https://, www)
#     text = re.sub(r'\b(http[s]?://\S+|www\.\S+)\b', '', text)  # Remove URLs

#     # Step 3: Remove content inside square brackets, such as [1], [2], etc. (citations)
#     text = re.sub(r'\[.*?\]', '', text)  # Remove anything inside square brackets

#     # Step 4: Remove citations in the form (Author, Year)
#     text = re.sub(r'\(.*?\d{4}.*?\)', '', text)  # Remove (Author, Year) citations

#     # Step 5: Remove dates (various formats: dd-mm-yyyy, mm/dd/yyyy, Month Day, Year)
#     text = re.sub(r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b(?:\.|uary|ember)? \d{1,2}, \d{4})\b', '', text)

#     # Step 6: Remove times (12:00 AM, 23:59, etc.)
#     text = re.sub(r'\b\d{1,2}:\d{2}\s?(?:AM|PM|am|pm)?\b', '', text)  # Remove time formats

#     # Step 7: Remove references section if detected
#     if re.search(r'\bReferences\b', text, re.IGNORECASE):
#         text = text.split('References', 1)[0]  # Remove everything after "References"

#     # Step 8: Normalize whitespaces (removes extra spaces, tabs, line breaks)
#     text = re.sub(r'\s+', ' ', text).strip()  # Replace multiple spaces with one

#     return text

# # Improved extraction function for values and units
# def extract_value_and_unit(keyword, tokens_with_pos):
#     keyword_tokens = [lemmatizer.lemmatize(normalize(token)) for token in keyword.split()]
#     combined_keyword_length = len(keyword_tokens)

#     # Check for the full combined keyword first
#     for i in range(len(tokens_with_pos) - combined_keyword_length + 1):
#         match = True
#         for j in range(combined_keyword_length):
#             # Fuzzy matching
#             if fuzz.ratio(normalize(keyword_tokens[j]), normalize(tokens_with_pos[i + j][0])) < 80:
#                 match = False
#                 break

#         if match:
#             return find_value_and_unit(tokens_with_pos, i + combined_keyword_length)

#     # Check for the first word in the combined keyword with synonyms
#     first_keyword = keyword_tokens[0]
#     for i in range(len(tokens_with_pos)):
#         for syn in get_synonyms(first_keyword):
#             if normalize(tokens_with_pos[i][0]) == syn:
#                 return find_value_and_unit(tokens_with_pos, i + 1)

#     return "N/A", "N/A"

# # Helper function to find the value and unit
# def find_value_and_unit(tokens_with_pos, start_index):
#     value_range = ""
#     unit = ""
    
#     for k in range(start_index, len(tokens_with_pos)):
#         # Check for the pattern "X to Y" where X and Y are numbers
#         if tokens_with_pos[k][1] == 'CD' and k + 2 < len(tokens_with_pos) and tokens_with_pos[k + 1][0] == 'to' and tokens_with_pos[k + 2][1] == 'CD':
#             value_from = tokens_with_pos[k][0]  # Value before 'to'
#             value_to = tokens_with_pos[k + 2][0]  # Value after 'to'
#             value_range = f"{value_from} to {value_to}"  # Construct the value range
            
#             # Check if the next token after 'to Y' is a unit (tagged as NN, NNS)
#             if k + 3 < len(tokens_with_pos) and tokens_with_pos[k + 3][1] in ['NN', 'NNS']:
#                 unit = tokens_with_pos[k + 3][0]  # Capture the unit
#                 return value_range, unit  # Return value range and unit
#             else:
#                 return value_range, ""  # Return value range without unit if no unit is found
#     return "N/A", "N/A"  # Return "N/A" if no value is found

# def extract_deficiency_prevalence_and_ci(tokens_with_pos,additional_deficiency_keywords=None):
#     if additional_deficiency_keywords is None:
#         additional_deficiency_keywords = keyword_names
#     deficiencies = []
#     prevalences = []
#     ci_values = []
#     other_values = []  # List for other numerical values
    
#     i = 0
#     found_prevalence = False  # Flag to check if 'prevalence' keyword is found in the sentence
    
#     while i < len(tokens_with_pos):
#         token, pos = tokens_with_pos[i]
        
        
#         # Look for deficiency names directly or related terms
#         if (pos == 'NN' and i + 1 < len(tokens_with_pos) and tokens_with_pos[i + 1][0].lower() == 'deficiency') or token.lower() in additional_deficiency_keywords:
#             deficiency = token + " deficiency" if pos == 'NN' else token
#             deficiencies.append(deficiency)
#             i += 1  # Skip next token
        
#         # Detect if the word 'prevalence' is present in the sentence
#         if token.lower() == 'prevalence':
#             found_prevalence = True
        
#         # Look for prevalence values (Cardinal followed by % and prevalence keyword is present)
#         if pos == 'CD' and i + 1 < len(tokens_with_pos) and tokens_with_pos[i + 1][0] == '%':
#             if found_prevalence:  # Only append if 'prevalence' was found in the sentence
#                 prevalence = token + tokens_with_pos[i + 1][0]  # e.g., '41.9%'
#                 prevalences.append(prevalence)
#             else:
#                 # If 'prevalence' is not found, treat it as an 'other value'
#                 other_values.append(token + tokens_with_pos[i + 1][0])
#             i += 1  # Skip the '%'
        
#         # Look for CI values enclosed in parentheses
#         if token == '(' and i + 1 < len(tokens_with_pos) and tokens_with_pos[i + 1][0] == '95' and tokens_with_pos[i + 2][0] == '%':
#             j = i + 3  # Move past '95%', 'CI'
#             ci = []
#             while j < len(tokens_with_pos) and tokens_with_pos[j][0] != ')':
#                 if tokens_with_pos[j][1] == 'CD':  # Collect only numerical values
#                     ci.append(tokens_with_pos[j][0])
#                 j += 1
#             if len(ci) >= 2:
#                 ci_values.append(f"{ci[0]} to {ci[1]}")
#             i = j  # Move past ')'

#         # Look for other numerical values (not prevalence or CI) if not already handled
#         if pos == 'CD' and i + 1 < len(tokens_with_pos) and tokens_with_pos[i + 1][0] != '%':
#             other_values.append(token)
        
#         i += 1
    
#     # Combine deficiencies, prevalences, CI values, and other numerical values
#     results = []
#     for idx in range(len(deficiencies)):
#         deficiency = deficiencies[idx] if idx < len(deficiencies) else "Unknown deficiency"
#         prevalence = prevalences[idx] if idx < len(prevalences) else "Unknown prevalence"
#         ci = ci_values[idx] if idx < len(ci_values) else "NA"
#         other_value = other_values[idx] if idx < len(other_values) else "No other value"
#         results.append((deficiency, prevalence, ci, other_value))
    
#     return results

# file_list=[]
# file_ids=[]
# def read_files(file_list, file_ids):
#     file_contents = {}
    
#     for file_path, pdf_number in zip(file_list, file_ids):  # Iterate with pdf_numbers
#         try:
#             # Get the file extension
#             file_extension = file_path.split('.')[-1].lower()

#             # Handle PDF files
#             if file_extension == 'pdf':
#                 extracted_data = extract_text_from_pdf(file_path)
#                 file_contents[file_path] = (extracted_data, pdf_number)  # Store structured data and pdf_number
#                 # csv=process_pdf_and_save_to_csv(file_contents, output_csv_path, keywords_with_ids)

#             # Handle TXT files
#             elif file_extension == 'txt':
#                 with open(file_path, 'r', encoding='utf-8') as file:
#                     raw_text = file.read()
#                     cleaned_text = clean_text(raw_text)
#                     file_contents[file_path] = (cleaned_text, pdf_number)  # Include pdf_number

#             # Handle Word (DOCX) files
#             elif file_extension == 'docx':
#                 doc = Document(file_path)
#                 cleaned_text = '\n'.join([clean_text(para.text) for para in doc.paragraphs if para.text.strip() != ""])
#                 file_contents[file_path] = (cleaned_text, pdf_number)  # Include pdf_number

#             # Unsupported file type
#             else:
#                 file_contents[file_path] = (f"Unsupported file type: {file_extension}", pdf_number)  # Include pdf_number

#         except Exception as e:
#             file_contents[file_path] = (f"Error reading file: {e}", pdf_number)  # Include pdf_number
#     # print(file_contents,"file_contents")
#     return file_contents
# keyword_names=[]
# keyword_ids=[]
# def read_keywords_and_ids( keyword_ids,keyword_names):
#     # Create a list of tuples (keyword_id, keyword)
#     keywords_with_ids = list(zip( keyword_ids,keyword_names))
#     print(keywords_with_ids,"keywordsssssssss_with_ids")
#     return keywords_with_ids

# import pandas as pd
# # from nltk import pos_tag, word_tokenize

# def process_pdf_and_save_to_df(file_contents, keywords_with_ids):
#     print(file_contents,"file content")
#     print(keywords_with_ids,"keyword with id")
#     # List to store all rows
#     print("inside process pdf function")
#     data_rows = []
#     print('Inside process_pdf_and_save_to_df')
#     print('Keywords with IDs:', keywords_with_ids)
#     print('File Contents:', file_contents)
    
#     # Column headers
#     columns = ['Keyword ID','PDF Number','Page', 'Line','Source','Sentence',  'Keyword',  'Data Type', 'Value',   'Table Number']
    
#     for keyword_id, keyword in keywords_with_ids:  # Iterate over each keyword with its ID
#         print(f"Processing keyword: {keyword} (ID: {keyword_id})")
#         for pdf_path, (extracted_data, pdf_number) in file_contents.items():  # Iterate over the file contents
#             print(f"Processing PDF: {pdf_path} with number {pdf_number}")
#             for page_number, line_number, cleaned_line, source, table_label in extracted_data:
#                 # Check if the current keyword is in the cleaned line
#                 if keyword.lower() in cleaned_line.lower():
#                     print(f"Keyword '{keyword}' found in line: {cleaned_line}")
#                     # Assuming the tokenization and extraction functions work
#                     # Process each tokenized result
#                     tokens_with_pos = pos_tag(word_tokenize(cleaned_line))
#                     results = extract_deficiency_prevalence_and_ci(tokens_with_pos)  # Ensure this function is defined
#                     print(results,"results")
                    
#                     for result in results:
#                         print(f"Result for {keyword}: {result}")
#                         deficiency, prevalence, ci, other_value = result
#                         data_rows.append([keyword_id,pdf_number, page_number, line_number,source, cleaned_line,keyword,  'Deficiency', deficiency,   table_label if table_label else 'N/A'])
#                         data_rows.append([keyword_id,pdf_number, page_number, line_number,source, cleaned_line,keyword, 'Prevalence', prevalence,  table_label if table_label else 'N/A'])
#                         data_rows.append([keyword_id,pdf_number, page_number, line_number,source, cleaned_line,keyword, '95% CI', ci, table_label if table_label else 'N/A'])
#                         data_rows.append([keyword_id,pdf_number, page_number, line_number,source, cleaned_line,keyword, 'Other Value', other_value, table_label if table_label else 'N/A'])
#                         # print("Data row appended:", data_rows[-1])  # Print the last appended row
#     # print("Data row appended:", data_rows)
#     # Create DataFrame from collected data rows
#     df = pd.DataFrame(data_rows, columns=columns)
#     print("DataFrame created")
#     return df

# pdf_paths = read_files(file_list, file_ids) 
# # output_csv_path = "extracted_data4.csv"  # Use a consistent CSV filename
# keywords_with_ids = read_keywords_and_ids(keyword_names, keyword_ids) # Create a list of tuples (keyword_id, keyword)
# process_pdf_and_save_to_df(pdf_paths, keywords_with_ids)  # Pass the modified file paths




import PyPDF2
import csv
import re
# from docx import Document
import pandas as pd
from nltk import pos_tag, word_tokenize
from nltk.stem import WordNetLemmatizer
from fuzzywuzzy import fuzz
import ftfy

import nltk




# Initialize the lemmatizer
lemmatizer = WordNetLemmatizer()

# Define the synonyms dictionary
synonyms = {
    "b12": ["b12", "cobalamin"],
    "vitamin D": ['vitamin D'],
    "Copper deficiency": ['copper', 'Hypocupremia'],
    "Selenium deficiency": ['Keshan disease'],
    "Zinc deficiency": ['zinc', 'Acrodermatitis enteropathica'],
    "Calcium deficiency": ['Hypocalcemia', 'Calcium'],
    "Magnesium deficiency": ['hypomagnesemia'],
    "Ferritin deficiency": ['holoferritin'],
    "Iron deficiency": ["iron", "ferrous"],
    "Iodine deficiency": ['underactive thyroid'],
    "Vitamin A deficiency": ['retinol'],
    "Beta carotene deficiency": ['Food Orange 5', 'Provitamin A'],
    "Vitamin B1 deficiency": ['Thiamine', 'thiamin'],
    "Vitamin B2 deficiency": ['Riboflavin'],
    "Vitamin B12 deficiency": ['Cobalamin'],
    "Vitamin B6 deficiency": ['Pyridoxine'],
    "Vitamin C deficiency": ['L-ascorbic acid'],
    "Vitamin D deficiency": ['calciferol', 'cholecalciferol', 'ergocalciferol', 'viosterol'],
    "Vitamin E deficiency": ['tocopherol'],
    "Vitamin B9 deficiency": ['Folic Acid'],
}

# Normalize a keyword
def normalize(keyword):
    return re.sub(r'[^a-zA-Z0-9]', '', keyword.lower())

# Get synonyms for a keyword
def get_synonyms(keyword):
    normalized_keyword = normalize(keyword)  # Normalize the keyword
    # Get synonyms from the dictionary or return the keyword if not found
    return synonyms.get(normalized_keyword, [keyword])

# Function to clean text
def clean_text(text):
    text=re.sub(r'[^\x00-\x7F]+', ' ', text)  # Remove non-ASCII characters
    text=re.sub(r'\s+', ' ', text).strip() #remove extra space
    text = re.sub(r'\b(http[s]?://\S+|www\.\S+)\b', '', text)  # Remove URLs
    text=ftfy.fix_text(text)
    # text = unidecode(text)
    return text
# Function to extract sentences from PDF files
def extract_sentences_from_pdfs(file_list):
    extracted_data = []
    for pdf_file in file_list:
        with open(pdf_file, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_number, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                if text:
                    lines = text.splitlines()
                    sentence = ""
                    start_line_number = None
                    for line_number, line in enumerate(lines, start=1):
                        if start_line_number is None:
                            start_line_number = line_number

                        # Clean each line of text before processing
                        line = clean_text(line)

                        sentence += " " + line.strip()
                        if line.strip().endswith('.'):
                            extracted_data.append([
                                pdf_file,
                                page_number,
                                start_line_number,
                                line_number,
                                sentence.strip()
                            ])
                            sentence = ""
                            start_line_number = None
    return extracted_data

# Function to find the value and unit
def find_value_and_unit(tokens_with_pos, start_index):
    value_range = ""
    unit = ""
    
    for k in range(start_index, len(tokens_with_pos)):
        if tokens_with_pos[k][1] == 'CD' and k + 2 < len(tokens_with_pos) and tokens_with_pos[k + 1][0] == 'to' and tokens_with_pos[k + 2][1] == 'CD':
            value_from = tokens_with_pos[k][0]
            value_to = tokens_with_pos[k + 2][0]
            value_range = f"{value_from} to {value_to}"
            
            if k + 3 < len(tokens_with_pos) and tokens_with_pos[k + 3][1] in ['NN', 'NNS']:
                unit = tokens_with_pos[k + 3][0]
                return value_range, unit
            else:
                return value_range, ""
    return "N/A", "N/A"

# Function to extract value and unit based on keywords
def extract_value_and_unit(keyword, tokens_with_pos):
    keyword_tokens = [lemmatizer.lemmatize(normalize(token)) for token in keyword.split()]
    combined_keyword_length = len(keyword_tokens)

    for i in range(len(tokens_with_pos) - combined_keyword_length + 1):
        match = True
        for j in range(combined_keyword_length):
            if fuzz.ratio(normalize(keyword_tokens[j]), normalize(tokens_with_pos[i + j][0])) < 80:
                match = False
                break

        if match:
            return find_value_and_unit(tokens_with_pos, i + combined_keyword_length)

    first_keyword = keyword_tokens[0]
    for i in range(len(tokens_with_pos)):
        for syn in get_synonyms(first_keyword):
            if normalize(tokens_with_pos[i][0]) == syn:
                return find_value_and_unit(tokens_with_pos, i + 1)

    return "N/A", "N/A"

# Function to extract deficiencies, prevalences, and confidence intervals
def extract_deficiency_prevalence_and_ci(tokens_with_pos, sentence_metadata, additional_deficiency_keywords=None):
    # Default deficiency keywords from synonyms
    if additional_deficiency_keywords is None:
        additional_deficiency_keywords = synonyms.keys()
    
    deficiencies = []
    prevalences = []
    ci_values = []
    other_values = []
    other_units = []  # To store the units for numerical values
    n_values = []  # For n values like "n=123"

    found_prevalence = False
    i = 0
    while i < len(tokens_with_pos):
        token, pos = tokens_with_pos[i]
        
        # Detect deficiency keywords based on the token or additional keywords
        if (pos == 'NN' and i + 1 < len(tokens_with_pos) and tokens_with_pos[i + 1][0].lower() == 'deficiency') or token.lower() in additional_deficiency_keywords:
            deficiency = token + " deficiency" if pos == 'NN' else token
            deficiencies.append(deficiency)
            i += 1
        
        # Detect prevalence (often followed by a percentage)
        elif token.lower() == 'prevalence':
            found_prevalence = True
        
        # Look for prevalence values in the form of a percentage (CD + '%')
        if pos == 'CD' and i + 1 < len(tokens_with_pos) and tokens_with_pos[i + 1][0] == '%':
            if found_prevalence:
                prevalence = token + tokens_with_pos[i + 1][0]
                prevalences.append(prevalence)
            else:
                other_values.append(token + tokens_with_pos[i + 1][0])  # Append other numerical values
            i += 1
        
        # Extract confidence intervals (e.g., (95% CI: 10 to 20))
        elif token == '(' and i + 1 < len(tokens_with_pos) and tokens_with_pos[i + 1][0] == '95' and tokens_with_pos[i + 2][0] == '%':
            ci = []
            j = i + 3
            while j < len(tokens_with_pos) and tokens_with_pos[j][0] != ')':
                if tokens_with_pos[j][1] == 'CD':  # Number in confidence interval
                    ci.append(tokens_with_pos[j][0])
                j += 1
            if len(ci) == 2:
                ci_values.append(f"{ci[0]}-{ci[1]}")
            i = j  # Skip over the confidence interval

        # Detect other numerical values (e.g., "5 mg", "200 ng/ml")
        elif pos == 'CD':
            other_values.append(token)
            if i + 1 < len(tokens_with_pos) and tokens_with_pos[i + 1][1] == 'NN':  # Next token could be the unit
                other_units.append(tokens_with_pos[i + 1][0])
                i += 1  # Skip the unit
        
        # Detect 'n' values like "n = 123"
        elif token.lower() == 'n' and i + 1 < len(tokens_with_pos) and tokens_with_pos[i + 1][0] == '=':
            if i + 2 < len(tokens_with_pos) and tokens_with_pos[i + 2][1] == 'CD':  # The number after n=
                n_values.append(tokens_with_pos[i + 2][0])
                i += 2  # Skip over "n = number"
        
        i += 1  # Move to next token

    # Prepare final results
    results = []
    max_length = max(len(deficiencies), len(prevalences), len(ci_values), len(other_values), len(n_values))

    for idx in range(max_length):
        deficiency = deficiencies[idx] if idx < len(deficiencies) else "Unknown deficiency"
        prevalence = prevalences[idx] if idx < len(prevalences) else "Unknown prevalence"
        ci = ci_values[idx] if idx < len(ci_values) else "NA"
        other_value = other_values[idx] if idx < len(other_values) else "No other value"
        n_value = n_values[idx] if idx < len(n_values) else " "
        other_unit = other_units[idx] if idx < len(other_units) else "No unit"
        
        # Return results for each deficiency, prevalence, CI, etc.
        results.append((deficiency, prevalence, ci, other_value, other_unit, n_value))
    
    return results


# Function to read files and extract contents
file_list=[]
file_ids=[]
def read_files(file_list, file_ids):
    file_contents = {}
    for file_path, pdf_number in zip(file_list, file_ids):
        try:
            file_extension = file_path.split('.')[-1].lower()
            if file_extension == 'pdf':
                extracted_data = extract_sentences_from_pdfs([file_path])
                file_contents[file_path] = (extracted_data, pdf_number)
            elif file_extension == 'txt':
                with open(file_path, 'r', encoding='utf-8') as file:
                    raw_text = file.read()
                    cleaned_text = clean_text(raw_text)
                    file_contents[file_path] = (cleaned_text, pdf_number)
            # elif file_extension == 'docx':
            #     doc = Document(file_path)
            #     cleaned_text = '\n'.join([clean_text(para.text) for para in doc.paragraphs if para.text.strip() != ""])
            #     file_contents[file_path] = (cleaned_text, pdf_number)
            else:
                file_contents[file_path] = (f"Unsupported file type: {file_extension}", pdf_number)
        except Exception as e:
            file_contents[file_path] = (f"Error reading file: {e}", pdf_number)
    # print(file_contents,"file_contentsss")
    return file_contents

keyword_names=[]
keyword_ids=[]
def read_keywords_and_ids(keyword_names, keyword_ids):
    """
    Create a list of tuples (keyword_id, keyword).
    """
    keywords_with_ids = list(zip(keyword_ids, keyword_names))
    print(keywords_with_ids, "Keywords with IDs")
    return keywords_with_ids


def process_pdf_and_save_to_df(file_contents, keywords_with_ids):
    # List to store all rows
    data_rows = []
    
    # Column headers
    columns = ['Keyword ID', 'PDF Number', 'Page', 'start line', 'end Line', 'pdf name', 'Sentence', 'Keyword', 'Data Type', 'Value']

    for keyword_id, keyword in keywords_with_ids:
        # Ensure that 'keyword' is a string
        if not isinstance(keyword, str):
            print(f"Skipping non-string keyword: {keyword}")
            continue
        
        keyword = keyword.lower()  # Convert keyword to lowercase for case-insensitive comparison

        for pdf_path, (extracted_data, pdf_number) in file_contents.items():
            for pdf_file, page_number, start_line_number, line_number, cleaned_line in extracted_data:
                
                # Ensure that 'cleaned_line' is a string
                if not isinstance(cleaned_line, str):
                    print(f"Skipping non-string line: {cleaned_line}")
                    continue
                
                if keyword in cleaned_line.lower():
                    tokens_with_pos = pos_tag(word_tokenize(cleaned_line))
                    results = extract_deficiency_prevalence_and_ci(tokens_with_pos, 
                                                                  (pdf_file, page_number, start_line_number, line_number))

                    for result in results:
                        # Adjust unpacking based on the number of returned values
                        if len(result) >= 4:
                            deficiency, prevalence, ci, other_value = result[:4]  # Ensure to only take the first four values
                        else:
                            deficiency, prevalence, ci, other_value = "N/A", "N/A", "N/A", "N/A"  # Fallback values

                        data_rows.append([keyword_id, pdf_number, page_number, start_line_number, line_number, pdf_file, cleaned_line, keyword, 'Deficiency', deficiency])
                        data_rows.append([keyword_id, pdf_number, page_number, start_line_number, line_number, pdf_file, cleaned_line, keyword, 'Prevalence', prevalence])
                        data_rows.append([keyword_id, pdf_number, page_number, start_line_number, line_number, pdf_file, cleaned_line, keyword, '95% CI', ci])
                        data_rows.append([keyword_id, pdf_number, page_number, start_line_number, line_number, pdf_file, cleaned_line, keyword, 'Other Value', other_value])

    df = pd.DataFrame(data_rows, columns=columns)
    # df.to_csv(output_csv, index=False)
    # print(f"Data saved to {output_csv}")
    return df

# Example usage
# pdf_files = ['Amarasinghe 2022.pdf']  # Add your PDF files here
# keyword_list = ['Vitamin A deficiency', 'Iron deficiency','b12']  # Add keywords here
# keyword_ids = [1, 2,3]  # Corresponding keyword IDs
extracted_sentences = extract_sentences_from_pdfs(file_list)

# Create keyword tuples with IDs
keywords_with_ids = read_keywords_and_ids(keyword_ids,keyword_names)

# Read files and extract contents
file_contents = read_files(file_list, file_ids)

# Process the files and save results to CSV
process_pdf_and_save_to_df(file_contents, keywords_with_ids)

print(f"Data successfully written to extracted_deficiencies_and_prevalence1234.csv")
# # 
