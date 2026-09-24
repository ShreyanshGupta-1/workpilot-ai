from pypdf import PdfReader
from google import genai
import os
import re
import numpy as np
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_embedding(text):
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

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

chunk_embeddings = [get_embedding(chunk) for chunk in all_chunks]

def search_document(query):
    query_embedding = get_embedding(query)
    scores = [cosine_similarity(query_embedding, emb) for emb in chunk_embeddings]

    scored = sorted(zip(scores, range(len(scores))), reverse=True)
    top3 = scored[:5]

    if top3[0][0] < 0.5:
        return "No relevant information found in the document."

    result = ""
    for score, idx in top3:
        result += f"[Source: {all_sources[idx]}] {all_chunks[idx]}\n\n"
    return result

if __name__ == "__main__":
    result = search_document("what projects has Shreyansh worked on?")
    print(result)