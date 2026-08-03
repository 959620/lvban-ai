# 教务智能工作台

与根目录微信小程序相互独立。完整说明见：

- [backend/README.md](backend/README.md)
- [frontend/README.md](frontend/README.md)

快速启动：

```bash
# 终端 1 — 后端（当前开发常用 8004；若 8003 被旧进程占用可继续用 8004）
cd backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 8004

# 终端 2 — 前端
cd frontend
npm run dev
```

浏览器打开前端地址（Vite 默认 http://127.0.0.1:5173 ）。
请确认 `frontend/vite.config.ts` 里 `/api` 代理指向后端端口。

接口文档：http://127.0.0.1:8004/docs

生产部署（Zeabur）见 [ZEABUR.md](ZEABUR.md)。
