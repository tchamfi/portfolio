"""
Agent Portfolio — Analyse une fiche de poste, interroge le RAG de Lionel,
et rédige une réponse personnalisée.

Utilise LangGraph pour l'orchestration et les outils.
"""

import os
import sys
import json
from typing import Annotated, TypedDict

from anthropic import Anthropic
import chromadb

# Ajoute le projet au path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

from cv_data import CV_CHUNKS
from doc_loader import load_documents_as_chunks

# --- Configuration ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CHROMA_PATH = os.path.join(PROJECT_DIR, "chroma_db")
COLLECTION_NAME = "lionel_cv"
TOP_K = 10


# ============================================================
# OUTILS DE L'AGENT
# ============================================================

def analyze_job_posting(job_text: str) -> dict:
    """
    Outil 1 : Analyse une fiche de poste et extrait les exigences clés.
    Retourne un dict structuré avec les compétences demandées, le contexte, etc.
    """
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system="""Tu es un expert en analyse de fiches de poste IT.
Extrais les informations clés au format JSON strict (pas de markdown, pas de backticks).
Le JSON doit contenir :
{
    "titre": "titre du poste",
    "entreprise": "nom de l'entreprise ou null",
    "contexte": "résumé du contexte en 2 phrases",
    "competences_requises": ["liste", "des", "compétences", "techniques"],
    "competences_methodologiques": ["Scrum", "SAFe", etc.],
    "experience_demandee": "X ans en Y",
    "points_cles": ["les 3-5 exigences les plus importantes"],
    "secteur": "secteur d'activité",
    "remote_possible": true/false ou null
}""",
        messages=[{
            "role": "user",
            "content": f"Analyse cette fiche de poste :\n\n{job_text}"
        }],
    )

    text = response.content[0].text.strip()
    # Nettoie les backticks si présents
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw_analysis": text, "error": "Parsing JSON échoué"}


def query_rag_profile(queries: list[str]) -> str:
    """
    Outil 2 : Interroge le RAG avec plusieurs requêtes pour trouver
    les expériences et compétences qui matchent.
    """
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception:
        return "ERREUR : Base ChromaDB non initialisée. Lance d'abord Streamlit ou le MCP server."

    all_results = []
    seen_ids = set()

    for query in queries:
        results = collection.query(
            query_texts=[query],
            n_results=TOP_K,
        )

        for i, doc in enumerate(results["documents"][0]):
            chunk_id = results["ids"][0][i]
            if chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                source = results["metadatas"][0][i].get("source", "cv_data.py")
                distance = results["distances"][0][i] if results.get("distances") else None
                all_results.append({
                    "id": chunk_id,
                    "source": source,
                    "text": doc,
                    "distance": distance,
                })

    # Trie par pertinence (distance la plus faible en premier)
    if all_results and all_results[0].get("distance") is not None:
        all_results.sort(key=lambda x: x["distance"] or 999)

    # Garde les 15 meilleurs résultats
    top_results = all_results[:15]

    context = "\n\n---\n\n".join(
        f"[{r['source']}]\n{r['text']}" for r in top_results
    )
    return context


def compute_matching(job_analysis: dict, profile_context: str) -> dict:
    """
    Outil 3 : Calcule le matching entre la fiche de poste et le profil.
    Retourne un score et une analyse détaillée.
    """
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system="""Tu es un expert en matching de profils IT.
Analyse l'adéquation entre la fiche de poste et le profil du candidat.
Réponds au format JSON strict (pas de markdown, pas de backticks) :
{
    "score_global": 85,
    "points_forts": ["liste des points où le profil matche parfaitement"],
    "points_attention": ["liste des points où le profil est moins aligné"],
    "competences_manquantes": ["compétences demandées mais absentes du profil"],
    "arguments_cles": ["les 3 arguments les plus convaincants pour le recruteur"],
    "conseil_approche": "conseil stratégique pour la candidature"
}""",
        messages=[{
            "role": "user",
            "content": f"""Fiche de poste analysée :
{json.dumps(job_analysis, ensure_ascii=False, indent=2)}

Profil du candidat (Lionel TCHAMFONG) :
{profile_context}"""
        }],
    )

    text = response.content[0].text.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw_matching": text, "error": "Parsing JSON échoué"}


def draft_response(job_analysis: dict, matching: dict, response_type: str = "email") -> str:
    """
    Outil 4 : Rédige une réponse personnalisée (email ou pitch).
    """
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    if response_type == "email":
        instruction = """Rédige un email de candidature professionnel en français.
L'email doit :
- Être concis (max 250 mots)
- Accrocher dès la première phrase avec un élément différenciant
- Mettre en avant les 3 arguments clés du matching
- Mentionner le TJM (650-750 euros) si pertinent
- Terminer par une proposition de call
- Ton : professionnel mais pas corporate, montrer de l'énergie
- Signer : Lionel TCHAMFONG"""
    else:
        instruction = """Rédige un pitch oral de 2 minutes en français.
Le pitch doit :
- Commencer par une accroche percutante
- Structurer les arguments du plus impactant au moins impactant
- Inclure un exemple concret par argument
- Terminer par une question ouverte pour engager la conversation
- Ton : confiant, concret, orienté résultats"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system=instruction,
        messages=[{
            "role": "user",
            "content": f"""Fiche de poste :
{json.dumps(job_analysis, ensure_ascii=False, indent=2)}

