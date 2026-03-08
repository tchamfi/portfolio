"""
agent.py — Portfolio matching agent
Uses search_chunks() from rag_pipeline (TF-IDF based)
"""

import os, json
from anthropic import Anthropic
from rag_pipeline import search_chunks

TOP_K = 10


def _get_api_key():
    try:
        import streamlit as st
        return st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))
    except Exception:
        return os.getenv("ANTHROPIC_API_KEY", "")


def analyze_job_posting(job_text):
    client = Anthropic(api_key=_get_api_key())
    response = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=1024,
        system="""Tu es un expert en analyse de fiches de poste IT.
Extrais les informations cles au format JSON strict (pas de markdown, pas de backticks).
{
    "titre": "titre du poste",
    "entreprise": "nom ou null",
    "contexte": "resume en 2 phrases",
    "competences_requises": ["liste", "techniques"],
    "competences_methodologiques": ["Scrum", "SAFe"],
    "experience_demandee": "X ans en Y",
    "points_cles": ["3-5 exigences importantes"],
    "secteur": "secteur",
    "remote_possible": true/false
}""",
        messages=[{"role": "user", "content": f"Analyse cette fiche de poste :\n\n{job_text}"}],
    )
    text = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw_analysis": text, "error": "JSON parse failed"}


def query_rag_profile(queries):
    return search_chunks(queries, top_k=TOP_K)


def compute_matching(job_analysis, profile_context):
    client = Anthropic(api_key=_get_api_key())
    response = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=1500,
        system="""Tu es un expert en matching de profils IT.
Reponds au format JSON strict :
{
    "score_global": 85,
    "points_forts": ["liste"],
    "points_attention": ["liste"],
    "competences_manquantes": ["liste"],
    "arguments_cles": ["3 arguments convaincants"],
    "conseil_approche": "conseil strategique"
}""",
        messages=[{"role": "user", "content": f"Fiche :\n{json.dumps(job_analysis, ensure_ascii=False)}\n\nProfil :\n{profile_context}"}],
    )
    text = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw_matching": text, "error": "JSON parse failed"}


def draft_response(job_analysis, matching, response_type="email"):
    client = Anthropic(api_key=_get_api_key())
    if response_type == "email":
        instruction = """Redige un email de candidature professionnel, concis (max 250 mots). Signe : Lionel TCHAMFONG.
REGLES DE FORMAT STRICTES :
- Texte brut uniquement. AUCUN markdown (pas de **, pas de -, pas de #, pas de ```).
- Pas de listes a puces. Utilise des phrases et paragraphes naturels.
- L'email doit pouvoir etre copie-colle directement dans Gmail sans caracteres speciaux.
- Commence par Objet : puis le corps de l'email."""
    else:
        instruction = """Redige un pitch oral de 2 minutes, confiant et concret.
REGLES DE FORMAT : Texte brut uniquement, pas de markdown, pas de listes a puces, pas de caracteres speciaux."""
    response = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=1500, system=instruction,
        messages=[{"role": "user", "content": f"Fiche :\n{json.dumps(job_analysis, ensure_ascii=False)}\n\nMatching :\n{json.dumps(matching, ensure_ascii=False)}"}],
    )
    return response.content[0].text


def run_agent(job_text, response_type="email"):
    results = {"steps": [], "job_analysis": None, "profile_context": None, "matching": None, "response": None}

    results["steps"].append("Analyse de la fiche...")
    job_analysis = analyze_job_posting(job_text)
    results["job_analysis"] = job_analysis

    queries = []
    for k in ["competences_requises", "competences_methodologiques"]:
        v = job_analysis.get(k, [])
        if v: queries.append(" ".join(v[:5]))
    for p in job_analysis.get("points_cles", [])[:3]:
        queries.append(p)
    if job_analysis.get("secteur"): queries.append(f"experience {job_analysis['secteur']}")
    if job_analysis.get("titre"): queries.append(job_analysis["titre"])
    if not queries: queries = ["Product Owner", "competences techniques"]

    profile_context = query_rag_profile(queries)
    results["profile_context"] = profile_context

    matching = compute_matching(job_analysis, profile_context)
    results["matching"] = matching

    results["response"] = draft_response(job_analysis, matching, response_type)
    return results
