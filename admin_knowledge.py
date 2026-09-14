"""Owner-facing publication of facts shared by questions and matching."""

from html import escape

import streamlit as st

import knowledge_store as store
from rag_pipeline import ask, search_evidence, get_evidence_by_ids, get_knowledge_status, validate_knowledge_publication


KINDS = {"tool": "Outil", "skill": "Compétence", "language": "Langue",
         "certification": "Formation / certification", "achievement": "Réalisation"}
PRACTICES = {"professional": "Pratique professionnelle", "training": "Formation / prototype",
             "historical": "Pratique dont l’actualité reste à préciser", "unspecified": "Non précisé"}
STATES = {"draft": "Brouillon", "published": "Publié", "archived": "Archivé"}


def _items(value):
    return [part.strip() for part in value.split(",") if part.strip()]


def _error(exc):
    if isinstance(exc, store.KnowledgeError):
        if exc.code == "K422":
            st.error(str(exc))
        else:
            st.error("L’enregistrement n’a pas pu être confirmé. Rechargez la liste avant de réessayer. "
                     f"({exc.code})")
    elif isinstance(exc, ValueError):
        st.error(str(exc))
    else:
        st.error("La publication ne peut pas être confirmée. Actualisez les fiches et vérifiez la correction avant de réessayer.")


def _preview(fields):
    """Display the author's actual statements, without asking an LLM to embellish them."""
    st.markdown("**Information que l’IA pourra utiliser**")
    st.text(fields.get("statement", ""))
    details = [KINDS.get(fields.get("kind"), "Compétence"),
               PRACTICES.get(fields.get("practice"), "Non précisé")]
    if fields.get("companies"):
        details.append(", ".join(fields["companies"]))
    if fields.get("period"):
        details.append(fields["period"])
    st.caption(" · ".join(details))
    if fields.get("limits"):
        st.text("Précisions et limites : " + fields["limits"])
    if fields.get("correction_of"):
        st.caption("Cette fiche corrige uniquement le passage choisi dans une information existante.")


def _refresh_after_publication(message):
    # The common corpus fingerprint invalidates matching sessions and cached
    # evaluations. Clear the owner's old screen immediately as well.
    st.session_state.pop("agent_results", None)
    st.session_state.pop("knowledge_test_result", None)
    st.session_state.knowledge_notice = message
    st.rerun()


