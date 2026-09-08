"""
agent.py — Portfolio matching agent
Uses search_chunks() from rag_pipeline (TF-IDF based)
"""

import json
from rag_pipeline import search_chunks
from llm_provider import complete as llm_complete

TOP_K = 10


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
    llm = _get_llm_config()
    system = """Tu es un expert en analyse de fiches de poste IT.
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
}"""
    text, metrics = llm_complete(
        model=llm["model"], system=system,
        user_content=f"Analyse cette fiche de poste :\n\n{job_text}",
        max_tokens=1024, temperature=llm["temp_matching"],
    )
    text = text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text), metrics
    except json.JSONDecodeError:
        return {"raw_analysis": text, "error": "JSON parse failed"}, metrics


def query_rag_profile(queries):
    return search_chunks(queries, top_k=TOP_K)


def compute_matching(job_analysis, profile_context):
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
- gaps_imperatifs : compétences ABSENTES du profil qui sont réellement centrales pour le poste. Ce sont des bloquants.
- gaps_apprecies : compétences ABSENTES du profil qui sont secondaires ou complémentaires pour le poste. Ce sont des nice-to-have.
- Ne te limite pas à repérer des mots-clés comme "requis" ou "apprécié". Juge l'importance réelle de chaque compétence absente à partir du contexte : est-elle dans une section clé de l'offre (titre, résumé, premières lignes) ou noyée dans une longue liste secondaire ? revient-elle plusieurs fois ? est-elle formulée avec une intensité forte ("maîtrise", "expert", "indispensable") ou mentionnée en passant ? une offre peut exiger une compétence sans utiliser un mot comme "requis", et à l'inverse citer une compétence secondaire avec un vocabulaire qui semble strict.
- En cas de doute réel sur l'importance d'une compétence, classe-la plutôt en gaps_apprecies : le bénéfice du doute va au candidat, pas à l'exclusion automatique.

POINTS D'ATTENTION — TON SOUPLE ET CONSTRUCTIF :
- Pour chaque point d'attention, cherche dans le profil l'expérience la plus proche de ce qui manque et cite-la explicitement, même si ce n'est pas un équivalent exact.
- Explique ensuite pourquoi l'écart n'est pas réellement problématique : proximité avec un outil ou une technologie déjà maîtrisée, capacité de montée en compétence démontrée ailleurs dans le profil, nature du manque (théorique vs pratique, périphérique vs central au poste).
- Distingue une compétence adjacente ponctuelle d'une expertise réellement profonde et durable. Si le profil montre qu'une compétence proche est pratiquée depuis longtemps ou de façon répétée sur plusieurs expériences (pas une mention isolée), présente-la comme une expertise solide et directement pertinente, pas comme "une base extensible" ou un simple point de départ. Ne minimise pas une compétence forte pour rester dans un registre uniformément prudent.
- Cette structure (expérience proche + pourquoi ce n'est pas grave) s'applique à CHAQUE point d'attention, sans exception, même quand l'écart est large ou porte sur un sujet central du poste. Un écart plus large mérite une reformulation plus honnête sur son ampleur, jamais une bascule vers un ton d'avertissement ("écart réel à combler rapidement", "point bloquant potentiel", etc.). Si tu ne trouves aucune expérience proche à citer pour un point donné, dis-le explicitement plutôt que de laisser le point sans relativisation ("c'est un sujet neuf pour le candidat, sans équivalent direct dans son parcours à ce jour") : la formulation reste factuelle, jamais alarmiste.
- Ne formule jamais un point d'attention comme si tu citais une phrase prononcée par le candidat (ex. "le candidat le reconnaît lui-même"). C'est toi, l'évaluateur, qui portes le jugement à partir du profil. Reste au style évaluation neutre, jamais au style citation ou aveu.
- Le ton doit rester factuel et honnête, jamais alarmiste. L'objectif est d'aider le lecteur à relativiser un manque, pas de le minimiser artificiellement ni d'inventer une expérience qui n'existe pas.
- Exemple de formulation attendue : "Pas d'expérience directe sur [X], mais une pratique récente de [Y proche] et une capacité de montée en compétence déjà démontrée sur [Z] rendent cet écart facilement comblable."

Réponds au format JSON strict :
{
    "score_global": 85,
    "points_forts": ["liste de 4-5 points forts valorisants"],
    "points_attention": ["liste de 2-3 points d'attention souples : ce qui manque, l'expérience la plus proche dans le profil, et pourquoi ce n'est pas un souci en soi"],
    "gaps_imperatifs": ["compétences absentes réellement centrales pour le poste"],
    "gaps_apprecies": ["compétences absentes secondaires ou complémentaires pour le poste"],
    "arguments_cles": ["3 arguments convaincants pour un recruteur"],
    "conseil_approche": "conseil stratégique pour aborder le poste"
}"""
    user_content = f"Fiche :\n{json.dumps(job_analysis, ensure_ascii=False)}\n\nProfil :\n{profile_context}"
    text, metrics = llm_complete(
        model=llm["model"], system=system_prompt, user_content=user_content,
        max_tokens=llm["max_tokens_matching"], temperature=llm["temp_matching"],
    )
    text = text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text), metrics
    except json.JSONDecodeError:
        return {"raw_matching": text, "error": "JSON parse failed"}, metrics


def draft_response(job_analysis, matching, response_type="email"):
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
    user_content = f"Fiche :\n{json.dumps(job_analysis, ensure_ascii=False)}\n\nMatching :\n{json.dumps(matching, ensure_ascii=False)}"
    text, metrics = llm_complete(
        model=llm["model"], system=instruction, user_content=user_content,
        max_tokens=llm["max_tokens_matching"],
    )
    return text, metrics


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
