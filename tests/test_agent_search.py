"""CPU-only tests using the real Lagent dispatcher and scripted model output."""

import asyncio
import io
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import requests
from lagent.schema import ActionStatusCode

from server.web_configs import WEB_CONFIGS
from server.base.modules.agent.agent_worker import get_agent_prompt
from server.base.modules.agent.parallel_search import MCP_URL, USER_AGENT, ParallelSearchAction
from server.base.modules.agent.search_provider import get_search_provider


SOURCE = "https://www.example.com/carrier/policy?region=cn&lang=zh"
SEARCH_TEXT = json.dumps({"results": [{"url": SOURCE, "excerpts": ["配送政策，预计 2–3 天。"]}]}, ensure_ascii=False)


class ScriptedModel:
    available_models = ["scripted-model"]

    def chat_completions_v1(self, **kwargs):
        self.prompt = kwargs["messages"]
        yield {"choices": [{"delta": {"content": (
            '<|action_start|><|plugin|>\n'
            '{"name":"ParallelSearchAction","parameters":{"query":"顺丰 杭州 配送 政策"}}'
            '<|action_end|>\n'
        )}}]}


class AgentSearchTests(unittest.TestCase):
    def setUp(self):
        self.config = patch.multiple(WEB_CONFIGS, ENABLE_AGENT=True, AGENT_SEARCH_PROVIDER="auto",
                                     AGENT_WEATHER_API_KEY=None, AGENT_DELIVERY_TIME_API_KEY=None)
        self.config.start()
        self.addCleanup(self.config.stop)
        self.sent = []
        self.content_type = "application/json"
        self.search_result = {"content": [{"type": "text", "text": SEARCH_TEXT}]}
        self.failure = None
        self.http_status = 200
        self.mutate_message = lambda message: message
        self.send_patch = patch.object(requests.Session, "send", self.send)
        self.send_patch.start()
        self.addCleanup(self.send_patch.stop)

    def send(self, request, **kwargs):
        self.sent.append((request, kwargs))
        body = json.loads(request.body)
        if self.failure and body["method"] == "tools/call":
            raise self.failure
        response = requests.Response()
        response.status_code = self.http_status
        response.headers["Content-Type"] = self.content_type
        if body["method"] == "initialize":
            result = {"protocolVersion": "2024-11-05"}
            response.headers["Mcp-Session-Id"] = "test-mcp-session"
        elif body["method"] == "tools/list":
            result = {"tools": [{"name": "web_search"}]}
        elif body["method"] == "tools/call":
            result = self.search_result
        else:
            response.status_code = 202
            response.raw = io.BytesIO(b"")
            return response
        message = self.mutate_message({"jsonrpc": "2.0", "id": body["id"], "result": result})
        data = json.dumps(message, ensure_ascii=False)
        if self.content_type == "text/event-stream":
            data = ': heartbeat\n\ndata: {"jsonrpc":"2.0","method":"notifications/message"}\n\ndata: ' + data + "\n\n"
        response.raw = io.BytesIO(data.encode())
        return response

    def test_default_dispatch_and_answer_context(self):
        model = ScriptedModel()
        with patch.dict("os.environ", {"PARALLEL_API_KEY": "ambient-key", "WEATHER_API_KEY": "ambient-key"}), \
             patch("requests.sessions.get_netrc_auth", side_effect=AssertionError("must be anonymous")):
            prompt = get_agent_prompt(model, "顺丰到杭州需要多久？", "上海", "顺丰")
        self.assertIn(SOURCE, prompt)
        self.assertIn("配送政策", prompt)
        self.assertIn("客户的问题：“顺丰到杭州需要多久？" , prompt)
        self.assertIn("不能据此保证送达时间", prompt)
        self.assertIn("ParallelSearchAction", str(model.prompt))
        self.assertEqual(len(self.sent), 4)
        for request, kwargs in self.sent:
            self.assertEqual(request.url, MCP_URL)
            self.assertEqual(request.headers["User-Agent"], USER_AGENT)
            self.assertNotIn("Authorization", request.headers)
            self.assertNotIn("x-api-key", request.headers)
            self.assertEqual(kwargs["allow_redirects"], False)
            self.assertGreater(kwargs["timeout"][1], 0)
            self.assertLessEqual(kwargs["timeout"][1], 30)
        for request, _ in self.sent[1:]:
            self.assertEqual(request.headers["Mcp-Session-Id"], "test-mcp-session")
            self.assertEqual(request.headers["MCP-Protocol-Version"], "2024-11-05")
        payload = json.loads(self.sent[-1][0].body)
        self.assertEqual(payload["params"], {"name": "web_search", "arguments": {
            "objective": "顺丰 杭州 配送 政策", "search_queries": ["顺丰 杭州 配送 政策"]}})

    def test_sse_dispatch_and_consumption(self):
        self.content_type = "text/event-stream"
        self.assertIn(SOURCE, get_agent_prompt(ScriptedModel(), "配送政策", "上海", "顺丰"))

    def test_provider_choices(self):
        cases = [
            ("auto", None, None, "parallel"),
            ("auto", "weather", "delivery", "delivery"),
            ("auto", "weather", None, None),
            ("auto", None, "delivery", None),
            ("auto", "", None, None),
            ("parallel", "weather", "delivery", "parallel"),
            ("delivery", None, None, None),
            ("delivery", "weather", "delivery", "delivery"),
            ("none", "weather", "delivery", None),
        ]
        for provider, weather, delivery, expected in cases:
            with self.subTest(provider=provider, weather=weather, delivery=delivery):
                config = SimpleNamespace(ENABLE_AGENT=True, AGENT_SEARCH_PROVIDER=provider,
                                         AGENT_WEATHER_API_KEY=weather, AGENT_DELIVERY_TIME_API_KEY=delivery)
                self.assertEqual(get_search_provider(config), expected)
                config.ENABLE_AGENT = False
                self.assertIsNone(get_search_provider(config))
        with patch.object(WEB_CONFIGS, "AGENT_SEARCH_PROVIDER", "typo"):
            with self.assertRaises(ValueError):
                get_search_provider()

    def test_disable_and_chat_permission_never_dispatch(self):
        self.assertEqual(get_agent_prompt(object(), "query", "", "", enabled=False), "")
        with patch.object(WEB_CONFIGS, "ENABLE_AGENT", False):
            self.assertEqual(get_agent_prompt(object(), "query", "", ""), "")
        with patch.object(WEB_CONFIGS, "AGENT_SEARCH_PROVIDER", "none"):
            self.assertEqual(get_agent_prompt(object(), "query", "", ""), "")
        self.assertEqual(self.sent, [])

    def test_search_error_does_not_become_answer_or_fallback(self):
        self.search_result = {"isError": True, "content": [{"type": "text", "text": "Error: quota"}]}
        self.assertEqual(get_agent_prompt(ScriptedModel(), "query", "", ""), "")
        self.assertEqual(len(self.sent), 4)

    def test_network_error_and_timeout(self):
        for failure in (requests.Timeout("timeout"), requests.ConnectionError("offline")):
            with self.subTest(failure=type(failure).__name__):
                self.failure = failure
                action = ParallelSearchAction()
                result = action({"query": "query"})
                self.assertEqual(result.state, ActionStatusCode.API_ERROR)
                self.assertFalse(result.result)

    def test_cancellation_propagates_and_closes_session(self):
        for failure in (KeyboardInterrupt(), asyncio.CancelledError()):
            with self.subTest(failure=type(failure).__name__):
                self.failure = failure
                with patch.object(requests.Session, "close") as close:
                    with self.assertRaises(type(failure)):
                        ParallelSearchAction()({"query": "query"})
                    close.assert_called_once()

    def test_invalid_queries_do_not_send(self):
        for query in (" ", "x" * 1001):
            self.assertEqual(ParallelSearchAction()({"query": query}).state, ActionStatusCode.ARGS_ERROR)
        self.assertEqual(self.sent, [])

    def test_malformed_or_empty_tool_response(self):
        for result in ({}, {"content": []}, {"content": [{"type": "image"}]}, {"content": None}):
            with self.subTest(result=result):
                self.search_result = result
                self.assertEqual(ParallelSearchAction()({"query": "query"}).state, ActionStatusCode.API_ERROR)

    def test_bounded_response(self):
        with patch("server.base.modules.agent.parallel_search.MAX_RESPONSE_BYTES", 10):
            self.assertEqual(ParallelSearchAction()({"query": "query"}).state, ActionStatusCode.API_ERROR)
        self.assertEqual(len(self.sent), 1)

    def test_http_failures_and_redirects_do_not_dispatch_search(self):
        for status in (301, 401, 429, 500):
            with self.subTest(status=status):
                self.sent.clear()
                self.http_status = status
                self.assertEqual(ParallelSearchAction()({"query": "query"}).state, ActionStatusCode.API_ERROR)
                self.assertEqual(len(self.sent), 1)

    def test_protocol_failures_do_not_dispatch_search(self):
        cases = [
            lambda msg: {**msg, "id": 999},
            lambda msg: {**msg, "jsonrpc": "1.0"},
            lambda msg: {"jsonrpc": "2.0", "id": msg["id"], "error": {"message": "failed"}},
            lambda msg: {**msg, "result": {"protocolVersion": "unsupported"}},
        ]
        for mutate in cases:
            self.sent.clear()
            self.mutate_message = mutate
            self.assertEqual(ParallelSearchAction()({"query": "query"}).state, ActionStatusCode.API_ERROR)
            self.assertEqual(len(self.sent), 1)

    def test_model_can_decline_search(self):
        class NoToolModel(ScriptedModel):
            def chat_completions_v1(self, **kwargs):
                yield {"choices": [{"delta": {"content": "可以参考商品说明书。"}}]}
        self.assertEqual(get_agent_prompt(NoToolModel(), "商品颜色", "", ""), "")
        self.assertEqual(self.sent, [])

    def test_plugin_status_uses_the_same_provider_resolver(self):
        with patch("requests.get", return_value=SimpleNamespace(status_code=200)):
            from server.base.server_info import SERVER_PLUGINS_INFO
            SERVER_PLUGINS_INFO.update_info()
            self.assertTrue(SERVER_PLUGINS_INFO.agent_enabled)
            with patch.object(WEB_CONFIGS, "ENABLE_AGENT", False):
                SERVER_PLUGINS_INFO.update_info()
                self.assertFalse(SERVER_PLUGINS_INFO.agent_enabled)
            with patch.object(WEB_CONFIGS, "AGENT_WEATHER_API_KEY", "partial"):
                SERVER_PLUGINS_INFO.update_info()
                self.assertFalse(SERVER_PLUGINS_INFO.agent_enabled)


if __name__ == "__main__":
    unittest.main()
