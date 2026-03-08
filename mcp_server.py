"""
Serveur MCP "Ask Lionel" — Expose le RAG CV comme un outil pour Claude Desktop.
"""

import os
import sys
import chromadb
from anthropic import Anthropic
from mcp.server.fastmcp import FastMCP

# Ajoute le dossier du projet au path pour les imports
PROJECT_DIR = "/Users/emirogconsulting/rag-cv-chatbot"
sys.path.insert(0, PROJECT_DIR)

from cv_data import CV_CHUNKS
from doc_loader import load_documents_as_chunks

# --- Configuration ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
COLLECTION_NAME = "lionel_cv"
CHROMA_PATH = os.path.join(PROJECT_DIR, "chroma_db")
TOP_K = 10


def log(msg):
    """Log vers stderr pour ne pas polluer le protocole MCP sur stdout."""
    print(msg, file=sys.stderr)


# --- Initialise le serveur MCP ---
mcp = FastMCP(
    name="ask-lionel",
)


# --- Fonctions RAG ---

def init_chroma():
    """Initialise ChromaDB avec les chunks du CV + documents."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "CV et documents de Lionel TCHAMFONG"}
    )

    # Chunks manuels
    log(f"[ask-lionel] {len(CV_CHUNKS)} chunks manuels (cv_data.py)")
    collection.add(
        ids=[c["id"] for c in CV_CHUNKS],
        documents=[c["text"] for c in CV_CHUNKS],
        metadatas=[c["metadata"] for c in CV_CHUNKS],
    )

    # Documents auto-charges depuis ./docs/
    original_cwd = os.getcwd()
    os.chdir(PROJECT_DIR)
    doc_chunks = load_documents_as_chunks()
    os.chdir(original_cwd)

    if doc_chunks:
        collection.add(
            ids=[c["id"] for c in doc_chunks],
            documents=[c["text"] for c in doc_chunks],
            metadatas=[c["metadata"] for c in doc_chunks],
        )

    total = len(CV_CHUNKS) + len(doc_chunks)
    log(f"[ask-lionel] {total} chunks indexes dans ChromaDB")
    return collection


def retrieve_context(question: str, top_k: int = TOP_K) -> str:
    """Recherche les chunks les plus pertinents."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(COLLECTION_NAME)

    results = collection.query(
        query_texts=[question],
        n_results=top_k,
    )

    context_parts = []
    for i, doc in enumerate(results["documents"][0]):
        source = results["metadatas"][0][i].get("source", "cv_data.py")
        context_parts.append(f"[Source {i+1} - {source}]\n{doc}")

    return "\n\n---\n\n".join(context_parts)


def generate_rag_response(question: str, context: str) -> str:
    """Genere une reponse via Claude en s'appuyant sur le contexte RAG."""
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    system_prompt = """Tu es un assistant qui repond aux questions sur le profil professionnel de Lionel TCHAMFONG, 
Product Owner Senior specialise GenAI & Data.
Reponds UNIQUEMENT a partir du contexte fourni. Sois factuel, concis et professionnel.
Si l'information n'est pas dans le contexte, dis-le honnetement."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": f"Contexte :\n{context}\n\n---\nQuestion : {question}"
        }],
    )
    return response.content[0].text


# --- Outils MCP exposes a Claude Desktop ---

@mcp.tool()
def ask_lionel(question: str) -> str:
    """
    Pose une question sur le profil professionnel de Lionel TCHAMFONG.
    
    Utilise cet outil pour repondre a toute question sur :
    - Son experience professionnelle (EPSA, EssilorLuxottica, GRDF, Enedis, Orange, Bouygues)
    - Ses competences techniques (Cloud, Data, GenAI, Agile)
    - Ses certifications (CSPO, CSM, AWS, Databricks)
    - Son parcours de formation (ingenieur telecom, Jedha Bootcamp)
    - Ses projets (IA prediction pollution, plateforme Data EPSA, EyeCloud)
    - Sa disponibilite, son TJM, ses langues
    
    Args:
        question: La question sur le profil de Lionel
    
    Returns:
        La reponse basee sur le CV et les documents de Lionel
    """
    log(f"[ask-lionel] Question recue : {question}")
    context = retrieve_context(question)
    response = generate_rag_response(question, context)
    log(f"[ask-lionel] Reponse generee ({len(response)} chars)")
    return response


@mcp.tool()
def search_lionel_docs(keywords: str) -> str:
    """
    Recherche dans les documents de Lionel par mots-cles.
    
    Retourne les extraits les plus pertinents sans interpretation,
    utile pour obtenir des details techniques bruts.
    
    Args:
        keywords: Mots-cles de recherche (ex: "medallion bronze silver gold")
    
    Returns:
        Les extraits de documents les plus pertinents
    """
    log(f"[ask-lionel] Recherche : {keywords}")
    context = retrieve_context(keywords, top_k=5)
    return f"Extraits trouves pour '{keywords}' :\n\n{context}"


@mcp.tool()
def get_lionel_summary() -> str:
    """
    Retourne un resume du profil de Lionel TCHAMFONG.
    Utile comme point de depart avant d'approfondir un sujet.
    
    Returns:
        Le resume du profil professionnel de Lionel
    """
    for chunk in CV_CHUNKS:
        if chunk["id"] == "profil_resume":
            return chunk["text"]
    return "Resume non disponible."


# --- Lancement ---
if __name__ == "__main__":
    if not ANTHROPIC_API_KEY:
        log("[ask-lionel] ERREUR : Variable ANTHROPIC_API_KEY non definie.")
        sys.exit(1)

    log("[ask-lionel] Indexation des documents...")
    init_chroma()

    log("[ask-lionel] Serveur MCP 'Ask Lionel' demarre !")
    mcp.run()
