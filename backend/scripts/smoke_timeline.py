import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8003"


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
    created = call(
        "POST",
        f"/api/students/{student_id}/timeline",
        {
            "event_type": "portfolio_milestone",
            "title": "完成项目一初稿",
            "event_date": "2026-08-15",
            "status": "upcoming",
            "notes": "需要老师反馈构图",
            "related_course_id": None,
        },
        token=token,
    )
    print("created", created["id"], created["event_type_label"])
    timeline = call("GET", f"/api/students/{student_id}/timeline", token=token)
    print("total", timeline["total"], "summary", timeline["summary"])
    types = {item["event_type"] for item in timeline["items"]}
    print("types", sorted(types))
    if created["id"].startswith("manual:"):
        eid = int(created["id"].split(":")[1])
        updated = call(
            "PATCH",
            f"/api/timeline/events/{eid}",
            {"status": "done"},
            token=token,
        )
        print("updated_status", updated["status"])


if __name__ == "__main__":
    main()
