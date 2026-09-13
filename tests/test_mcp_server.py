"""MCP adapter contract without installing its optional transport dependency."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch


class FakeFastMCP:
    def __init__(self, **kwargs):
        self.run = Mock()

    def tool(self):
        return lambda function: function


class MCPContractTests(unittest.TestCase):
    def setUp(self):
        self.rag = types.ModuleType("rag_pipeline")
        self.rag.ask = Mock(return_value=("Réponse [C01]", {"model": "test"}))
        self.rag.retrieve_context = Mock(return_value="[C01] Stratégie de test")
        self.rag.get_knowledge_status = Mock(return_value={"version": "V3"})
        fastmcp = types.ModuleType("mcp.server.fastmcp")
        fastmcp.FastMCP = FakeFastMCP
        fake_modules = {
            "mcp": types.ModuleType("mcp"),
            "mcp.server": types.ModuleType("mcp.server"),
            "mcp.server.fastmcp": fastmcp,
            "rag_pipeline": self.rag,
        }
        path = Path(__file__).resolve().parents[1] / "mcp_server.py"
        spec = importlib.util.spec_from_file_location("mcp_adapter_under_test", path)
        self.adapter = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, fake_modules), patch.dict("os.environ", {}, clear=True):
            spec.loader.exec_module(self.adapter)

    def test_question_uses_shared_rag_and_language(self):
        self.assertEqual(self.adapter.ask_lionel("What is your QA experience?", "en"), "Réponse [C01]")
        self.rag.ask.assert_called_once_with(
            "What is your QA experience?", language="en", operational_context=None
        )

    def test_invalid_language_does_not_trigger_llm(self):
        with self.assertRaises(ValueError):
            self.adapter.ask_lionel("Question", "de")
        self.rag.ask.assert_not_called()

    def test_search_and_summary_work_without_llm_or_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertIn("[C01]", self.adapter.search_lionel_docs("QA"))
            self.assertIn("[C01]", self.adapter.get_lionel_summary())
        self.rag.ask.assert_not_called()
        self.assertEqual(self.rag.retrieve_context.call_count, 2)

    def test_no_match_is_explicit(self):
        self.rag.retrieve_context.return_value = ""
        self.assertIn("Aucun extrait", self.adapter.search_lionel_docs("inconnu"))

    def test_startup_does_not_require_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            self.adapter.main()
        self.rag.get_knowledge_status.assert_called_once_with()
        self.adapter.mcp.run.assert_called_once_with()
        self.rag.ask.assert_not_called()


if __name__ == "__main__":
    unittest.main()
