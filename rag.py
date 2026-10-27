"""
rag.py
------
Implements Retrieval-Augmented Generation (RAG) - Phase 4.

What this does, step by step:
1. Reads every .txt file in data/knowledge_base/ (Skilled Sapiens' own
   internal knowledge, written by us in Phase 4).
2. Converts each document into a numeric "embedding" - a vector that
   captures its meaning - using a small, free, local model
   (sentence-transformers). No API call, no cost.
3. Stores these vectors in a FAISS index, a fast similarity-search
   structure, so we can find "which documents are most similar to this
   query" without comparing against every document one by one.
4. Given a query (e.g. "AI upskilling for an IT company"), embeds the
   query the same way and retrieves the most similar knowledge chunks.
5. Sends ONLY the retrieved chunks (not the LLM's general knowledge) to
   the LLM, with strict instructions to answer using just that content.
   This is what makes the explanation "grounded" rather than invented.
"""

import os
import glob

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from openai import OpenAI

import config
import prompts

KNOWLEDGE_BASE_DIR = "data/knowledge_base"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  # small (~90MB), fast, free, runs on CPU

# Loaded once and reused - loading this model from disk is slow, so we
# don't want to do it on every single retrieval call.
_embedding_model = None


def get_embedding_model():
    """Lazy-loads the embedding model once, then reuses it."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model


def load_knowledge_documents() -> list:
    """Reads every .txt file in the knowledge base folder into memory."""
    documents = []
    filepaths = sorted(glob.glob(os.path.join(KNOWLEDGE_BASE_DIR, "*.txt")))

    for filepath in filepaths:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read().strip()
        if text:
            documents.append({"source": os.path.basename(filepath), "text": text})

    return documents


def build_index():
    """
    Builds an in-memory FAISS index from the knowledge base documents.

    Returns (index, documents):
      - index: the FAISS index used for similarity search
      - documents: the original list of {source, text} dicts, in the
        same order as the vectors in the index, so we can map a search
        result back to readable text.
    """
    documents = load_knowledge_documents()
    if not documents:
        raise ValueError(
            f"No knowledge documents found in '{KNOWLEDGE_BASE_DIR}'. "
            "Make sure the .txt files exist there."
        )

    model = get_embedding_model()
    texts = [doc["text"] for doc in documents]

    # normalize_embeddings=True means we can use inner product for
    # cosine similarity search below - a standard, simple RAG setup.
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # IP = inner product = cosine similarity here
    index.add(embeddings.astype("float32"))

    return index, documents


def retrieve(query: str, index, documents: list, top_k: int = 3) -> list:
    """
    Given a query and a pre-built index, returns the top_k most similar
    knowledge chunks, each with a similarity score (higher = more relevant).
    """
    model = get_embedding_model()
    query_embedding = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)

    scores, indices = index.search(query_embedding.astype("float32"), top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:  # FAISS returns -1 if there aren't enough documents to fill top_k
            continue
        results.append({
            "source": documents[idx]["source"],
            "text": documents[idx]["text"],
            "similarity": float(score),
        })

    return results


def generate_grounded_explanation(query: str, retrieved_chunks: list) -> str:
    """
    Sends retrieved internal knowledge to the LLM and asks it to answer
    using ONLY that information. This is the "generation" half of RAG.

    If retrieval found nothing, we deliberately do NOT call the LLM with
    empty context - that would risk it inventing an answer. We return a
    clear, honest message instead, per the project brief's anti-hallucination rule.
    """
    if not retrieved_chunks:
        return "No relevant internal knowledge could be retrieved for this query."

    context_text = "\n\n".join(
        f"[Source: {chunk['source']}]\n{chunk['text']}" for chunk in retrieved_chunks
    )

    try:
        client = OpenAI(api_key=config.GROQ_API_KEY, base_url=config.GROQ_BASE_URL)
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": prompts.RAG_GROUNDED_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": prompts.RAG_GROUNDED_USER_TEMPLATE.format(
                        context=context_text, query=query
                    ),
                },
            ],
            max_tokens=300,
            temperature=0.3,  # lower temperature = more consistent, less "creative" drift
        )
        return response.choices[0].message.content

    except Exception as e:
        # Never let a RAG/LLM failure crash the whole agent - degrade gracefully.
        return (
            f"Could not generate an explanation due to an LLM error ({e}). "
            "The retrieved internal knowledge above is still available."
        )
