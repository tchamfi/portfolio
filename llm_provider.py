"""
llm_provider.py — Abstraction multi-fournisseur (Anthropic + OpenAI)

Point d'entree unique : complete(model, system, user_content, max_tokens, temperature)
Route automatiquement vers le bon SDK/la bonne API selon le modele demande,
et retourne toujours (texte, metrics) dans le meme format, quel que soit le
fournisseur — le reste de l'app (agent.py, rag_pipeline.py) n'a pas besoin de
savoir si le modele vient d'Anthropic ou d'OpenAI.
"""

import os
import time


def _secret(key):
    try:
        import streamlit as st
        return st.secrets.get(key, os.getenv(key, ""))
    except Exception:
        return os.getenv(key, "")


def _get_anthropic_key():
    return _secret("ANTHROPIC_API_KEY")


def _get_openai_key():
    return _secret("OPENAI_API_KEY")


# Modeles OpenAI supportes (famille GPT-5.6 : Luna/Terra/Sol, et GPT-6 Astra)
OPENAI_MODELS = ("gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol", "gpt-6-astra")

# Tarifs $ / 1M tokens (input, output) — sert au calcul du cout par interaction
# affiche dans l'onglet Analytics de l'admin.
MODEL_PRICING = {
    "claude-haiku-4-5-20251001": (1.0, 5.0),
    "claude-sonnet-5":           (2.0, 10.0),
    "claude-opus-5":             (5.0, 25.0),
    "gpt-5.6-luna":              (1.0, 6.0),
    "gpt-5.6-terra":             (2.5, 15.0),
    "gpt-5.6-sol":               (5.0, 30.0),
    "gpt-6-astra":               (10.0, 50.0),
}
_DEFAULT_PRICING = (3.0, 15.0)  # fallback si le modele n'est pas dans la table


def is_openai_model(model):
    return (model or "").startswith("gpt-")


def _no_sampling_params(model):
    """Modeles qui n'acceptent plus temperature/top_p : les modeles Anthropic
    recents en raisonnement force, et toute la famille OpenAI GPT-5.6/GPT-6
    (modeles de raisonnement, temperature fixee a 1 cote OpenAI)."""
    anthropic_no_sampling = ("claude-sonnet-5", "claude-opus-4-8", "claude-opus-4-7",
                              "claude-fable-5", "claude-mythos-5")
    if model in OPENAI_MODELS:
        return True
    return any(m in (model or "") for m in anthropic_no_sampling)


def _cost(model, tokens_in, tokens_out):
    cin, cout = MODEL_PRICING.get(model, _DEFAULT_PRICING)
    return round(tokens_in * cin / 1_000_000 + tokens_out * cout / 1_000_000, 6)


# ---------------------------------------------------------------- Anthropic

def _extract_anthropic_text(response):
    """Concatene tous les blocs texte de la reponse, sans supposer que
    content[0] est forcement du texte (un bloc thinking peut passer devant)."""
    parts = []
    for block in getattr(response, "content", []) or []:
        t = getattr(block, "text", None)
        if t:
            parts.append(t)
    return "".join(parts)


def _call_anthropic(model, system, user_content, max_tokens, temperature):
    from anthropic import Anthropic
    client = Anthropic(api_key=_get_anthropic_key())
    kwargs = dict(
        model=model, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": user_content}],
    )
    if temperature is not None and not _no_sampling_params(model):
        kwargs["temperature"] = temperature
    try:
        response = client.messages.create(**kwargs)
    except TypeError as e:
        if "temperature" in str(e) and "temperature" in kwargs:
            kwargs.pop("temperature", None)
            response = client.messages.create(**kwargs)
        else:
            raise
    except Exception as e:
        if "temperature" in str(e).lower() and "temperature" in kwargs:
            kwargs.pop("temperature", None)
            response = client.messages.create(**kwargs)
        else:
            raise
    text = _extract_anthropic_text(response)
    tokens_in = response.usage.input_tokens
    tokens_out = response.usage.output_tokens
    return text, tokens_in, tokens_out


# ------------------------------------------------------------------ OpenAI

def _extract_openai_text(response):
    text = getattr(response, "output_text", None)
    if text:
        return text
    parts = []
    for item in getattr(response, "output", []) or []:
        for c in getattr(item, "content", []) or []:
            t = getattr(c, "text", None)
            if t:
                parts.append(t)
    return "".join(parts)


def _call_openai(model, system, user_content, max_tokens, temperature):
    from openai import OpenAI
    client = OpenAI(api_key=_get_openai_key())
    # Famille GPT-5.6 / GPT-6 : modeles de raisonnement, passent par l'API
    # Responses (pas Chat Completions), utilisent max_output_tokens, et
    # n'acceptent pas de temperature personnalisee (fixee a 1 cote OpenAI).
    # Les tokens de raisonnement interne sont decomptes du meme budget que la
    # reponse visible : un max_tokens hérité d'un appel Claude (souvent 1024-1500)
    # peut donc etre entierement consomme par le raisonnement, laissant une
    # reponse vide. On garantit un plancher pour eviter ce cas.
    effective_max = max(max_tokens, 4000) if model in OPENAI_MODELS else max_tokens
    kwargs = dict(model=model, instructions=system, input=user_content, max_output_tokens=effective_max)
    if model in OPENAI_MODELS:
        kwargs["reasoning"] = {"effort": "low"}  # reponses courtes et rapides, coherent avec l'usage du site
    if temperature is not None and not _no_sampling_params(model):
        kwargs["temperature"] = temperature
    try:
        response = client.responses.create(**kwargs)
    except TypeError as e:
        if "temperature" in str(e) and "temperature" in kwargs:
            kwargs.pop("temperature", None)
            response = client.responses.create(**kwargs)
        else:
            raise
    except Exception as e:
        msg = str(e).lower()
        if "temperature" in msg and "temperature" in kwargs:
            kwargs.pop("temperature", None)
            response = client.responses.create(**kwargs)
        elif "reasoning" in msg and "reasoning" in kwargs:
            kwargs.pop("reasoning", None)
            response = client.responses.create(**kwargs)
        else:
            raise
    text = _extract_openai_text(response)
    usage = getattr(response, "usage", None)
    tokens_in = getattr(usage, "input_tokens", 0) if usage else 0
    tokens_out = getattr(usage, "output_tokens", 0) if usage else 0
    return text, tokens_in, tokens_out


# --------------------------------------------------------------- Point d'entree

def complete(model, system, user_content, max_tokens, temperature=None):
    """Envoie un prompt au modele demande (Anthropic ou OpenAI selon le nom)
    et retourne (texte, metrics). metrics contient toujours tokens_input,
    tokens_output, latence_ms, cout_usd, model — meme format quel que soit
    le fournisseur, pour que l'Analytics de l'admin reste homogene."""
    t0 = time.time()
    if is_openai_model(model):
        text, tokens_in, tokens_out = _call_openai(model, system, user_content, max_tokens, temperature)
    else:
        text, tokens_in, tokens_out = _call_anthropic(model, system, user_content, max_tokens, temperature)
    latence_ms = int((time.time() - t0) * 1000)
    return text, {
        "tokens_input": tokens_in,
        "tokens_output": tokens_out,
        "latence_ms": latence_ms,
        "cout_usd": _cost(model, tokens_in, tokens_out),
        "model": model,
    }
