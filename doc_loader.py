"""Load the public skills reference as complete, attributable knowledge blocks.

The application reads one explicitly selected Markdown file. Project documents,
uploaded files and legacy CV chunks are never discovered recursively or loaded as
a fallback. Policy and release-note sections are not retrieval evidence.
"""

from collections import Counter
import hashlib
from pathlib import Path
import re


KNOWLEDGE_PATH = Path(__file__).resolve().parent / "knowledge" / "skills_public.md"
INDEXED_SECTIONS = frozenset({2, 3, 4, 5, 6, 7, 8, 9})
CATEGORY_LABELS = {
    "skill": "Compétence / skill",
    "case": "Cas professionnel / professional experience",
    "qa": "Question-réponse / reference answer",
    "experience": "Mission et parcours / career experience",
    "tool": "Outil et niveau de pratique / tools and scope of practice",
    "certification": "Formation et certification / education and certification",
    "positioning": "Positionnement professionnel / professional profile",
    "metric": "Résultat rapporté / reported achievement",
}


def _read_reference(path=None):
    """An optional explicit file path supports tests; directories are rejected."""
    selected = KNOWLEDGE_PATH if path is None else Path(path)
    if selected.suffix.lower() != ".md" or not selected.is_file():
        raise FileNotFoundError(f"Public Markdown knowledge file not found: {selected}")
    raw = selected.read_bytes()
    return selected, raw, raw.decode("utf-8-sig")


def get_knowledge_fingerprint(path=None) -> str:
    """Return a content SHA-256, independent of file timestamps and cwd."""
    return hashlib.sha256(_read_reference(path)[1]).hexdigest()


def _version(text):
    match = re.search(r"^Version\s*:\s*([^\s—]+)", text, re.MULTILINE)
    if not match:
        raise ValueError("Knowledge reference must declare its version")
    return match.group(1)


def _sections(text):
    headings = list(re.finditer(r"^## (\d+)\. (.+)$", text, re.MULTILINE))
    return {
        int(heading.group(1)): (
            heading.group(2),
            text[heading.end():headings[i + 1].start() if i + 1 < len(headings) else len(text)].strip(),
        )
        for i, heading in enumerate(headings)
    }


def _table_rows(body):
    """Return data rows only; the corpus uses simple, unescaped Markdown tables."""
    rows = []
    in_table = False
    for line in body.splitlines():
        if not line.strip().startswith("|"):
            in_table = False
            continue
        cells = [part.strip() for part in line.strip().strip("|").split("|")]
        if not in_table:
            in_table = True
            continue
        if all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells):
            continue
        rows.append(cells)
    return rows


def _without_table(body):
    return "\n".join(line for line in body.splitlines() if not line.strip().startswith("|")).strip()


def _reference_ids(text, prefixes="LUD"):
    """Expand both explicit IDs and ranges such as 'D01 à D04'."""
    expanded = text
    pattern = rf"\b([{prefixes}])(\d{{2}})\s*(?:à|[-–])\s*\1(\d{{2}})\b"
    for match in re.finditer(pattern, text):
        start, end = int(match.group(2)), int(match.group(3))
        if 0 <= end - start < 100:
            replacement = " ".join(f"{match.group(1)}{i:02d}" for i in range(start, end + 1))
            expanded = expanded.replace(match.group(0), replacement)
    return list(dict.fromkeys(re.findall(rf"\b[{prefixes}]\d{{2}}\b", expanded)))


def _field(body, *labels):
    for label in labels:
        for line in body.splitlines():
            clean = line.replace("**", "").strip()
            match = re.match(rf"{re.escape(label)}\s*:\s*(.+)", clean, re.IGNORECASE)
            if match:
                return match.group(1).strip()
    return ""


def _source_catalog(sections):
    return {
        row[0]: {"id": row[0], "label": row[1], "scope": row[2]}
        for row in _table_rows(sections.get(1, ("", ""))[1])
        if len(row) == 3 and re.fullmatch(r"[LUD]\d{2}", row[0])
    }


def _headed_blocks(body, prefix):
    headings = list(re.finditer(rf"^### ({prefix}\d{{2}}) — (.+)$", body, re.MULTILINE))
    for i, heading in enumerate(headings):
        end = headings[i + 1].start() if i + 1 < len(headings) else len(body)
        yield heading.group(1), heading.group(2), body[heading.end():end].strip()


