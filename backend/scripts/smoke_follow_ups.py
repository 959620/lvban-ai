import json
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8002"
CN_TZ = timezone(timedelta(hours=8))


def call(method, path, data=None, token=None, form=False):
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


def main():
    auth = call("POST", "/api/auth/login", {"username": "teacher1", "password": "test1234"}, form=True)
    token = auth["access_token"]
    students = call("GET", "/api/students", token=token)
    student_id = students["items"][0]["id"]
    now = datetime.now(CN_TZ)
    remind = (now + timedelta(hours=2)).replace(second=0, microsecond=0).isoformat()
    item = call(
        "POST",
        "/api/follow-ups",
        {
            "student_id": student_id,
            "contact_date": now.isoformat(),
            "contact_with": "parent",
            "content": "沟通作品集进度，家长希望加强督促",
            "result": "同意本周加一节课",
            "next_action": "发送课程方案",
            "next_remind_at": remind,
            "create_task": True,
        },
        token=token,
    )
    print("follow_up", item["id"], "task", item["created_task_id"])
    student = call("GET", f"/api/students/{student_id}", token=token)
    print("student_next_contact", student["next_contact_at"] is not None)
    dash = call("GET", "/api/tasks/dashboard", token=token)
    print("todo_total", dash["stats"]["todo_total"], "contact", dash["stats"]["contact_count"])
    listed = call("GET", f"/api/follow-ups?student_id={student_id}", token=token)
    print("list_total", listed["total"])


if __name__ == "__main__":
    main()
