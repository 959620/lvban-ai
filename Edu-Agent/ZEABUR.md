# Edu-Agent 零终端部署（浏览器直接打开）

不想用 PowerShell？任选一种方式：

---

## 方式一：Windows 双击启动（本机）

1. 确保已 `git pull` 到最新 `master`
2. 进入文件夹 `Edu-Agent`
3. **双击 `启动.bat`**
4. 会自动打开浏览器 → http://127.0.0.1:8000/

> 首次双击会安装依赖，稍等 1～2 分钟。

---

## 方式二：Zeabur 云部署（推荐，永久网址）

### A. 网页部署（约 3 分钟）

1. 打开 https://dash.zeabur.com/ 并登录（建议用 GitHub）
2. **New Project** → 选择区域（如 Taipei）
3. **Add Service** → **GitHub** → 仓库 `959620/lvban-ai`，分支 `master`
4. **重要**：进入该服务 **Settings** → **Root Directory** 填 `Edu-Agent`  
   （不填会误用仓库根目录的旧「教务工作台」Dockerfile）
5. 确认使用 `Edu-Agent/Dockerfile` 构建
6. **Variables** 添加：

   | 变量 | 值 |
   |------|-----|
   | `DATABASE_URL` | `sqlite:////app/data/edu_agent.db` |
   | `APP_ENV` | `production` |
   | `DEBUG` | `false` |

7. **Volumes** 添加挂载：`/app/data`（持久化 SQLite）
8. 点击 **Deploy**，完成后 **Networking** → 生成域名
9. 浏览器打开 `https://你的域名.zeabur.app`

可选变量：`OPENAI_API_KEY`、`NOTIFY_EMAIL`、`NOTIFY_WECOM` 等。

### B. CLI 一键部署（给 Cursor Agent / CI）

1. 在 https://dash.zeabur.com/account/api-tokens 创建 **API Token**
2. 在 Cursor 环境变量或本机终端设置：

```bash
export ZEABUR_TOKEN=你的token
export PUBLIC_DOMAIN=edu-agent   # 域名前缀，可改
cd Edu-Agent
bash scripts/deploy-zeabur.sh
```

3. 若模板首次从整仓拉取，请在 Dashboard 将该服务 **Root Directory** 设为 `Edu-Agent` 后 **Redeploy**

### 验证

- 首页：`https://你的域名.zeabur.app/`
- 健康检查：`/api/health`
- 接口文档：`/docs`

---

## 方式三：Cursor 云端 Desktop（开发调试）

在 Cursor Agent 窗口顶部点 **Desktop** → Chrome 访问 http://127.0.0.1:8000/

（不要用本机 Simple Browser，那是你电脑上的地址。）
