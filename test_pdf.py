
from pypdf import PdfReader
import re

reader = PdfReader("knowledge/shreyansh_resume.pdf")
full_text = ""
for page in reader.pages:
    full_text += page.extract_text() + " "

print(full_text)
# Split by sentence-ending punctuation
chunks = re.split(r'\n\s*\n', full_text)
chunks = [chunk.strip() for chunk in chunks if chunk.strip() != ""]
