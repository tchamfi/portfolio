"""Optional MCP adapter for the portfolio's public knowledge base.

Install requirements-mcp.txt to run this stdio server. Retrieval needs no
ChromaDB or LLM API key; only ask_lionel calls the configured LLM.
"""

import logging

from mcp.server.fastmcp import FastMCP

from rag_pipeline import ask, get_knowledge_status, retrieve_context


logger = logging.getLogger(__name__)
mcp = FastMCP(name="ask-lionel")


@mcp.tool()
def ask_lionel(question: str, language: str = "fr") -> str:
    """Answer a career question using the public V3 corpus and its references.

    Covers the entire Product Owner and QA career, not just one employer.
    Language is fr or en. Requires a key for the LLM configured in the RAG.
    Live availability and daily rate are not provided by this MCP adapter.
    """
    if language not in ("fr", "en"):
        raise ValueError("language doit être 'fr' ou 'en'.")
    text, _metrics = ask(question, language=language, operational_context=None)
    return text


@mcp.tool()
def search_lionel_docs(keywords: str) -> str:
    """Return relevant public skill/experience excerpts with their references.

    Searches only the approved knowledge corpus. Does not load original
    employer documents, CV_CHUNKS, or a separate persistent Chroma index.
    No LLM API key is needed.
    """
    context = retrieve_context(keywords, top_k=5)
    return context or "Aucun extrait pertinent dans la base publique."


@mcp.tool()
def get_lionel_summary() -> str:
    """Return profile excerpts from the current public corpus without an LLM.

    Excerpts retain their source identifiers and contribution limits.
    """
    context = retrieve_context(
        "profil positionnement parcours Product Owner depuis 2016 "
        "QA IER Bolloré Bouygues Orange Enedis GRDF Essilor EPSA "
        "Generali BNP Paribas",
        top_k=8,
    )
    return context or "Résumé non disponible dans la base publique."


def main():
    # stderr is used for diagnostics; stdout is reserved for the MCP protocol.
    logging.basicConfig(level=logging.INFO)
    get_knowledge_status()
    logger.info("Serveur MCP Ask Lionel prêt ; corpus public chargé.")
    mcp.run()


if __name__ == "__main__":
    main()
