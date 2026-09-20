import pypdf
import csv
from pathlib import Path

def load_pdf(file_path):
    """
    Load a pdf file and return it as string
    """
    text = ""
    #catch file not found error and return empty string
    try:
        with open(file_path, 'rb') as f:
            pdf_reader = pypdf.PdfReader(f)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text is not None:
                    text += page_text + "\n"
                else:
                    text += ""  # If no text is found, add an empty string
                
        if text.strip() == "":
            raise ValueError(f"No text found in PDF file: {file_path}")
        else:
            return text
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}") from None


def load_txt(file_path):
    """
    load text file and return it as string
    """
    text = ""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        if text.strip() == "":
            raise ValueError(f"No text found in text file: {file_path}")
        else:
            return text
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}") from None

def load_csv(file_path):
    """
    load csv file and return it as string
    """
    text = ""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                #"name: Alice, age: 30, department: Engineering"
                text += ",".join([f"{key}: {value}" for key, value in row.items()]) + "\n"
        if text.strip() == "":
            raise ValueError(f"No text found in csv file: {file_path}")
        else:
            return text
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}") from None



"""
creating a dispatch table to map file extensions
to their corresponding loader functions
"""
loaders = {
    '.pdf': load_pdf,
    '.txt': load_txt,
    '.csv': load_csv
}


def load_document(file_path):
    """ 
    load document based on file extension
    """
    #get the file extension
    file_extension = Path(file_path).suffix.lower()

    #check if the file extension is supported
    if file_extension in loaders:
        #call corresponding loader function
        return loaders[file_extension](file_path)
    else:
        raise ValueError(f"Unsupported file extension: {file_extension}")
