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

# Le SDK anthropic installe (requirements.txt: anthropic>=0.45.0, sans plafond) peut avoir
# supprime le support de "temperature" independamment du modele demande. Plutot que de deviner
# par nom de modele, on tente l'appel avec temperature et on retente sans si ca echoue precisement
# sur ce parametre (que ce soit un TypeError cote SDK ou une erreur 400 cote API).
def _create_message(client, **kwargs):
    try:
        return client.messages.create(**kwargs)
    except TypeError as e:
        if "temperature" in str(e) and "temperature" in kwargs:
            kwargs = {k: v for k, v in kwargs.items() if k != "temperature"}
            return client.messages.create(**kwargs)
        raise
    except Exception as e:
        if "temperature" in str(e).lower() and "temperature" in kwargs:
            kwargs = {k: v for k, v in kwargs.items() if k != "temperature"}
            return client.messages.create(**kwargs)
        raise

def _supports_temperature(model):
    # Conserve pour compatibilite mais plus utilise directement : voir _create_message ci-dessus.
    _NO_SAMPLING_PARAMS_MODELS = ("claude-sonnet-5", "claude-opus-4-8", "claude-opus-4-7", "claude-fable-5", "claude-mythos-5")
    return not any(m in (model or "") for m in _NO_SAMPLING_PARAMS_MODELS)

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


def _get_llm_config():
    """Get LLM config from Streamlit session or defaults."""
    try:
        import streamlit as st
        cfg = st.session_state.get("config", {})
        return {
            "model": cfg.get("llm_model", "claude-sonnet-5"),
            "temp_chat": float(cfg.get("llm_temp_chat", "1.0")),
            "top_k": int(cfg.get("llm_top_k", "12")),
            "max_tokens_chat": int(cfg.get("llm_max_tokens_chat", "1024")),
        }
    except Exception:
        return {"model": "claude-sonnet-5", "temp_chat": 1.0, "top_k": 12, "max_tokens_chat": 1024}


CLAUDE_INPUT_COST = 3.0 / 1_000_000   # $3 per million input tokens
CLAUDE_OUTPUT_COST = 15.0 / 1_000_000  # $15 per million output tokens


def generate_response(question, context):
    import time
    client = Anthropic(api_key=_get_api_key())
    llm = _get_llm_config()
    system_prompt = """Tu ES Lionel TCHAMFONG. Tu réponds en première personne (je, mon, mes) aux questions des recruteurs et clients.
Règles STRICTES :
- Réponds naturellement comme si tu étais en entretien. Ne JAMAIS dire "d'après mes sources", "le contexte indique", "mes sources", "les informations fournies" ou toute formulation qui révèle que tu es une IA lisant un document.
- Base tes réponses UNIQUEMENT sur les informations du contexte ci-dessous. Ne JAMAIS inventer.
- Cite les faits exacts (noms, dates, chiffres, services AWS) tels qu'ils apparaissent. Sois précis et concret.
- Quand on te demande des certifications, formations ou études : liste TOUTES celles présentes dans le contexte, sans en omettre.
- ATTENTION : Tu es DIPLÔMÉ de l'ENSEIRB (Institut Polytechnique de Bordeaux). Tu ENSEIGNES à l'IUT d'Évry / EFREI. Ce sont deux choses différentes.
- Si l'information n'est pas dans le contexte, dis simplement : "Je vous invite à me contacter directement pour en discuter."
- Sois professionnel, précis, engageant et concret. Donne des exemples réels de tes missions."""

    t0 = time.time()
    kwargs = dict(
        model=llm["model"], max_tokens=llm["max_tokens_chat"],
        system=system_prompt,
        messages=[{"role": "user", "content": f"Contexte :\n{context}\n\n---\nQuestion : {question}"}],
        temperature=llm["temp_chat"],
    )
    response = _create_message(client, **kwargs)
    latence_ms = int((time.time() - t0) * 1000)
    tokens_in = response.usage.input_tokens
    tokens_out = response.usage.output_tokens
    cout = round(tokens_in * CLAUDE_INPUT_COST + tokens_out * CLAUDE_OUTPUT_COST, 6)
    return response.content[0].text, {"tokens_input": tokens_in, "tokens_output": tokens_out, "latence_ms": latence_ms, "cout_usd": cout, "model": llm["model"]}


def ask(question):
    llm = _get_llm_config()
    context = retrieve_context(question, top_k=llm["top_k"])
    text, metrics = generate_response(question, context)
    return text, metrics
