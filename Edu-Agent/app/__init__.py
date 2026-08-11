"""
Edu-Agent 应用包。

分层约定：
- api/           HTTP 路由
- models/        ORM + Pydantic Schema
- database/      引擎与会话
- services/      业务编排
- scheduler/     定时提醒
- ai/            自然语言解析
- notification/  通知通道（含企业微信预留）
"""
