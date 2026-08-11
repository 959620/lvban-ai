"""
Step 7 解析器本地验证（不依赖真实 OpenAI Key）。

运行：
  cd Edu-Agent
  .venv/bin/python scripts/test_parser_step7.py
"""

from __future__ import annotations

import json
from unittest.mock import patch

from app.ai.openai_client import OpenAIClient, OpenAIClientError
from app.ai.parser import OpenAITaskParser, RuleBasedTaskParser, get_task_parser, parser_status
from config.settings import Settings


def test_rule_parser() -> None:
    result = RuleBasedTaskParser().parse(
        "8月20日下午3点提醒我联系学生王同学确认作品集修改情况"
    )
    assert result["student"] == "王同学"
    assert result["deadline"] == "2026-08-20T15:00:00"
    assert result["parse_source"] == "rule"
    print("rule_ok", result)


def test_openai_success_mocked() -> None:
    fake = {
        "task": "催李同学提交作品集第二版",
        "deadline": "2026-08-20T15:00:00",
        "student": "李同学",
        "priority": "urgent",
    }

    class FakeClient(OpenAIClient):
        def __init__(self) -> None:
            super().__init__(Settings(openai_api_key="sk-test"))

        def chat_json(self, **kwargs):  # noqa: ANN003
            return json.dumps(fake)

    result = OpenAITaskParser(client=FakeClient()).parse(
        "下周三下午提醒我催李同学交作品集第二版，比较紧急"
    )
    assert result["parse_source"] == "openai"
    assert result["student"] == "李同学"
    assert result["priority"] == "urgent"
    print("openai_ok", result)


def test_openai_fallback_mocked() -> None:
    class BrokenClient(OpenAIClient):
        def __init__(self) -> None:
            super().__init__(Settings(openai_api_key="sk-test"))

        def chat_json(self, **kwargs):  # noqa: ANN003
            raise OpenAIClientError("boom")

    result = OpenAITaskParser(client=BrokenClient()).parse(
        "下周提醒我催李同学提交作品集第二版"
    )
    assert result["parse_source"] == "openai_fallback"
    assert result["student"] == "李同学"
    print("fallback_ok", result)


def test_factory_without_key() -> None:
    with patch("app.ai.parser.get_settings", return_value=Settings(openai_api_key="")):
        parser = get_task_parser()
        assert isinstance(parser, RuleBasedTaskParser)
        status = parser_status()
        assert status["engine"] == "rule"
        print("factory_ok", status)


if __name__ == "__main__":
    test_rule_parser()
    test_openai_success_mocked()
    test_openai_fallback_mocked()
    test_factory_without_key()
    print("ALL_PASSED")
