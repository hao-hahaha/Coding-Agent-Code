import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import alpha_factory_v1.backend.llm_provider as llm


class TestEmbedderFallback(unittest.TestCase):
    def test_openai_failure_falls_back(self) -> None:
        os.environ["OPENAI_API_KEY"] = "sk-test"
        llm._OPENAI_KEY = "sk-test"
        llm._sync_embed.cache_clear()
        with patch.object(llm.openai.Embedding, "create", side_effect=llm.openai.OpenAIError("boom")) as mock_create:

            class _Vec(list):
                def tolist(self):
                    return list(self)

            fake_mod = SimpleNamespace(
                SentenceTransformer=lambda *_: SimpleNamespace(
                    encode=lambda text, normalize_embeddings=True: _Vec([0.1, 0.2])
                )
            )
            with patch.dict(sys.modules, {"sentence_transformers": fake_mod}):
                vec = llm._sync_embed("hi")
        mock_create.assert_called_once()
        self.assertEqual(vec, [0.1, 0.2])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
