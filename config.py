"""
config.py — Constants, fallback config, welcome messages, helpers
"""

import streamlit as st

PRIVATE_CODE = "tchamfi"

FALLBACK_CONFIG = {
    "tjm": "650 - 750", "disponibilite": "Immediat", "remote": "IDF + Remote",
    "show_tjm": True, "show_phone": True,
    "linkedin": "https://www.linkedin.com/in/lionel-tchamfong-productowner/",
    "email": "tchamfong@gmail.com", "phone": "+33 6 65 34 96 56",
    "calendly": "https://calendly.com/tchamfong",
    "profil_p1": "Product Owner / Product Manager Senior avec 15+ ans d'experience en IT.",
    "profil_p2": "J'aide les organisations a concevoir et piloter des produits digitaux.",
    "profil_p3": "Certifie CSPO, CSM, AWS Cloud Practitioner et Databricks Fundamentals.",
    "profil_p4": "Enseignant vacataire en methodologies Agile.",
    "profil_p1_en": "Senior PO/PM with 15+ years of IT experience.",
    "profil_p2_en": "I help organizations design and deliver digital products.",
    "profil_p3_en": "Certified CSPO, CSM, AWS Cloud Practitioner and Databricks.",
    "profil_p4_en": "Agile lecturer at IUT d'Evry / EFREI.",
    "metric1_label": "Experience", "metric1_value": "15+ years", "metric1_desc": "Product & Tech Leadership",
    "metric2_label": "Delivery", "metric2_value": "35+ releases", "metric2_desc": "Products shipped to production",
    "metric3_label": "International", "metric3_value": "Europe & India", "metric3_desc": "Cross-border coordination",
    "metric4_label": "Platforms", "metric4_value": "Cloud, APIs & Data", "metric4_desc": "AWS, Azure, Databricks",
    "exp": [], "case_studies": [],
    "show_profil": True, "show_metrics": True, "show_case_studies": True, "show_parcours": True, "show_recos": True,
    "hero_name": "Lionel TCHAMFONG",
    "hero_title": "Senior Product Owner — Data Platforms, APIs & AI",
    "hero_tagline_fr": "Je concois et pilote des plateformes data, APIs et produits IA dans des environnements internationaux complexes.",
    "hero_tagline_en": "I design and scale data platforms, APIs and AI-powered products in complex international environments.",
    "hero_badges": "CSPO,CSM,Cloud,Data,GenAI",
}

WELCOME_FR = """Bonjour ! Je suis l'assistant IA de Lionel TCHAMFONG.

Posez-moi vos questions, par exemple :
- "Quelle est son experience en data platforms ?"
- "A-t-il deja travaille a l'international ?"
- "Quelles certifications possede-t-il ?"
- "Quel est son TJM et sa disponibilite ?"

Je réponds en me basant sur son parcours réel."""

WELCOME_EN = """Hello! I'm Lionel TCHAMFONG's AI assistant.

Ask me anything, for example:
- "What is his experience with data platforms?"
- "Has he worked internationally?"
- "What certifications does he hold?"
- "What is his daily rate and availability?"

I answer based on his actual career history."""

CHEVRON_SVG = '<svg viewBox="0 0 24 24"><path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6z"/></svg>'


def get_config_context():
    cfg = st.session_state.config
    lang = st.session_state.get("lang", "fr")
    if lang == "en":
        lines = ["CRITICAL INSTRUCTION: You are Lionel TCHAMFONG. You MUST answer ENTIRELY in English. Every word in English. First person (I, my). Formal tone (you, your). No # characters."]
    else:
        lines = ["INSTRUCTION : Tu es Lionel TCHAMFONG. Reponds ENTIEREMENT en francais. Premiere personne (je, mon). Vouvoiement (vous, votre). Pas de #. Paragraphes naturels."]
    lines.append(f"TJM : {cfg.get('tjm', '')} euros/jour")
    lines.append(f"Disponibilite : {cfg.get('disponibilite', '')}")
    lines.append(f"Mode : {cfg.get('remote', '')}")
    exp_list = cfg.get("exp", [])
    if isinstance(exp_list, list):
        ec = [e["company"] for e in exp_list if e.get("status") == "En cours"]
        et = [e["company"] for e in exp_list if e.get("status") == "Terminee"]
        if ec: lines.append(f"En cours : {', '.join(ec)}")
        if et: lines.append(f"Terminees : {', '.join(et)}")
    return "\n[INFO]\n" + "\n".join(lines)


def swap(lst, i, j):
    if 0 <= i < len(lst) and 0 <= j < len(lst):
        lst[i], lst[j] = lst[j], lst[i]
