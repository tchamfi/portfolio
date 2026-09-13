"""Regression tests for the public knowledge boundary and attributable retrieval."""

import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import doc_loader


class PublicKnowledgeLoaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference_bytes = doc_loader.KNOWLEDGE_PATH.read_bytes()
        cls.reference = cls.reference_bytes.decode("utf-8")
        cls.chunks = doc_loader.load_documents_as_chunks()
        cls.records = {chunk["id"]: chunk for chunk in cls.chunks}

    def test_all_semantic_records_are_complete_and_identifiable(self):
        for prefix, count in (("C", 29), ("E", 7), ("Q", 10)):
            actual = {key for key in self.records if len(key) == 3 and key.startswith(prefix)}
            self.assertEqual(actual, {f"{prefix}{index:02d}" for index in range(1, count + 1)})
        self.assertEqual(doc_loader.get_knowledge_metadata()["counts"], {
            "positioning": 1, "experience": 12, "skill": 29, "case": 7,
            "qa": 10, "tool": 14, "certification": 7, "metric": 6,
        })
        self.assertIn("frontend comme backend", self.records["C01"]["text"])
        self.assertIn("frameworks d’automatisation", self.records["C01"]["text"])
        self.assertNotIn("[C02]", self.records["C01"]["text"])

    def test_personal_role_and_limitations_travel_with_the_skill(self):
        for index in range(1, 30):
            record = self.records[f"C{index:02d}"]
            metadata = record["metadata"]
            self.assertTrue(metadata["role"], record["id"])
            self.assertTrue(metadata["attribution"], record["id"])
            self.assertIn(metadata["role"], record["text"])
            if metadata["scope"]:
                self.assertIn(metadata["scope"], record["text"])
            else:
                # C06 has no explicit limitation in V3; the loader must not
                # invent a restriction merely to populate metadata.
                self.assertEqual(record["id"], "C06")
        self.assertIn("Bruno", self.records["C02"]["text"])
        self.assertIn("rétroactivement", self.records["C02"]["metadata"]["scope"])
        self.assertIn("production", self.records["E03"]["text"])
        self.assertIn("adoptée par les RH", self.records["E03"]["text"])
        self.assertIn("Data Engineers construisent les pipelines", self.records["E02"]["text"])

    def test_sources_are_resolved_including_ranges_without_private_links(self):
        case = self.records["E03"]
        self.assertEqual(case["metadata"]["source_refs"], ["L04", "U03", "D01", "D02", "D03", "D04"])
        self.assertEqual(self.records["Q02"]["metadata"]["source_refs"], ["L06", "L07", "L08", "L09", "U01", "U03"])
        self.assertEqual(self.records["E02"]["metadata"]["competency_refs"], ["C12", "C13", "C14", "C15"])
        for record in self.chunks:
            self.assertTrue(record["metadata"]["sources"], record["id"])
            for source in record["metadata"]["sources"]:
                self.assertIn(source["label"], record["text"])
                self.assertIn(source["id"], record["metadata"]["source_refs"])
            self.assertNotRegex(record["text"], r"https?://|docs/DOC|docs/EYECLOUD")

    def test_policy_source_catalog_prose_and_release_notes_are_not_facts(self):
        marker = "DO_NOT_RETRIEVE_POLICY_SENTINEL"
        modified = self.reference.replace(
            "## 10. Consignes", f"## 10. Consignes {marker}\n\n{marker}\n\nConsignes"
        ).replace("## 11. Note", f"## 11. Note {marker}\n\n{marker}\n\nNote")
        modified = modified.replace("## 1. Sources", f"## 1. Sources {marker}\n\n{marker}\n\nSources")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "skills_public.md"
            path.write_text(modified, encoding="utf-8")
            chunks = doc_loader.load_documents_as_chunks(path)
        self.assertFalse(any(marker in chunk["text"] for chunk in chunks))
        self.assertTrue(all(chunk["metadata"]["section"] in range(2, 10) for chunk in chunks))
        combined = "\n".join(chunk["text"] for chunk in chunks)
        self.assertNotIn("Statuts de correspondance à employer", combined)
        self.assertNotIn("Lors d’une future intégration", combined)

    def test_default_boundary_ignores_documents_and_other_nearby_markdown(self):
        secret_marker = "PRIVATE_OR_LEGACY_DOCUMENT_MUST_NOT_BE_INDEXED"
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            (base / "docs").mkdir()
            (base / "docs" / "internal.md").write_text(secret_marker, encoding="utf-8")
            (base / "other.md").write_text(secret_marker, encoding="utf-8")
            reference = base / "skills_public.md"
            reference.write_bytes(self.reference_bytes)
            with patch.object(doc_loader, "KNOWLEDGE_PATH", reference):
                loaded = doc_loader.load_documents_as_chunks()
            self.assertEqual(len(loaded), len(self.chunks))
            self.assertFalse(any(secret_marker in chunk["text"] for chunk in loaded))
            with self.assertRaises(FileNotFoundError):
                doc_loader.load_documents_as_chunks(base / "docs")
            with self.assertRaises(FileNotFoundError):
                doc_loader.load_documents_as_chunks(base / "missing.md")

    def test_fingerprint_tracks_contents_even_if_timestamp_is_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "skills_public.md"
            path.write_bytes(self.reference_bytes)
            stat = path.stat()
            original = doc_loader.get_knowledge_fingerprint(path)
            self.assertEqual(original, hashlib.sha256(self.reference_bytes).hexdigest())
            path.write_bytes(self.reference_bytes + b"\n")
            os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
            self.assertNotEqual(original, doc_loader.get_knowledge_fingerprint(path))
            self.assertEqual(doc_loader.get_knowledge_metadata(path)["version"], "3.0")

    def test_metrics_and_certificates_retain_provenance_qualifiers(self):
        for record in self.chunks:
            if record["metadata"]["category"] == "metric":
                self.assertIn("résultats rapportés", record["text"])
                self.assertIn("ne constituent pas des mesures recalculées ou auditées", record["text"])
            if record["metadata"]["category"] == "certification":
                self.assertIn("validité administrative actuelle non vérifiée", record["text"])

    def test_malformed_reference_fails_without_old_corpus_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "skills_public.md"
            path.write_text("# Incomplete\nVersion : 3.0", encoding="utf-8")
            with self.assertRaises(ValueError):
                doc_loader.load_documents_as_chunks(path)
            path.write_text(self.reference.replace("U01, L07, L08, L09 ;", "U99, L07, L08, L09 ;"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unknown source"):
                doc_loader.load_documents_as_chunks(path)


if __name__ == "__main__":
    unittest.main()
