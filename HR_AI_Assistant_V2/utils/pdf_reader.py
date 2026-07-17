# ==========================================================
# File Name : pdf_reader.py
# Module    : PDF Reader
#
# Purpose:
# Read all HR policy PDF documents from the specified folder, extract their text,
# and split the content into smaller chunks for efficient AI processing.
# ==========================================================

import os
from functools import lru_cache
import pdfplumber


def split_text(text, chunk_size=800):
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


@lru_cache(maxsize=2)
def read_all_pdfs(folder_path):
    full_text = ''

    for file in os.listdir(folder_path):
        if file.lower().endswith('.pdf'):
            path = os.path.join(folder_path, file)
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    full_text += page.extract_text() or ''

    return split_text(full_text)
