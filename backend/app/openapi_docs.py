"""OpenAPI / Swagger 中文文档配置。"""

OPENAPI_TAGS = [
    {"name": "系统", "description": "健康检查等系统接口"},
    {"name": "认证", "description": "注册、登录、当前用户"},
    {"name": "学生", "description": "学生 CRM：建档、筛选、目标院校与标签"},
    {"name": "待办", "description": "工作台待办、勾选完成与今日提醒汇总"},
    {"name": "课程库", "description": "机构课程维护：类型、适合专业/阶段、目标与价格"},
    {"name": "日程", "description": "排课预约、日/周课表、教室占用与缺课标记"},
    {"name": "跟进", "description": "沟通跟进记录，联动下次提醒与待办"},
    {"name": "课程匹配", "description": "规则匹配推荐学生，并生成销售话术"},
    {"name": "AI 助手", "description": "OpenAI 对话助手；未配置密钥时使用本地匹配/话术兜底"},
    {"name": "时间轴", "description": "学生时间轴：排课聚合、作品集/申请节点"},
]

APP_DESCRIPTION = """
## 艺术留学机构 · 教务老师智能工作台 API

面向教务老师的个人工作台后端。当前已开通：认证、学生 CRM、工作台待办、跟进记录、课程库、课程匹配、AI 助手、日程排课、学生时间轴。

### 使用说明

1. 先调用 **注册** 或 **登录** 获取 `access_token`
2. 点击右上角 **Authorize**，填写：`Bearer <你的令牌>`（或只填令牌，视 Swagger 版本而定）
3. 再调试需要登录的接口

### 约定

- 业务数据按登录老师（`owner_id`）隔离
- 未配置 `OPENAI_API_KEY` 时，AI 接口返回占位回复
"""
