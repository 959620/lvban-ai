# Zeabur 部署说明（教务智能工作台）

仓库已配置根目录 `Dockerfile`：构建前端并打包进 FastAPI，**同一域名**提供页面与 `/api`。

## 一键部署（推荐）

1. 打开 [Zeabur Dashboard](https://dash.zeabur.com/)
2. **New Project** → 选区域
3. **Add Service** → **GitHub** → 选择仓库 `959620/lvban-ai`
4. 确认使用 Dockerfile 构建后部署
5. 服务启动后：**Networking / Domain** 生成公网域名

或使用 CLI（需先登录）：

```bash
npx zeabur@latest auth login
npx zeabur@latest deploy
```

## 环境变量（服务 Variables）

| 变量 | 说明 | 示例 |
|------|------|------|
| `SECRET_KEY` | JWT 密钥（必改） | 随机长字符串 |
| `DATABASE_URL` | 数据库 | `sqlite:////data/jiaowu.db` |
| `OPENAI_API_KEY` | AIHubMix / OpenAI Key | `sk-...` |
| `OPENAI_BASE_URL` | 兼容接口 | `https://aihubmix.com/v1` |
| `OPENAI_MODEL` | 模型名 | `gpt-5.6-luna` |
| `CORS_ORIGINS` | 跨域；同域部署可保持默认 | `*` |

## 持久化（重要）

SQLite 默认会丢数据（容器重建）。请在 Zeabur 服务里添加 **Volume**：

- 挂载路径：`/data`
- 并设置 `DATABASE_URL=sqlite:////data/jiaowu.db`

## 验证

- 首页：你的 Zeabur 域名
- 健康检查：`/api/health`
- 接口文档：`/docs`

微信小程序（`miniprogram/`）不在本次 Web 部署范围内。