Matching avec le profil de Lionel :
{json.dumps(matching, ensure_ascii=False, indent=2)}

Rédige la réponse."""
        }],
    )

    return response.content[0].text


# ============================================================
# AGENT PRINCIPAL — ORCHESTRATION
# ============================================================

def run_agent(job_text: str, response_type: str = "email") -> dict:
    """
    Agent principal qui orchestre les 4 étapes.
    
    Args:
        job_text: Le texte de la fiche de poste
        response_type: "email" ou "pitch"
    
    Returns:
        Dict avec toutes les étapes et résultats
    """
    results = {
        "steps": [],
        "job_analysis": None,
        "profile_context": None,
        "matching": None,
        "response": None,
    }

    # --- ÉTAPE 1 : Analyse de la fiche de poste ---
    results["steps"].append("Analyse de la fiche de poste...")
    job_analysis = analyze_job_posting(job_text)
    results["job_analysis"] = job_analysis
    results["steps"].append(f"Fiche analysee : {job_analysis.get('titre', 'N/A')} - {job_analysis.get('entreprise', 'N/A')}")

    # --- ÉTAPE 2 : Construction des requêtes RAG intelligentes ---
    results["steps"].append("Construction des requetes RAG...")
    rag_queries = []

    # Requêtes basées sur les compétences requises
    competences = job_analysis.get("competences_requises", [])
    if competences:
        rag_queries.append(" ".join(competences[:5]))

    # Requêtes basées sur les compétences méthodologiques
    methodo = job_analysis.get("competences_methodologiques", [])
    if methodo:
        rag_queries.append(" ".join(methodo))

    # Requêtes basées sur les points clés
    points_cles = job_analysis.get("points_cles", [])
    for point in points_cles[:3]:
        rag_queries.append(point)

    # Requête sur le secteur
    secteur = job_analysis.get("secteur", "")
    if secteur:
        rag_queries.append(f"experience {secteur}")

    # Requête générale sur le titre
    titre = job_analysis.get("titre", "")
    if titre:
        rag_queries.append(titre)

    # Fallback si aucune requête
    if not rag_queries:
        rag_queries = ["Product Owner experience", "competences techniques"]

    results["steps"].append(f"{len(rag_queries)} requetes RAG generees")

    # --- ÉTAPE 3 : Interrogation du RAG ---
    results["steps"].append("Interrogation du RAG...")
    profile_context = query_rag_profile(rag_queries)
    results["profile_context"] = profile_context
    results["steps"].append(f"Contexte recupere ({len(profile_context)} chars)")

    # --- ÉTAPE 4 : Matching ---
    results["steps"].append("Calcul du matching profil vs fiche de poste...")
    matching = compute_matching(job_analysis, profile_context)
    results["matching"] = matching
    score = matching.get("score_global", "N/A")
    results["steps"].append(f"Score de matching : {score}/100")

    # --- ÉTAPE 5 : Rédaction de la réponse ---
    results["steps"].append(f"Redaction de la reponse ({response_type})...")
    response = draft_response(job_analysis, matching, response_type)
    results["response"] = response
    results["steps"].append("Reponse generee !")

    return results


# --- Test en standalone ---
if __name__ == "__main__":
    if not ANTHROPIC_API_KEY:
        print("Erreur : ANTHROPIC_API_KEY non definie")
        print("Lance : export ANTHROPIC_API_KEY='ta-cle'")
        sys.exit(1)

    # Fiche de poste test
    test_job = """
    Product Owner GenAI - Paris
    
    Nous recherchons un Product Owner expérimenté pour piloter notre squad GenAI.
    
    Responsabilités :
    - Transformer les opportunités IA en features et user stories actionnables
    - Travailler au quotidien avec les AI Engineers et Software Engineers
    - Challenger les choix d'architecture (RAG, Agents, LLM)
    - Coordonner avec les autres squads produit
    - Garantir une vraie agilité (pas du Scrum cosmétique)
    
    Profil recherché :
    - 5+ ans d'expérience en Product Ownership
    - Expérience sur des plateformes techniques (API, Cloud, Data)
    - Compréhension des architectures GenAI (RAG, Agents, MCP)
    - Certifié CSPO ou équivalent
    - Expérience de coordination multi-squads
    - Anglais courant
    
    Stack : Azure, Python, LangChain, ChromaDB
    Méthodologie : Scrum, SAFe
    TJM : selon profil
    """

    print("Agent Portfolio - Test")
    print("=" * 60)
    results = run_agent(test_job, response_type="email")

    print("\n--- ÉTAPES ---")
    for step in results["steps"]:
        print(f"  > {step}")

    print("\n--- ANALYSE ---")
    print(json.dumps(results["job_analysis"], ensure_ascii=False, indent=2))

    print("\n--- MATCHING ---")
    print(json.dumps(results["matching"], ensure_ascii=False, indent=2))

    print("\n--- RÉPONSE ---")
    print(results["response"])
