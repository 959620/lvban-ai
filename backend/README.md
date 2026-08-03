# 艺术留学教务智能工作台

个人教务 AI 工作台（React + FastAPI + SQLite）。本仓库根目录另有微信小程序「旅伴 AI」，二者独立。

## 目录

```
backend/     FastAPI 后端
frontend/    React + Tailwind 前端
miniprogram/ 原有微信小程序（无关）
```

## 环境要求

- Node.js 18+
- Python 3.12+

## 启动后端

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux

uvicorn app.main:app --reload --port 8000
```

接口文档：http://127.0.0.1:8000/docs （中文）
ReDoc：http://127.0.0.1:8000/redoc

## 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问：http://127.0.0.1:5173

## AI 配置

编辑 `backend/.env`：

```env
OPENAI_API_KEY=你的_AIHubMix_密钥
OPENAI_BASE_URL=https://aihubmix.com/v1
OPENAI_MODEL=gpt-5.6-luna
```

未配置时，AI 助手仍可用本地规则兜底（课程匹配分析、话术模板）。
当前默认走 [AIHubMix](https://aihubmix.com) 的 OpenAI 兼容接口；换其他中转只需改 `OPENAI_BASE_URL` / `OPENAI_MODEL`。

## 已完成模块

认证、学生 CRM、工作台待办、跟进、课程库、课程匹配、AI 助手。

## 下一步建议

日程排课，或继续打磨匹配/话术体验。