def load_documents_as_chunks(path=None) -> list[dict]:
    """Return complete Markdown records in the former CV_CHUNKS shape.

    Each record has ``id``, ``text`` and structured ``metadata``. Skill Cxx,
    case Exx and answer Qxx identifiers are stable across corpus versions.
    No character overlap is used: attribution and limitations stay together.
    Missing/malformed knowledge fails explicitly instead of serving old facts.
    """
    selected, raw, text = _read_reference(path)
    version = _version(text)
    fingerprint = hashlib.sha256(raw).hexdigest()
    sections = _sections(text)
    if not INDEXED_SECTIONS.issubset(sections):
        raise ValueError("Knowledge reference is missing a required content section (2–9)")
    catalog = _source_catalog(sections)
    chunks = []

    def add(identifier, title, body, category, section, refs=None, role="", scope=""):
        reference_ids = _reference_ids(body) if refs is None else refs
        unknown = set(reference_ids) - catalog.keys()
        if unknown:
            raise ValueError(f"Unknown source references in {identifier}: {sorted(unknown)}")
        sources = [dict(catalog[key]) for key in reference_ids]
        role = _field(body, "Rôle", "Rôle de Lionel", "Répartition du travail") or role
        scope = _field(body, "Périmètre", "Portée") or scope
        attribution = _field(body, "Attribution")
        keywords = _field(body, "Mots-clés") or title
        provenance = "\n".join(
            f"- {source['id']} : {source['label']} — {source['scope']}" for source in sources
        )
        record_text = f"[{identifier}] {title}\nCatégorie : {CATEGORY_LABELS[category]}\n\n{body}"
        if role and not _field(body, "Rôle", "Rôle de Lionel", "Répartition du travail"):
            record_text += f"\n\nRôle documenté : {role}"
        if scope and not _field(body, "Périmètre", "Portée"):
            record_text += f"\n\nPérimètre et limites : {scope}"
        if provenance:
            record_text += f"\n\nProvenance publique :\n{provenance}"
        chunks.append({
            "id": identifier,
            "text": record_text,
            "metadata": {
                "category": category,
                "source": selected.name,
                "doc_name": "Référentiel public de compétences de Lionel Tchamfong",
                "title": title,
                "section": section,
                "knowledge_version": version,
                "knowledge_fingerprint": fingerprint,
                "role": role,
                "scope": scope,
                "attribution": attribution,
                "source_refs": reference_ids,
                "sources": sources,
                "competency_refs": _reference_ids(body, "C"),
                "keywords": keywords,
            },
        })

    add("P01", sections[2][0], sections[2][1], "positioning", 2,
        refs=["L01", "U01", "U02", "U03"])

    # Career rows have no source column: these mappings follow the explicit
    # employer scopes in the reference catalog, not technology keyword matches.
    career_sources = {
        "BNP Paribas": ["L02"], "Generali": ["L03"], "EPSA": ["L04", "U02", "U03"],
        "EssilorLuxottica": ["L05"], "GRDF": ["L06"], "Enedis": ["L06"],
        "Orange": ["L07"], "Bouygues": ["L08"], "IER": ["L09"],
        "Ansaldo": ["L10"], "Homerider": ["L11"], "UQAM": ["L11"],
    }
    career_scope = _without_table(sections[3][1])
    for index, row in enumerate(_table_rows(sections[3][1]), 1):
        period, employer_role, contributions = row
        refs = next((ids for employer, ids in career_sources.items() if employer in employer_role), None)
        if refs is None:
            raise ValueError(f"A source mapping is required for career row: {employer_role}")
        body = f"Période : {period}\nOrganisation et rôle : {employer_role}\nContributions : {contributions}"
        add(f"EXP{index:02d}", employer_role, body, "experience", 3,
            refs=refs, role=employer_role.split(" — ", 1)[-1], scope=career_scope)

    for section, prefix, category in ((4, "C", "skill"), (5, "E", "case"), (9, "Q", "qa")):
        for identifier, title, body in _headed_blocks(sections[section][1], prefix):
            add(identifier, title, body, category, section)

    for index, row in enumerate(_table_rows(sections[6][1]), 1):
        tool, practice, refs = row
        add(f"T{index:02d}", tool, f"Outil ou domaine : {tool}\nPratique : {practice}",
            "tool", 6, refs=_reference_ids(refs), role=practice,
            scope="Ne pas attribuer chaque outil à toutes les missions ni déduire une durée de pratique.")

    certification_scope = _without_table(sections[7][1])
    for index, row in enumerate(_table_rows(sections[7][1]), 1):
        qualification, description = row
        refs = ["L11"] if qualification.startswith(("Diplôme", "Jedha")) else ["L01"]
        add(f"F{index:02d}", qualification, f"Élément : {qualification}\nInformation : {description}",
            "certification", 7, refs=refs, role="Formation ou certification mentionnée dans le profil",
            scope=certification_scope)

    metric_scope = _without_table(sections[8][1])
    for index, row in enumerate(_table_rows(sections[8][1]), 1):
        result, experience, refs = row
        add(f"M{index:02d}", f"{experience} — {result}",
            f"Résultat rapporté dans le profil : {result}\nExpérience : {experience}",
            "metric", 8, refs=_reference_ids(refs), scope=metric_scope)

    identifiers = [chunk["id"] for chunk in chunks]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Duplicate knowledge block identifiers")
    for category in ("skill", "case", "qa"):
        if not any(chunk["metadata"]["category"] == category for chunk in chunks):
            raise ValueError(f"No {category} records found in knowledge reference")
    return chunks


def get_knowledge_metadata(path=None) -> dict:
    """Describe the indexed corpus for diagnostics and administration."""
    chunks = load_documents_as_chunks(path)
    first = chunks[0]["metadata"]
    return {
        "version": first["knowledge_version"],
        "fingerprint": first["knowledge_fingerprint"],
        "source": first["source"],
        "counts": dict(Counter(chunk["metadata"]["category"] for chunk in chunks)),
        "chunk_count": len(chunks),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(get_knowledge_metadata(), ensure_ascii=False, indent=2))
