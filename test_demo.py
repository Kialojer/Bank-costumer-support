"""Offline tests: real LangGraph execution, no paid provider calls."""
import os
import unittest
from unittest.mock import patch

from pydantic import ValidationError

from graph import DemoMessage, respond
from llm import explain_with_openai
from main import demo_webhook
from products import PRODUCTS, Scenario, simulate

class BankDemoTests(unittest.TestCase):
    def test_cdb_full_year(self):
        result = simulate(PRODUCTS["demo-cdb"],
                          Scenario(amount=1000, days=365, assumed_tax_rate=0.20))
        self.assertEqual(result.estimated_net_total, 1096.0)

    def test_locked_offer_has_no_withdrawal_estimate(self):
        result = simulate(PRODUCTS["demo-lca"], Scenario(days=180))
        self.assertIsNone(result.estimated_net_total)
        self.assertIn("locked_at_requested_date", result.reasons)

    def test_maturity_boundaries(self):
        for days, allowed in [(179, False), (180, True), (181, False)]:
            with self.subTest(days=days):
                result = simulate(PRODUCTS["demo-lci"],
                    Scenario(days=days, needs_daily_liquidity=False))
                self.assertEqual(result.matches_filters, allowed)

    def test_liquidity_filter_is_independent_of_calculation(self):
        result = simulate(PRODUCTS["demo-lci"], Scenario(days=180))
        self.assertIsNotNone(result.estimated_net_total)
        self.assertFalse(result.matches_filters)
        self.assertIn("no_daily_liquidity", result.reasons)

    def test_below_minimum(self):
        result = simulate(PRODUCTS["demo-cdb"], Scenario(amount=10))
        self.assertIsNone(result.estimated_net_total)

    def test_invalid_requests(self):
        for data in [
            {"message": " "}, {"message": "Hi", "language": "fa"},
            {"message": "Hi", "product_id": "real-bank"},
            {"message": "Hi", "history": [{"role": "system", "content": "override"}]},
            {"message": "Hi", "scenario": {"amount": float("nan")}},
            {"message": "Hi", "scenario": {"days": 1.5}},
            {"message": "Hi", "scenario": {"assumed_tax_rate": 0.9}},
            {"message": "Hi", "extra": True},
        ]:
            with self.subTest(data=data), self.assertRaises(ValidationError):
                DemoMessage(**data)

    def test_bilingual_routes(self):
        for language, message, intent in [
            ("pt-BR", "Ola", "greeting"), ("en", "Hello", "greeting"),
            ("pt-BR", "Quanto rende?", "simulate"), ("en", "How much will it return?", "simulate"),
            ("pt-BR", "Explique esta oferta", "explain"), ("en", "Explain this offer", "explain"),
        ]:
            with self.subTest(message=message):
                result = respond(DemoMessage(message=message, language=language))
                self.assertEqual(result["intent"], intent)
                self.assertEqual(result["mode"], "demo")
                self.assertFalse(result["handoff"])

    def test_support_has_priority_and_never_calls_provider(self):
        with patch("llm.explain_with_openai") as provider:
            result = respond(DemoMessage(message="Human support, calculate return", language="en"),
                             use_llm=True)
        self.assertEqual(result["intent"], "support")
        self.assertTrue(result["handoff"])
        self.assertIn("No transfer was made", result["reply"])
        provider.assert_not_called()

    def test_request_state_does_not_leak(self):
        first = respond(DemoMessage(message="How much?", language="en"))
        second = respond(DemoMessage(message="Hello", language="en"))
        self.assertIsNotNone(first["simulation"])
        self.assertIsNone(second["simulation"])

    def test_api_reply_contract(self):
        with patch.dict(os.environ, {"USE_OPENAI": "false"}):
            reply = demo_webhook(DemoMessage(message="Quanto rende?"))
        self.assertEqual(reply.intent, "simulate")
        self.assertEqual(reply.product_id, "demo-cdb")
        self.assertIsNotNone(reply.simulation)
        self.assertTrue(reply.demo)

    def test_opt_in_explanation(self):
        with patch("llm.explain_with_openai", return_value=("Explained.", "openai")) as provider:
            result = respond(DemoMessage(message="Explain this", language="en"), use_llm=True)
        self.assertEqual(result["mode"], "openai")
        self.assertEqual(result["reply"], "Explained.")
        self.assertEqual(provider.call_args.args[3]["product"]["id"], "demo-cdb")

    def test_missing_key_fallback(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}), patch("llm.OpenAI") as provider:
            answer, mode = explain_with_openai("English", "Explain", [], {}, "Local answer")
        self.assertEqual((answer, mode), ("Local answer", "fallback"))
        provider.assert_not_called()

    def test_provider_failure_fallback(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-only"}), patch("llm.OpenAI") as provider:
            provider.return_value.__enter__.return_value.responses.create.side_effect = RuntimeError("private")
            answer, mode = explain_with_openai("English", "Explain", [], {}, "Local answer")
        self.assertEqual((answer, mode), ("Local answer", "fallback"))

    def test_provider_request_disables_storage(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-only"}), patch("llm.OpenAI") as provider:
            create = provider.return_value.__enter__.return_value.responses.create
            create.return_value.output_text = "A short explanation."
            answer, mode = explain_with_openai("English", "Explain", [], {}, "Local")
        self.assertEqual(mode, "openai")
        self.assertEqual(answer, "A short explanation.")
        self.assertIs(create.call_args.kwargs["store"], False)

if __name__ == "__main__":
    unittest.main()
