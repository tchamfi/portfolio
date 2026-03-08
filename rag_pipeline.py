"""
rag_pipeline.py — RAG pipeline for Ask Lionel
Uses TF-IDF (scikit-learn) instead of ChromaDB — lightweight, no C++ deps
"""

import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from anthropic import Anthropic
from cv_data import CV_CHUNKS
from doc_loader import load_documents_as_chunks

TOP_K = 12

_vectorizer = None
_tfidf_matrix = None
_all_chunks = None


def _get_api_key():
    try:
        import streamlit as st
        return st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))
    except Exception:
        return os.getenv("ANTHROPIC_API_KEY", "")


def create_chroma_collection():
    """Create TF-IDF index from CV chunks + documents. Name kept for compatibility."""
    global _vectorizer, _tfidf_matrix, _all_chunks

    if _all_chunks is not None:
        return

    _all_chunks = []

    # 1. Manual chunks from cv_data.py
    for c in CV_CHUNKS:
        _all_chunks.append({
            "id": c["id"],
            "text": c["text"],
            "metadata": c["metadata"]
        })
    print(f"[RAG] {len(CV_CHUNKS)} manual chunks")

    # 2. Auto-loaded documents from ./docs/
    doc_chunks = load_documents_as_chunks()
    for c in doc_chunks:
        _all_chunks.append({
            "id": c["id"],
            "text": c["text"],
            "metadata": c["metadata"]
        })
    print(f"[RAG] {len(doc_chunks)} document chunks")

    # 3. Build TF-IDF index
    texts = [c["text"] for c in _all_chunks]
    _vectorizer = TfidfVectorizer(
        max_features=10000,
        ngram_range=(1, 2),
        stop_words=None,  # keep French words
        sublinear_tf=True
    )
    _tfidf_matrix = _vectorizer.fit_transform(texts)
    print(f"[RAG] Total: {len(_all_chunks)} chunks indexed (TF-IDF)")


def get_collection():
    """Compatibility wrapper — ensures index is built."""
    if _all_chunks is None:
        create_chroma_collection()
    return True  # dummy return for compatibility


def retrieve_context(question, top_k=TOP_K):
    get_collection()
    return _search(question, top_k)


def _search(question, top_k):
    """Internal search function returning formatted context."""
    query_vec = _vectorizer.transform([question])
    similarities = cosine_similarity(query_vec, _tfidf_matrix).flatten()
    top_indices = np.argsort(similarities)[::-1][:top_k]

    parts = []
    for rank, idx in enumerate(top_indices):
        if similarities[idx] < 0.01:
            continue
        chunk = _all_chunks[idx]
        source = chunk["metadata"].get("source", "cv_data.py")
        parts.append(f"[Source {rank+1} - {source}]\n{chunk['text']}")
    return "\n\n---\n\n".join(parts)


def search_chunks(queries, top_k=10):
    """Search multiple queries and return deduplicated results (for agent)."""
    get_collection()
    seen = set()
    all_results = []
    for q in queries:
        query_vec = _vectorizer.transform([q])
        similarities = cosine_similarity(query_vec, _tfidf_matrix).flatten()
        top_indices = np.argsort(similarities)[::-1][:top_k]
        for idx in top_indices:
            if similarities[idx] < 0.01:
                continue
            cid = _all_chunks[idx]["id"]
            if cid not in seen:
                seen.add(cid)
                all_results.append({
                    "id": cid,
                    "text": _all_chunks[idx]["text"],
                    "score": float(similarities[idx]),
                    "source": _all_chunks[idx]["metadata"].get("source", "cv_data.py")
                })
    all_results.sort(key=lambda x: x["score"], reverse=True)
    return "\n\n---\n\n".join(f"[{r['source']}]\n{r['text']}" for r in all_results[:15])


def generate_response(question, context):
    client = Anthropic(api_key=_get_api_key())
    system_prompt = """Tu es l'assistant IA du portfolio de Lionel TCHAMFONG, Product Owner Senior specialise GenAI & Data.
Ton role est de repondre aux questions des recruteurs et clients potentiels.
Regles STRICTES :
- Reponds UNIQUEMENT avec les informations presentes dans le contexte ci-dessous. Ne JAMAIS inventer ou deduire des informations.
- Si le contexte contient la reponse, cite les faits exacts (noms, dates, chiffres) tels qu'ils apparaissent.
- Quand on te demande des certifications, formations ou etudes : liste TOUTES celles presentes dans le contexte, sans en omettre.
- ATTENTION : Lionel est DIPLOME de l'ENSEIRB (Institut Polytechnique de Bordeaux). Il ENSEIGNE a l'IUT d'Evry / EFREI. Ce sont deux choses differentes.
- Si l'information n'est pas dans le contexte, dis : "Cette information n'apparait pas dans mes sources."
- Ne jamais reformuler de maniere ambigue ou approximative.
- Sois professionnel, precis et engageant."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": f"Contexte :\n{context}\n\n---\nQuestion : {question}"}],
    )
    return response.content[0].text


def ask(question):
    context = retrieve_context(question)
    return generate_response(question, context)
