"""Unit tests cho codebase/ai.py (fake, Claude/Anthropic và OpenAI qua HTTP mock)."""
import io
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codebase"))

import ai  # noqa: E402
import tracing  # noqa: E402


class _FakeResponse:
    def __init__(self, payload: dict):
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._raw

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class AiConnectorTests(unittest.TestCase):
    def test_fake_provider_returns_contract_and_records_trace(self):
        with mock.patch.object(ai, "MODEL_PROVIDER", "fake"):
            tracing.begin("test_fake")
            res = ai.call_model("sys", "dòng 1\nxin chào")
            summary, _ = tracing.end()
        self.assertEqual(res["model"], "fake")
        self.assertEqual(res["tokens_in"], 0)
        self.assertEqual(res["tokens_out"], 0)
        self.assertIn("xin chào", res["text"])
        self.assertEqual(summary["model_calls"], 1)

    def test_api_base_supports_demo_configuration_and_specific_override(self):
        payload = {"usage": {"prompt_tokens": 12, "completion_tokens": 5},
                   "choices": [{"message": {"content": "Bản nháp"}}]}
        with mock.patch.dict("os.environ", {"API_BASE": "https://example.test/v1/"}, clear=True):
            with mock.patch.object(ai, "post_json", return_value=payload) as post:
                ai.call_openai("system", "user", "demo-model")
                self.assertEqual(post.call_args.args[0], "https://example.test/v1/chat/completions")
            with mock.patch.dict("os.environ", {"OPENAI_BASE_URL": "https://specific.test/chat"}):
                with mock.patch.object(ai, "post_json", return_value=payload) as post:
                    ai.call_openai("system", "user", "demo-model")
                    self.assertEqual(post.call_args.args[0], "https://specific.test/chat")
        local = {"message": {"content": "Bản nháp"}, "prompt_eval_count": 7, "eval_count": 3}
        with mock.patch.dict("os.environ", {"API_BASE": "http://localhost:11435/"}, clear=True):
            with mock.patch.object(ai, "post_json", return_value=local) as post:
                result = ai.call_ollama("system", "user", "demo-model")
                self.assertEqual(post.call_args.args[0], "http://localhost:11435/api/chat")
                self.assertEqual(result["tokens_in"], 7)

    def test_anthropic_and_claude_alias_parse_usage_and_headers(self):
        payload = {
            "content": [{"type": "text", "text": "Kế hoạch "}, {"type": "text", "text": "hợp lệ"}],
            "usage": {"input_tokens": 123, "output_tokens": 45},
        }
        for provider in ("anthropic", "claude"):
            captured = {}

            def fake_urlopen(req, timeout=60):
                captured["url"] = req.full_url
                captured["headers"] = dict(req.header_items())
                captured["body"] = json.loads(req.data.decode("utf-8"))
                return _FakeResponse(payload)

            with (
                mock.patch.object(ai, "MODEL_PROVIDER", provider),
                mock.patch.object(ai, "MODEL_NAME", "claude-haiku-4-5-20251001"),
                mock.patch.object(ai, "API_KEY", "sk-ant-test"),
                mock.patch("urllib.request.urlopen", side_effect=fake_urlopen),
            ):
                tracing.begin("test_claude")
                res = ai.call_model("system prompt", "user prompt")
                summary, _ = tracing.end()

            self.assertEqual(captured["url"], ai.URL_CLAUDE)
            self.assertEqual(captured["headers"]["X-api-key"], "sk-ant-test")
            self.assertEqual(captured["headers"]["Anthropic-version"], "2023-06-01")
            self.assertEqual(captured["body"]["system"], "system prompt")
            self.assertEqual(res, {
                "text": "Kế hoạch hợp lệ",
                "model": "claude-haiku-4-5-20251001",
                "tokens_in": 123,
                "tokens_out": 45,
            })
            self.assertEqual(summary["tokens_in"], 123)
            self.assertEqual(summary["tokens_out"], 45)

    def test_openai_provider_parses_usage_and_headers(self):
        payload = {
            "choices": [{"message": {"content": "Trả lời từ OpenAI"}}],
            "usage": {"prompt_tokens": 210, "completion_tokens": 64},
        }
        captured = {}

        def fake_urlopen(req, timeout=60):
            captured["url"] = req.full_url
            captured["headers"] = dict(req.header_items())
            captured["body"] = json.loads(req.data.decode("utf-8"))
            return _FakeResponse(payload)

        with (
            mock.patch.object(ai, "MODEL_PROVIDER", "openai"),
            mock.patch.object(ai, "MODEL_NAME", "gpt-4o-mini"),
            mock.patch.object(ai, "API_KEY", "sk-openai-test"),
            mock.patch("urllib.request.urlopen", side_effect=fake_urlopen),
        ):
            res = ai.call_model("sys", "hello")

        self.assertEqual(captured["url"], ai.URL_OPENAI)
        self.assertEqual(captured["headers"]["Authorization"], "Bearer sk-openai-test")
        self.assertEqual(captured["body"]["messages"][0], {"role": "system", "content": "sys"})
        self.assertEqual(res, {
            "text": "Trả lời từ OpenAI",
            "model": "gpt-4o-mini",
            "tokens_in": 210,
            "tokens_out": 64,
        })

    def test_ollama_provider_without_api_key_and_usage_counts(self):
        payload = {
            "message": {"content": "Phân công xong"},
            "prompt_eval_count": 88,
            "eval_count": 32,
        }
        captured = {}

        def fake_urlopen(req, timeout=60):
            captured["url"] = req.full_url
            captured["timeout"] = timeout
            captured["body"] = json.loads(req.data.decode("utf-8"))
            return _FakeResponse(payload)

        with (
            mock.patch.object(ai, "MODEL_PROVIDER", "ollama"),
            mock.patch.object(ai, "MODEL_NAME", "qwen2.5:7b"),
            mock.patch.object(ai, "API_KEY", ""),
            mock.patch("urllib.request.urlopen", side_effect=fake_urlopen),
        ):
            res = ai.call_model("sys", "xin chào")

        self.assertEqual(captured["url"], ai.URL_OLLAMA)
        self.assertEqual(captured["timeout"], 300)
        self.assertFalse(captured["body"]["stream"])
        self.assertEqual(res, {
            "text": "Phân công xong",
            "model": "qwen2.5:7b",
            "tokens_in": 88,
            "tokens_out": 32,
        })

    def test_gemini_provider_parses_usage_including_thoughts_tokens(self):
        payload = {
            "candidates": [{
                "content": {
                    "parts": [
                        {"text": "Suy nghĩ nội bộ", "thought": True},
                        {"text": "Bản nháp "},
                        {"text": "ca trực"},
                    ]
                }
            }],
            "usageMetadata": {
                "promptTokenCount": 150,
                "candidatesTokenCount": 40,
                "thoughtsTokenCount": 60,
            },
        }
        captured = {}

        def fake_urlopen(req, timeout=60):
            captured["url"] = req.full_url
            captured["headers"] = dict(req.header_items())
            captured["body"] = json.loads(req.data.decode("utf-8"))
            return _FakeResponse(payload)

        with (
            mock.patch.object(ai, "MODEL_PROVIDER", "gemini"),
            mock.patch.object(ai, "MODEL_NAME", "gemini-2.5-flash"),
            mock.patch.object(ai, "API_KEY", "AIza-test"),
            mock.patch("urllib.request.urlopen", side_effect=fake_urlopen),
        ):
            res = ai.call_model("system prompt", "user prompt")

        self.assertEqual(
            captured["url"],
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
        )
        self.assertEqual(captured["headers"]["X-goog-api-key"], "AIza-test")
        self.assertEqual(captured["body"]["systemInstruction"], {"parts": [{"text": "system prompt"}]})
        self.assertEqual(res, {
            "text": "Bản nháp ca trực",
            "model": "gemini-2.5-flash",
            "tokens_in": 150,
            "tokens_out": 100,
        })

    def test_missing_key_or_model_raises_runtime_error(self):
        with (
            mock.patch.object(ai, "MODEL_PROVIDER", "openai"),
            mock.patch.object(ai, "MODEL_NAME", "gpt-4o-mini"),
            mock.patch.object(ai, "API_KEY", ""),
        ):
            with self.assertRaises(RuntimeError):
                ai.call_model("sys", "hi")

        with (
            mock.patch.object(ai, "MODEL_PROVIDER", "anthropic"),
            mock.patch.object(ai, "MODEL_NAME", ""),
            mock.patch.object(ai, "API_KEY", "sk-test"),
        ):
            with self.assertRaises(RuntimeError):
                ai.call_model("sys", "hi")

    def test_http_error_surfaces_runtime_error(self):
        err = urllib.error.HTTPError(
            ai.URL_OPENAI, 401, "Unauthorized", {}, io.BytesIO(b'{"error":"bad key"}')
        )
        with (
            mock.patch.object(ai, "MODEL_PROVIDER", "openai"),
            mock.patch.object(ai, "MODEL_NAME", "gpt-4o-mini"),
            mock.patch.object(ai, "API_KEY", "bad"),
            mock.patch("urllib.request.urlopen", side_effect=err),
        ):
            with self.assertRaises(RuntimeError) as ctx:
                ai.call_model("sys", "hi")
        self.assertIn("HTTP 401", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
