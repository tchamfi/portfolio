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

RÈGLE DE STABILITÉ — IMPORTANTE :
Pour competences_requises, competences_methodologiques, competences_optionnelles et points_cles,
reprends les termes EXACTS utilisés dans la fiche de poste (mêmes mots, même casse, pas de
synonyme, pas de traduction, pas de reformulation, pas de regroupement de plusieurs termes en un
seul). Le but est que la même fiche produise toujours la même extraction, pour que la recherche
qui suit dans le profil retombe systématiquement sur les mêmes résultats.

RÈGLE SUR competences_optionnelles — IMPORTANTE :
Si la fiche contient une section clairement marquée comme optionnelle ("Optional Skills", "Nice
to have", "Apprécié", "Un plus", "Souhaité", etc.), liste ICI les compétences de cette section,
et NULLE PART AILLEURS (ne les remets pas dans competences_requises). Si la fiche ne distingue
pas explicitement de section optionnelle, laisse ce champ vide — ne devine pas.

{
    "titre": "titre du poste",
    "entreprise": "nom ou null",
    "contexte": "résumé en 2 phrases",
    "competences_requises": ["liste", "techniques"],
    "competences_methodologiques": ["Scrum", "SAFe"],
    "competences_optionnelles": ["compétences listées dans une section explicitement optionnelle, sinon []"],
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

RÈGLES D'ÉVALUATION DES COMPÉTENCES :
- Tu évalues les COMPÉTENCES TRANSFÉRABLES, pas seulement les mots-clés exacts.
  Exemple : expérience Splunk/CloudWatch = transférable vers Datadog/Grafana. Expérience AWS = transférable vers Azure/GCP.
- Un candidat senior qui maîtrise un outil équivalent à celui demandé doit être crédité, pas pénalisé.
- Les compétences méthodologiques (Scrum, pilotage, backlog, roadmap, KPIs) sont hautement transférables entre domaines.

TON RÔLE ICI SE LIMITE À CLASSER, PAS À NOTER :
Tu ne calcules PAS de score toi-même — un score calculé par un modèle de langage n'est pas fiable
pour de l'arithmétique. Ton seul travail est de dresser la liste complète des entrées de
competences_requises et competences_methodologiques de la fiche (chaque entrée comptée une seule
fois, sans doublon), et pour chacune, de déterminer si le profil la couvre (directement ou via une
compétence réellement transférable), ou si elle est absente. Chaque entrée absente est ensuite
classée gaps_imperatifs ou gaps_apprecies selon les critères ci-dessous. Le score final sera
calculé automatiquement par l'application à partir de ta classification — n'inclus pas de champ
score_global dans ta réponse.

ANALYSE DES GAPS — TRÈS IMPORTANT :
- gaps_imperatifs : compétences ABSENTES du profil qui sont réellement centrales pour le poste. Ce sont des bloquants.
- gaps_apprecies : compétences ABSENTES du profil qui sont secondaires ou complémentaires pour le poste. Ce sont des nice-to-have.
- Ne te limite pas à repérer des mots-clés comme "requis" ou "apprécié". Juge l'importance réelle de chaque compétence absente à partir du contexte : est-elle dans une section clé de l'offre (titre, résumé, premières lignes) ou noyée dans une longue liste secondaire ? revient-elle plusieurs fois ? est-elle formulée avec une intensité forte ("maîtrise", "expert", "indispensable") ou mentionnée en passant ? une offre peut exiger une compétence sans utiliser un mot comme "requis", et à l'inverse citer une compétence secondaire avec un vocabulaire qui semble strict.
- Si l'offre distingue explicitement une section "requis"/"required" d'une section "apprécié"/"optional"/"nice to have", respecte cette distinction en priorité.
- En cas de doute réel sur l'importance d'une compétence, classe-la plutôt en gaps_apprecies : le bénéfice du doute va au candidat, pas à l'exclusion automatique.
- Cette classification doit elle-même être stable : pour la même fiche et le même profil, une compétence donnée doit toujours atterrir dans la même catégorie (gap_imperatif ou gap_apprecie), pas tantôt l'une tantôt l'autre.

RÈGLE SPÉCIFIQUE AU PROFIL PRODUCT OWNER — À APPLIQUER AVANT DE CLASSER UNE COMPÉTENCE TECHNIQUE :
Le candidat est Product Owner / Product Manager, pas développeur. Distingue deux natures de compétences :
- Compétences cœur de métier PO (backlog, priorisation, stakeholders, méthodologie Agile, vision produit, KPIs, roadmap, animation d'équipe) : classe-les normalement, aucune pondération particulière ici.
- Compétences techniques/outillage (frameworks, langages, architectures, plateformes cloud, briques IA spécifiques, etc.) que l'offre présente comme un sujet à piloter, comprendre, ou pour dialoguer avec les équipes techniques (verbes/tournures comme "familiarité avec", "compréhension de", "à l'aise avec", "collaborer avec les ingénieurs sur", "capable d'échanger sur") : même absentes du profil, classe-les en gaps_apprecies plutôt qu'en gaps_imperatifs. Un PO n'est pas censé les implémenter lui-même, seulement en comprendre les enjeux pour piloter le produit.
- Exception : si l'offre exige explicitement une pratique développeur ou hands-on de cette compétence technique précise (verbes comme "coder", "développer", "implémenter vous-même", "écrire du code", "expérience de développement direct"), traite-la alors comme n'importe quelle autre compétence requise, sans cette pondération PO.
- En cas de doute sur le niveau d'exigence réel, relis la formulation exacte de l'offre (le verbe utilisé, son intensité) plutôt que de supposer par défaut un niveau élevé.

POINTS D'ATTENTION — TON SOUPLE ET CONSTRUCTIF :
- Pour chaque point d'attention, cherche dans le profil l'expérience la plus proche de ce qui manque et cite-la explicitement, même si ce n'est pas un équivalent exact.
- Explique ensuite pourquoi l'écart n'est pas réellement problématique : proximité avec un outil ou une technologie déjà maîtrisée, capacité de montée en compétence démontrée ailleurs dans le profil, nature du manque (théorique vs pratique, périphérique vs central au poste).
- Distingue une compétence adjacente ponctuelle d'une expertise réellement profonde et durable. Si le profil montre qu'une compétence proche est pratiquée depuis longtemps ou de façon répétée sur plusieurs expériences (pas une mention isolée), présente-la comme une expertise solide et directement pertinente, pas comme "une base extensible" ou un simple point de départ. Ne minimise pas une compétence forte pour rester dans un registre uniformément prudent.
- Cette structure (expérience proche + pourquoi ce n'est pas grave) s'applique à CHAQUE point d'attention, sans exception, même quand l'écart est large ou porte sur un sujet central du poste. Un écart plus large mérite une reformulation plus honnête sur son ampleur, jamais une bascule vers un ton d'avertissement ("écart réel à combler rapidement", "point bloquant potentiel", etc.). Si tu ne trouves aucune expérience proche à citer pour un point donné, dis-le explicitement plutôt que de laisser le point sans relativisation ("c'est un sujet neuf pour le candidat, sans équivalent direct dans son parcours à ce jour") : la formulation reste factuelle, jamais alarmiste.
- Ne formule jamais un point d'attention comme si tu citais une phrase prononcée par le candidat (ex. "le candidat le reconnaît lui-même"). C'est toi, l'évaluateur, qui portes le jugement à partir du profil. Reste au style évaluation neutre, jamais au style citation ou aveu.
- Le ton doit rester factuel et honnête, jamais alarmiste. L'objectif est d'aider le lecteur à relativiser un manque, pas de le minimiser artificiellement ni d'inventer une expérience qui n'existe pas.
- Exemple de formulation attendue : "Pas d'expérience directe sur [X], mais une pratique récente de [Y proche] et une capacité de montée en compétence déjà démontrée sur [Z] rendent cet écart facilement comblable."

Réponds au format JSON strict, SANS le champ score_global (il est calculé ailleurs) :
{
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
        matching = json.loads(text)
        matching = _enforce_explicit_optional(matching, job_analysis)
        matching["score_global"] = _compute_score(matching, job_analysis)
        return matching, metrics
    except json.JSONDecodeError:
        return {"raw_matching": text, "error": "JSON parse failed"}, metrics


def _enforce_explicit_optional(matching, job_analysis):
    """Filet de securite deterministe : si l'offre marque explicitement une
    section optionnelle (competences_optionnelles, extrait par
    analyze_job_posting), tout gap qui y correspond est force en
    gaps_apprecies, meme si le modele l'avait classe en gaps_imperatifs. Une
    section marquee 'Optional' dans l'offre ne doit jamais dependre de la
    memoire du modele plusieurs etapes de raisonnement plus loin."""
    optional = job_analysis.get("competences_optionnelles", []) if job_analysis else []
    if not optional:
        return matching
    optional_lower = [o.strip().lower() for o in optional if o and o.strip()]

    def is_optional(item):
        item_l = (item or "").strip().lower()
        return any(o in item_l or item_l in o for o in optional_lower)

    imp = matching.get("gaps_imperatifs", []) or []
    misclassified = [g for g in imp if is_optional(g)]
    if misclassified:
        matching["gaps_imperatifs"] = [g for g in imp if g not in misclassified]
        matching["gaps_apprecies"] = (matching.get("gaps_apprecies", []) or []) + misclassified
    return matching


def _compute_score(matching, job_analysis=None):
    """Calcule le score de matching de facon deterministe en Python, a partir
    du nombre de gaps que le modele a classes — jamais via un score que le
    modele calculerait et rapporterait lui-meme (peu fiable pour de
    l'arithmetique, verifie empiriquement sur des cas reels).

    Le poids de chaque gap est proportionnel au nombre total de competences
    listees dans l'offre (une offre courte penalise plus par gap qu'une offre
    longue), mais toujours contenu entre un plancher et un plafond fixes pour
    ne jamais devenir absurde dans un sens ou dans l'autre."""
    n_imperatifs = len(matching.get("gaps_imperatifs", []) or [])
    n_apprecies = len(matching.get("gaps_apprecies", []) or [])

    total = 0
    if job_analysis:
        total = len(job_analysis.get("competences_requises", []) or []) \
              + len(job_analysis.get("competences_methodologiques", []) or [])
    if total <= 0:
        total = max(n_imperatifs + n_apprecies, 1)

    poids_imperatif = max(8, min(18, 70 / total))
    poids_apprecie = max(3, min(8, 30 / total))

    score = 100 - (n_imperatifs * poids_imperatif) - (n_apprecies * poids_apprecie)
    return max(15, min(100, round(score)))


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
    for k in ["competences_requises", "competences_methodologiques", "competences_optionnelles"]:
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
