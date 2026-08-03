import json
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8002"
CN_TZ = timezone(timedelta(hours=8))


def call(method: str, path: str, data=None, token=None, form=False):
    headers = {}
    body = None
    if form:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        body = urlencode(data or {}).encode()
    elif data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(f"{BASE}{path}", data=body, headers=headers, method=method)
    with urlopen(req) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else None


def main() -> None:
    try:
        auth = call("POST", "/api/auth/login", {"username": "teacher1", "password": "test1234"}, form=True)
    except Exception:
        auth = call(
            "POST",
            "/api/auth/register",
            {"username": "teacher_s4", "password": "test1234", "display_name": "待办测试"},
        )
    token = auth["access_token"]

    students = call("GET", "/api/students", token=token)
    student_id = students["items"][0]["id"] if students["items"] else None

    now = datetime.now(CN_TZ)
    today_due = now.replace(hour=18, minute=0, second=0, microsecond=0).isoformat()
    soon_due = (now + timedelta(days=2)).replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
    overdue = (now - timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0).isoformat()

    t1 = call(
        "POST",
        "/api/tasks",
        {
            "title": "催交作品集草图",
            "student_id": student_id,
            "due_at": today_due,
            "priority": "urgent",
            "status": "todo",
            "source": "manual",
        },
        token=token,
    )
    call(
        "POST",
        "/api/tasks",
        {
            "title": "准备家长沟通",
            "student_id": student_id,
            "due_at": soon_due,
            "priority": "normal",
            "status": "todo",
            "source": "manual",
        },
        token=token,
    )
    call(
        "POST",
        "/api/tasks",
        {
            "title": "补发上周课表",
            "student_id": None,
            "due_at": overdue,
            "priority": "low",
            "status": "todo",
            "source": "manual",
        },
        token=token,
    )

    dash = call("GET", "/api/tasks/dashboard", token=token)
    print("stats", dash["stats"])
    print("today", [t["title"] for t in dash["today_tasks"]])
    print("upcoming", [t["title"] for t in dash["upcoming_tasks"]])
    print("incomplete", [t["title"] for t in dash["incomplete_tasks"]])

    toggled = call("POST", f"/api/tasks/{t1['id']}/toggle", token=token)
    print("toggled", toggled["status"])
    call("DELETE", f"/api/tasks/{t1['id']}", token=token)
    print("deleted_ok")


if __name__ == "__main__":
    main()
