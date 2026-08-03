# 旅伴 AI（微信小程序）

智能旅行规划小程序。用户输入目的地、日期、人数、预算与偏好后，生成可执行的个性化行程（当前为前端模拟数据）。

> 同仓库另有 **教务智能工作台**（React + FastAPI），说明见 [JIAOWU.md](JIAOWU.md)。

## 功能

- 首页 / 创建旅行 / 我的行程（TabBar）
- AI 对话规划 + 调整规划（可改基础信息、同行与节奏、旅行偏好并保存重生成）
- 行程详情（每日时间轴、美食、备用方案）
- 预算拆分、准备清单
- 新建行程状态为「已完成」，数据保存在本地 `wx.storage`

## 技术栈

- 微信原生小程序（WXML / WXSS / TypeScript）
- 本地模拟行程生成（无后端 / 无真实大模型）

## 如何运行

1. 安装 [微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)
2. 打开开发者工具 → **导入项目**
3. 目录选择本仓库根目录：`lvban-ai`（含 `project.config.json`）
4. AppID 可选用 **测试号**（工程默认 `touristappid`）
5. 详情 → 本地设置：勾选 **不校验合法域名**（示例封面图来自 Unsplash）
6. 编译预览

可选：在仓库根目录执行 `npm install`，仅用于安装 TypeScript 类型声明，不影响小程序运行。

## 页面路径

| 路径 | 说明 |
|------|------|
| `pages/index/index` | 首页 |
| `pages/create/create` | 创建旅行 |
| `pages/trips/trips` | 我的行程 |
| `pages/detail/detail?id=` | 行程详情 |
| `pages/plan/plan?id=` | AI 对话 / 调整规划 |
| `pages/budget/budget?id=` | 预算 |
| `pages/checklist/checklist?id=` | 准备清单 |

示例行程 ID：`trip-dali-demo`

## 后续可接入

- 真实大模型 API
- 微信登录与云开发存储
- 地图 / 天气 / 酒店 / 景点数据
