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


def _get_llm_config():
    """Get LLM config from Streamlit session or defaults."""
    try:
        import streamlit as st
        cfg = st.session_state.get("config", {})
        return {
            "model": cfg.get("llm_model", "claude-sonnet-5"),
            "temp_matching": float(cfg.get("llm_temp_matching", "0.2")),
            "max_tokens_matching": int(cfg.get("llm_max_tokens_matching", "1500")),
        }
    except Exception:
        return {"model": "claude-sonnet-5", "temp_matching": 0.2, "max_tokens_matching": 1500}


def analyze_job_posting(job_text):
    client = Anthropic(api_key=_get_api_key())
    llm = _get_llm_config()
    kwargs = dict(
        model=llm["model"], max_tokens=1024, temperature=llm["temp_matching"],
        system="""Tu es un expert en analyse de fiches de poste IT.
Extrais les informations clés au format JSON strict (pas de markdown, pas de backticks).
{
    "titre": "titre du poste",
    "entreprise": "nom ou null",
    "contexte": "résumé en 2 phrases",
    "competences_requises": ["liste", "techniques"],
    "competences_methodologiques": ["Scrum", "SAFe"],
    "experience_demandee": "X ans en Y",
    "points_cles": ["3-5 exigences importantes"],
    "secteur": "secteur",
    "remote_possible": true/false
}""",
        messages=[{"role": "user", "content": f"Analyse cette fiche de poste :\n\n{job_text}"}],
    )
    response, metrics = _timed_call(client, **kwargs)
    text = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text), metrics
    except json.JSONDecodeError:
        return {"raw_analysis": text, "error": "JSON parse failed"}, metrics


def query_rag_profile(queries):
    return search_chunks(queries, top_k=TOP_K)


def compute_matching(job_analysis, profile_context):
    client = Anthropic(api_key=_get_api_key())
    llm = _get_llm_config()
    system_prompt = """Tu es un expert en recrutement IT et en matching de profils senior.
Tu évalues la compatibilité entre un candidat et une offre avec une approche COMMERCIALE et RÉALISTE.

RÈGLES DE SCORING :
- Tu évalues les COMPÉTENCES TRANSFÉRABLES, pas seulement les mots-clés exacts.
  Exemple : expérience Splunk/CloudWatch = transférable vers Datadog/Grafana. Expérience AWS = transférable vers Azure/GCP.
- Un candidat senior qui maîtrise un outil équivalent à celui demandé doit être crédité, pas pénalisé.
- Les compétences méthodologiques (Scrum, pilotage, backlog, roadmap, KPIs) sont hautement transférables entre domaines.
- Le score doit refléter la capacité RÉELLE du candidat à réussir dans le poste, pas un matching mot-à-mot.
- Un profil qui coche 80% des critères avec des compétences transférables sur les 20% restants mérite 80-85, pas 60-70.
- Sois précis et cohérent : pour une même fiche de poste, ton évaluation doit rester stable, pas dispersée.

ÉCHELLE :
- 90-100 : Match quasi parfait, expérience directe sur tous les points
- 80-89 : Très bon match, compétences transférables sur les points manquants
- 70-79 : Bon match avec quelques gaps significatifs
- 60-69 : Match partiel, gaps importants
- <60 : Profil éloigné

ANALYSE DES GAPS — TRÈS IMPORTANT :
- gaps_imperatifs : compétences ABSENTES du profil qui sont marquées comme "requis", "impératif", "obligatoire", "indispensable", "X ans minimum", "maîtrise exigée" dans l'offre. Ce sont des bloquants.
- gaps_apprecies : compétences ABSENTES du profil qui sont marquées comme "apprécié", "un plus", "idéalement", "souhaité", "serait un atout", "connaissance souhaitée" dans l'offre. Ce sont des nice-to-have.
- Si une compétence n'est pas explicitement marquée comme optionnelle dans l'offre, considère-la comme impérative par défaut.

Réponds au format JSON strict :
{
    "score_global": 85,
    "points_forts": ["liste de 4-5 points forts valorisants"],
    "points_attention": ["liste de 2-3 points d'attention honnêtes mais constructifs"],
    "gaps_imperatifs": ["compétences absentes marquées comme requises/obligatoires dans l'offre"],
    "gaps_apprecies": ["compétences absentes marquées comme appréciées/optionnelles dans l'offre"],
    "arguments_cles": ["3 arguments convaincants pour un recruteur"],
    "conseil_approche": "conseil stratégique pour aborder le poste"
}"""
    kwargs = dict(
        model=llm["model"], max_tokens=llm["max_tokens_matching"], temperature=llm["temp_matching"],
        system=system_prompt,
        messages=[{"role": "user", "content": f"Fiche :\n{json.dumps(job_analysis, ensure_ascii=False)}\n\nProfil :\n{profile_context}"}],
    )
    response, metrics = _timed_call(client, **kwargs)
    text = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text), metrics
    except json.JSONDecodeError:
        return {"raw_matching": text, "error": "JSON parse failed"}, metrics


