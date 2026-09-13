from sentence_transformers import SentenceTransformer, util
from pypdf import PdfReader
import re

model = SentenceTransformer('all-MiniLM-L6-v2')

def load_and_chunk_pdf(filepath):
    reader = PdfReader(filepath)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() + "\n"
    file_chunks = re.split(r'\n\s*\n', full_text)
    file_chunks = [c.strip() for c in file_chunks if c.strip() != ""]
    return file_chunks

def load_and_chunk_txt(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    file_chunks = text.strip().split("\n")
    file_chunks = [c.strip() for c in file_chunks if c.strip() != ""]
    return file_chunks

resume_chunks = load_and_chunk_pdf("knowledge/shreyansh_resume.pdf")
about_chunks = load_and_chunk_txt("knowledge/about.txt")

all_chunks = resume_chunks + about_chunks
all_sources = (["resume"] * len(resume_chunks)) + (["about"] * len(about_chunks))

chunk_embeddings = model.encode(all_chunks)

def search_document(query):
    query_embedding = model.encode(query)
    scores = util.cos_sim(query_embedding, chunk_embeddings)[0]
    top_results = scores.topk(3)
    
    if top_results.values[0] < 0.15:
        return "No relevant information found in the document."
    
    result = ""
    for idx in top_results.indices:
        result += f"[Source: {all_sources[idx]}] {all_chunks[idx]}\n\n"
    return result
