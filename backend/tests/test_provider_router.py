import os
import unittest
from unittest.mock import patch

from app.provider_router import list_providers


class ProviderRouterTests(unittest.TestCase):
    def test_provider_catalog_does_not_expose_credentials(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "secret-test-value"}, clear=True):
            providers = list_providers()
        self.assertTrue(next(p for p in providers if p["id"] == "gemini")["enabled"])
        self.assertNotIn("secret-test-value", repr(providers))
        self.assertEqual(next(p for p in providers if p["id"] == "wan22_local")["kind"], "video")

    def test_text_providers_are_registered(self):
        ids = {p["id"] for p in list_providers()}
        self.assertTrue({"gemini", "groq", "openrouter", "wan22_local"}.issubset(ids))


if __name__ == "__main__":
    unittest.main()
