# Edu-Agent 零终端部署（浏览器直接打开）

不想用 PowerShell？任选一种方式：

---

## 方式一：Windows 双击启动（最简单）

1. 确保已 `git pull` 到最新 `master`
2. 进入文件夹 `Edu-Agent`
3. **双击 `启动.bat`**
4. 会自动打开浏览器 → http://127.0.0.1:8000/

> 首次双击会安装依赖，稍等 1～2 分钟。

---

## 方式二：Zeabur 云部署（永久网址，任何设备打开）

全程在网页点选，不用本地终端：

1. 打开 https://dash.zeabur.com/
2. **New Project** → 选区域
3. **Add Service** → **GitHub** → 仓库 `959620/lvban-ai`
4. **Root Directory** 填：`Edu-Agent`
5. 使用 `Edu-Agent/Dockerfile` 构建并 Deploy
6. **Networking** → 生成域名，例如 `https://edu-agent-xxx.zeabur.app`
7. 以后直接浏览器打开该链接即可

可选环境变量（Variables）：

| 变量 | 说明 |
|------|------|
| `DATABASE_URL` | `sqlite:////data/edu_agent.db` |
| `OPENAI_API_KEY` | 可选，AI 解析 |
| `NOTIFY_EMAIL` / `NOTIFY_WECOM` | 通知开关 |

建议添加 Volume 挂载 `/app/data` 持久化数据库。

---

## 方式三：Cursor 云端 Desktop（开发调试）

在 Cursor Agent 窗口顶部点 **Desktop** → Chrome 访问 http://127.0.0.1:8000/

（不要用本机 Simple Browser，那是你电脑上的地址。）