def draft_response(job_analysis, matching, response_type="email"):
    client = Anthropic(api_key=_get_api_key())
    if response_type == "email":
        instruction = """Rédige un email de candidature professionnel, concis (max 250 mots). Signé : Lionel TCHAMFONG.
RÈGLES DE FORMAT STRICTES :
- Texte brut uniquement. AUCUN markdown (pas de **, pas de -, pas de #, pas de ```).
- Pas de listes à puces. Utilise des phrases et paragraphes naturels.
- L'email doit pouvoir être copié-collé directement dans Gmail sans caractères spéciaux.
- Commence par Objet : puis le corps de l'email."""
    else:
        instruction = """Rédige un pitch oral de 2 minutes, confiant et concret.
RÈGLES DE FORMAT : Texte brut uniquement, pas de markdown, pas de listes à puces, pas de caractères spéciaux."""
    llm = _get_llm_config()
    response, metrics = _timed_call(client,
        model=llm["model"], max_tokens=llm["max_tokens_matching"], system=instruction,
        messages=[{"role": "user", "content": f"Fiche :\n{json.dumps(job_analysis, ensure_ascii=False)}\n\nMatching :\n{json.dumps(matching, ensure_ascii=False)}"}],
    )
    return response.content[0].text, metrics


def _timed_call(client, **kwargs):
    """Wrapper to capture tokens and latency on any Claude call. Retries without
    'temperature' if the installed SDK / model rejects it (Sonnet 5 and later no
    longer support sampling params, and requirements.txt pins anthropic>=0.45.0
    without an upper bound, so this can change under us on redeploy)."""
    import time
    COST_IN = 3.0 / 1_000_000
    COST_OUT = 15.0 / 1_000_000
    t0 = time.time()
    try:
        response = client.messages.create(**kwargs)
    except TypeError as e:
        if "temperature" in str(e) and "temperature" in kwargs:
            kwargs = {k: v for k, v in kwargs.items() if k != "temperature"}
            response = client.messages.create(**kwargs)
        else:
            raise
    except Exception as e:
        if "temperature" in str(e).lower() and "temperature" in kwargs:
            kwargs = {k: v for k, v in kwargs.items() if k != "temperature"}
            response = client.messages.create(**kwargs)
        else:
            raise
    return response, {
        "tokens_input": response.usage.input_tokens,
        "tokens_output": response.usage.output_tokens,
        "latence_ms": int((time.time() - t0) * 1000),
        "cout_usd": round(response.usage.input_tokens * COST_IN + response.usage.output_tokens * COST_OUT, 6),
        "model": kwargs.get("model", "")
    }


def _merge_metrics(metrics_list):
    """Sum all metrics across multiple LLM calls."""
    return {
        "tokens_input": sum(m.get("tokens_input", 0) for m in metrics_list),
        "tokens_output": sum(m.get("tokens_output", 0) for m in metrics_list),
        "latence_ms": sum(m.get("latence_ms", 0) for m in metrics_list),
        "cout_usd": round(sum(m.get("cout_usd", 0) for m in metrics_list), 6),
        "model": metrics_list[0].get("model", "") if metrics_list else ""
    }


def run_agent(job_text, response_type="email"):
    results = {"steps": [], "job_analysis": None, "profile_context": None, "matching": None, "response": None, "metrics": {}}
    all_metrics = []

    results["steps"].append("Analyse de la fiche...")
    job_analysis, m1 = analyze_job_posting(job_text)
    all_metrics.append(m1)
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

    matching, m3 = compute_matching(job_analysis, profile_context)
    all_metrics.append(m3)
    results["matching"] = matching

    response_text, m4 = draft_response(job_analysis, matching, response_type)
    all_metrics.append(m4)
    results["response"] = response_text
    results["metrics"] = _merge_metrics(all_metrics)
    return results
