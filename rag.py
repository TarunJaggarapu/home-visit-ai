"""
Retrieval-Augmented Generation (RAG) over the notes.

The idea in three steps:
  1. Split notes into chunks and turn each into a vector (an "embedding").
  2. Store vectors in a FAISS index for fast similarity search.
  3. For a question: embed it, find the closest chunks, and hand those chunks
     to the LLM as context so it answers from the notes, not from memory.
"""
import numpy as np
import faiss
from config import client, EMBED_MODEL, CHAT_MODEL


def _embed(texts: list[str]) -> np.ndarray:
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return np.array([d.embedding for d in resp.data], dtype="float32")


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    """Simple character-based chunker with overlap so context isn't cut mid-idea."""
    chunks, start = [], 0
    while start < len(text):
        chunk = text[start:start + chunk_size]
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


class NotesIndex:
    def __init__(self):
        self.index = None
        self.chunks: list[str] = []
        self.sources: list[str] = []

    def build(self, docs: list[tuple[str, str]]):
        """docs = list of (source_name, full_text)."""
        self.chunks, self.sources = [], []
        for name, text in docs:
            for c in chunk_text(text):
                self.chunks.append(c)
                self.sources.append(name)
        vectors = _embed(self.chunks)
        faiss.normalize_L2(vectors)                 # so inner product == cosine similarity
        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)
        return self

    def search(self, query: str, k: int = 4):
        q = _embed([query])
        faiss.normalize_L2(q)
        scores, ids = self.index.search(q, k)
        return [
            (self.chunks[i], self.sources[i], float(scores[0][j]))
            for j, i in enumerate(ids[0]) if i != -1
        ]


def answer_question(index: NotesIndex, question: str, k: int = 4):
    """Returns (answer_text, retrieved_hits)."""
    hits = index.search(question, k)
    context = "\n\n---\n\n".join(f"[{src}]\n{chunk}" for chunk, src, _ in hits)
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Answer the question using ONLY the note excerpts provided. "
                    "Cite the source note name(s) in brackets. If the answer is not "
                    "in the excerpts, say you cannot find it in the notes."
                ),
            },
            {"role": "user", "content": f"Excerpts:\n{context}\n\nQuestion: {question}"},
        ],
    )
    return resp.choices[0].message.content.strip(), hits
