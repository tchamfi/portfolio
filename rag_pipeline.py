"""
rag_pipeline.py — RAG pipeline for Ask Lionel
Compatible with chromadb 0.5.x
"""

import os
import chromadb
from anthropic import Anthropic
from cv_data import CV_CHUNKS
from doc_loader import load_documents_as_chunks

COLLECTION_NAME = "lionel_cv"
TOP_K = 12

_client = None
_collection = None


def _get_api_key():
    try:
        import streamlit as st
        return st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))
    except Exception:
        return os.getenv("ANTHROPIC_API_KEY", "")


def create_chroma_collection():
    global _client, _collection

    # Reuse existing if already created (handles Streamlit reruns)
    if _collection is not None:
        return _collection

    _client = chromadb.EphemeralClient()

    # Collect all chunks
    all_ids, all_docs, all_meta = [], [], []

    for c in CV_CHUNKS:
        all_ids.append(c["id"])
        all_docs.append(c["text"])
        all_meta.append(c["metadata"])
    print(f"[RAG] {len(CV_CHUNKS)} manual chunks")

    doc_chunks = load_documents_as_chunks()
    for c in doc_chunks:
        all_ids.append(c["id"])
        all_docs.append(c["text"])
        all_meta.append(c["metadata"])
    print(f"[RAG] {len(doc_chunks)} document chunks")

    _collection = _client.get_or_create_collection(name=COLLECTION_NAME)
    _collection.upsert(ids=all_ids, documents=all_docs, metadatas=all_meta)
    print(f"[RAG] Total: {len(all_ids)} chunks indexed")
    return _collection


def get_collection():
    global _collection
    if _collection is None:
        create_chroma_collection()
    return _collection


def retrieve_context(question, top_k=TOP_K):
    collection = get_collection()
    results = collection.query(query_texts=[question], n_results=top_k)
    parts = []
    for i, doc in enumerate(results["documents"][0]):
        source = results["metadatas"][0][i].get("source", "cv_data.py")
        parts.append(f"[Source {i+1} - {source}]\n{doc}")
    return "\n\n---\n\n".join(parts)


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
