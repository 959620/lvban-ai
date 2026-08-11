"""
AI 自然语言解析层。

设计原因：
- 与业务服务解耦：解析失败可用规则兜底，不阻塞建任务
- OpenAI 仅作为实现之一，便于换模型或离线模式
"""

from app.ai.parser import get_task_parser

__all__ = ["get_task_parser"]