def render_knowledge_admin():
    if not st.session_state.get("is_private"):
        return
    st.markdown("### Connaissances IA")
    st.caption("Publiez vos compétences et réalisations pour les intégrer aux réponses et au matching. "
               "Les brouillons restent privés. Décrivez ce que vous avez personnellement fait.")
    notice = st.session_state.pop("knowledge_notice", None)
    if notice:
        st.success(notice)
    if st.button("Actualiser les fiches", key="knowledge_reload"):
        try:
            store.list_facts(force=True)
            st.rerun()
        except store.KnowledgeError as exc:
            _error(exc)
    try:
        facts = store.list_facts()
    except store.KnowledgeError as exc:
        _error(exc)
        return
    by_id = {fact["id"]: fact for fact in facts}
    options = ["new"] + list(by_id)
    pending = st.session_state.pop("knowledge_pending_selection", None)
    if pending in options:
        st.session_state.knowledge_selected = pending
    if st.session_state.get("knowledge_selected") not in options:
        st.session_state.knowledge_selected = "new"

    def label(identifier):
        if identifier == "new":
            return "+ Ajouter une connaissance"
        fact = by_id[identifier]
        return f"{fact['title']} — {STATES.get(fact.get('state'), 'Brouillon')}"

    selected = st.selectbox("Fiche à consulter ou modifier", options,
                            format_func=label, key="knowledge_selected")
    current = by_id.get(selected, {})
    if current.get("state") == "draft" and current.get("has_published_version"):
        st.info("Vos modifications sont en brouillon. La dernière version publiée reste utilisée par l’IA.")
    elif current.get("state") == "archived":
        st.info("Cette fiche est archivée et n’alimente plus les réponses. Vous pouvez préparer une nouvelle version.")
    version = current.get("revision", "new")
    with st.form(f"knowledge_editor_{selected}_{version}"):
        kind = st.selectbox("Type de connaissance", list(KINDS),
            index=list(KINDS).index(current.get("kind", "tool")), format_func=KINDS.get)
        title = st.text_input("Compétence, outil ou réalisation", value=current.get("title", ""), max_chars=160)
        companies = st.text_input("Entreprises concernées (séparées par des virgules)",
                                 value=", ".join(current.get("companies", [])), max_chars=500)
        statement = st.text_area("Ce que j’ai personnellement fait", value=current.get("statement", ""),
            height=130, max_chars=4000,
            placeholder="J’ai utilisé Jira chez GRDF et je l’utilise actuellement chez BNP Paribas Personal Finance.")
        practice = st.selectbox("Nature de la pratique", list(PRACTICES),
            index=list(PRACTICES).index(current.get("practice", "unspecified")), format_func=PRACTICES.get)
        period = st.text_input("Période d’utilisation (facultatif)", value=current.get("period", ""), max_chars=120,
            help="Une période de mission ne prouve pas une utilisation continue de chaque outil.")
        limits = st.text_area("Précisions et limites (facultatif)", value=current.get("limits", ""), max_chars=2000,
            placeholder="Par exemple : suivi des tickets et du backlog ; administration des workflows non pratiquée.")
        keywords = st.text_input("Autres termes utiles pour retrouver cette compétence (facultatif)",
            value=", ".join(current.get("keywords", [])), max_chars=600)
        with st.expander("Corriger une information déjà publiée (facultatif)"):
            st.caption("Pour un simple ajout, laissez ces champs vides. Pour une correction, utilisez la référence "
                       "et copiez exactement le passage à remplacer depuis le test de recherche ci-dessous.")
            correction_of = st.text_input("Référence de la fiche à corriger", value=current.get("correction_of", ""), max_chars=80)
            correction_quote = st.text_area("Passage exact à remplacer", value=current.get("correction_quote", ""), max_chars=4000)
        preview = st.form_submit_button("Voir l’aperçu")
        save = st.form_submit_button("Enregistrer le brouillon")
        publish = st.form_submit_button("Enregistrer et publier", type="primary")
    fields = dict(kind=kind, title=title.strip(), companies=_items(companies), statement=statement.strip(),
                  practice=practice, period=period.strip(), limits=limits.strip(), keywords=_items(keywords),
                  correction_of=correction_of.strip(), correction_quote=correction_quote.strip())
    if preview:
        try:
            chunk = validate_knowledge_publication(dict(current, **fields, id=current.get("id", "K000000000000")))
            _preview(fields)
            with st.expander("Fiche transmise à l’IA"):
                st.text(chunk["text"])
        except (RuntimeError, ValueError) as exc:
            _error(exc)
    if save or publish:
        try:
            if publish:
                validate_knowledge_publication(dict(current, **fields, id=current.get("id", "K000000000000")))
            saved = store.save_draft(fields, fact_id=current.get("id"), expected_revision=current.get("revision"))
            st.session_state.knowledge_pending_selection = saved["id"]
            if publish:
                validate_knowledge_publication(saved, published_facts=store.published_snapshot(force=True)["facts"])
                store.publish_fact(saved["id"], expected_revision=saved["revision"])
                get_knowledge_status()
                _refresh_after_publication("Connaissance publiée : elle est prise en compte par les questions et le matching.")
            else:
                st.session_state.knowledge_notice = "Brouillon enregistré. Il n’est pas encore utilisé par l’IA."
                st.rerun()
        except (RuntimeError, ValueError) as exc:
            _error(exc)

    if current:
        with st.expander("Historique et archivage"):
            st.caption("Restaurer une version prépare un brouillon. La publication reste une action distincte.")
            try:
                history = store.get_history(current["id"])
                revisions = {item["revision"]: item for item in history}
                if revisions:
                    revision = st.selectbox("Version à consulter", list(revisions),
                        format_func=lambda value: f"{revisions[value].get('updated_at', '')} — "
                                                  f"{STATES.get(revisions[value].get('state'), 'Brouillon')}",
                        key=f"knowledge_history_{selected}")
                    _preview(revisions[revision])
                    if st.button("Restaurer cette version en brouillon", key=f"knowledge_restore_{selected}"):
                        store.restore_fact(selected, revision, expected_revision=current["revision"])
                        st.session_state.knowledge_notice = "Version restaurée en brouillon. Vérifiez-la avant publication."
                        st.rerun()
                if current.get("state") != "archived" and st.button("Archiver cette fiche", key=f"knowledge_archive_{selected}"):
                    store.archive_fact(selected, expected_revision=current["revision"])
                    _refresh_after_publication("Fiche archivée : elle ne sera plus utilisée par l’IA.")
            except (store.KnowledgeError, ValueError) as exc:
                _error(exc)

    st.divider()
    st.markdown("**Tester mes connaissances publiées**")
    with st.form("knowledge_test_form"):
        question = st.text_input("Question de vérification", key="knowledge_test_question",
            value="Quels outils Agile ai-je utilisés, et dans quelles entreprises ?", max_chars=2000)
        inspect = st.form_submit_button("Voir les informations retrouvées")
        answer = st.form_submit_button("Tester la réponse IA")
    if inspect or answer:
        try:
            with st.spinner("Vérification des connaissances publiées…"):
                evidence = search_evidence(question, top_k=8)
                text = None
                if answer:
                    text, metrics = ask(question, language="fr")
                    evidence = get_evidence_by_ids(metrics.get("evidence_ids", []))
                st.session_state.knowledge_test_result = {"question": question, "evidence": evidence, "answer": text}
        except Exception:
            st.error("Le test est temporairement indisponible. Vos connaissances enregistrées sont conservées.")
    result = st.session_state.get("knowledge_test_result")
    if result:
        st.caption(result["question"])
        if result["answer"]:
            st.markdown(escape(result["answer"]))
        if not result["evidence"]:
            st.info("Aucune information publiée n’a été retrouvée pour cette question.")
        for item in result["evidence"]:
            with st.expander(f"{item['id']} · {item.get('metadata', {}).get('title', 'Information publiée')}"):
                st.text(item["text"])


