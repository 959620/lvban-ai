"""
Prompt 模板集中管理。

把提示词从业务代码中拆出，便于迭代解析质量而不改调用链。
"""

from datetime import datetime
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("Asia/Shanghai")

TASK_PARSE_SYSTEM_PROMPT = """
你是艺术留学机构的教务助手，负责把老师的中文自然语言转换成结构化任务 JSON。

只输出一个 JSON 对象，不要 Markdown，不要解释。字段：
- task: string，简洁任务名称（去掉“提醒我/请帮我”等套话）
- deadline: string|null，截止/执行时间，ISO8601 本地时间（例如 2026-08-20T15:00:00）；不确定则为 null
- student: string|null，学生称呼（如“王同学”）；没有则为 null
- priority: "low"|"medium"|"high"|"urgent"，默认 medium

规则：
1. 相对时间（明天/下周/后天）请结合“当前时间”换算成具体日期。
2. “下午3点”=15:00，“中午”=12:00，未给时刻默认 09:00。
3. 不要编造学生姓名。
4. task 应保留业务动作，例如“催李同学提交作品集第二版”。
""".strip()


def build_task_parse_user_prompt(text: str, *, now: datetime | None = None) -> str:
    """构造带当前时间上下文的用户提示。"""
    now = now or datetime.now(LOCAL_TZ)
    now_str = now.strftime("%Y-%m-%d %H:%M:%S %Z")
    return (
        f"当前时间：{now_str}（Asia/Shanghai）\n"
        f"用户输入：{text.strip()}\n"
        "请输出 JSON。"
    )
