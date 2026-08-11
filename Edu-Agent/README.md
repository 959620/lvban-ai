# Edu-Agent — AI 个人教务助手

面向艺术留学教务老师的个人 Agent：用自然语言创建跟进任务、定时提醒、学生档案管理，并预留企业微信通知。

> 当前进度：**Step 6 定时提醒已完成**（APScheduler 扫描 → 本地通知 → 通知日志）。

---

## 架构一览

```text
自然语言输入 → API → AI/规则解析 → TaskService → SQLite
                                         ↓
                                 ReminderService（生成 24h/2h/到期提醒）
                                         ↓
                            NotificationChannel（local / email / wecom 预留）
```

---

## 目录结构

```text
Edu-Agent/
├── main.py
├── requirements.txt
├── README.md
├── config/                 # settings + .env.example
├── data/                   # SQLite
├── frontend/               # 简易网页（创建任务 UX）
└── app/
    ├── api/                # health + tasks
    ├── models/             # ORM + schemas
    ├── database/
    ├── services/           # task / student / reminder
    ├── scheduler/          # Step 6
    ├── ai/                 # 规则解析（Step 7 接 OpenAI）
    └── notification/       # local + email/wecom 预留
```

---

## 快速运行

```bash
cd Edu-Agent
python -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp config/.env.example .env
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

打开：

- 首页：http://127.0.0.1:8000/
- API 文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/api/health

---

## Step 4：如何测试任务创建

### 1）网页

1. 打开首页，输入自然语言（已预填示例）
2. 点「先解析预览」→ 检查任务名/学生/时间/优先级
3. 可编辑后点「确认创建」
4. 或点「一键创建」直接入库

### 2）API

```bash
# 仅解析
curl -s -X POST http://127.0.0.1:8000/api/tasks/parse \
  -H 'Content-Type: application/json' \
  -d '{"text":"下周提醒我催李同学提交作品集第二版"}'

# 一键创建
curl -s -X POST http://127.0.0.1:8000/api/tasks/parse-create \
  -H 'Content-Type: application/json' \
  -d '{"text":"8月20日下午3点提醒我联系学生王同学确认作品集修改情况"}'
```

期望：返回 `parsed` + `task`，且 `task.reminders` 含提前 24h / 2h / 到期（若时间未过期）。

---

## Step 5：如何测试任务存储

### 1）网页

1. 创建任务后，下方「任务列表」自动刷新
2. 用状态 / 学生 / 关键词 / 仅逾期筛选
3. 点「完成」或「取消」，未发送提醒应变为 `skipped` / `cancelled`

### 2）API

```bash
# 列表 + 筛选
curl -s 'http://127.0.0.1:8000/api/tasks?student_name=李&status=pending'

# 更新截止时间（会重建提醒）
curl -s -X PATCH http://127.0.0.1:8000/api/tasks/1 \
  -H 'Content-Type: application/json' \
  -d '{"due_at":"2026-08-25T15:00:00","priority":"high"}'

# 完成任务（未发送提醒 → skipped）
curl -s -X PATCH http://127.0.0.1:8000/api/tasks/1/status \
  -H 'Content-Type: application/json' \
  -d '{"status":"done"}'
```

---

## Step 6：如何测试定时提醒

### 1）创建一条「马上到期」的提醒任务

可用结构化接口把 `due_at` 设为 1 分钟后，或直接改库中某条 `reminders.remind_at` 为过去时间。

更简单：创建任务后，用 SQL/调试把提醒时间改到现在，再调用手动扫描。

### 2）手动扫描（推荐测试）

```bash
curl -s -X POST http://127.0.0.1:8000/api/notifications/run-once
curl -s http://127.0.0.1:8000/api/notifications
curl -s http://127.0.0.1:8000/api/notifications/scheduler-status
```

期望：`run-once` 返回 `sent >= 1`；通知日志出现 success；服务端控制台打印 `[LOCAL NOTIFY] ...`。

### 3）网页

首页「提醒与通知」区域 → 点「立即扫描提醒」→ 查看通知日志列表。

调度器默认每 60 秒自动扫描（`.env` 中 `SCHEDULER_INTERVAL_SECONDS` 可调）。

---

## 开发路线

| Step | 内容 | 状态 |
|------|------|------|
| 1 | 产品架构设计 | ✅ |
| 2 | 数据库设计 | ✅ |
| 3 | 项目目录 | ✅ |
| 4 | 任务创建功能 | ✅ |
| 5 | 任务存储增强（列表/更新/状态流转） | ✅ |
| 6 | 定时提醒 | ✅ |
| 7 | AI 自然语言解析（OpenAI） | 待做 |
| 8 | 通知模块完善（本地+邮件） | 待做 |
| 9 | 企业微信接口预留/接通 | 待做 |

---

## 安全提示

- 不要将 `.env`、数据库文件、SMTP/企业微信密钥提交到仓库
- MVP 默认单用户本地运行；多老师场景需后续增加鉴权