def render_correction_form(requirement, language="fr", result_key=""):
    """A private correction becomes a draft; it cannot override a public score."""
    if not st.session_state.get("is_private"):
        return
    identifier = repr((result_key, requirement.get("requirement_id"), requirement.get("text", "")))
    import hashlib
    key = hashlib.sha256(identifier.encode()).hexdigest()[:16]
    with st.expander("Suggest a correction" if language == "en" else "Signaler une correction"):
        with st.form(f"matching_correction_{key}"):
            title = st.text_input("Skill or tool" if language == "en" else "Compétence ou outil",
                value=requirement.get("text", "")[:160], max_chars=160)
            statement = st.text_area("My factual clarification" if language == "en" else "Ma précision factuelle", max_chars=4000)
            companies = st.text_input("Companies (comma-separated)" if language == "en" else "Entreprises (séparées par des virgules)", max_chars=500)
            submit = st.form_submit_button("Save as draft" if language == "en" else "Enregistrer en brouillon")
        if submit:
            try:
                store.save_draft({"kind": "skill", "title": title.strip(), "statement": statement.strip(),
                    "companies": _items(companies), "practice": "unspecified", "period": "", "limits": "",
                    "keywords": [], "correction_of": "", "correction_quote": ""})
                st.success("Draft saved. Review and publish it in Administration → AI knowledge." if language == "en"
                    else "Brouillon enregistré. Relisez-le et publiez-le dans Administration → Connaissances IA.")
            except (store.KnowledgeError, ValueError) as exc:
                _error(exc)
