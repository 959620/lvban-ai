import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8002"


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
            {"username": "teacher_s3", "password": "test1234", "display_name": "测试教务"},
        )
    token = auth["access_token"]
    opts = call("GET", "/api/students/options", token=token)
    print("tags", len(opts["tags"]), "majors", len(opts["majors"]))
    tag_ids = [t["id"] for t in opts["tags"] if t["name"] in ("需要强督促", "有艺术基础")]
    student = call(
        "POST",
        "/api/students",
        {
            "name": "李同学",
            "grade": "高二",
            "phone": "13800000000",
            "parent_phone": "13900000000",
            "major": "工业设计",
            "target_country": "美国",
            "target_major": "Industrial Design",
            "intake_year": 2027,
            "application_stage": "作品集制作",
            "portfolio_started": True,
            "portfolio_project_count": 3,
            "portfolio_progress": 60,
            "personality_notes": "细心",
            "family_notes": None,
            "communication_notes": "微信为主",
            "important_events": None,
            "next_contact_at": None,
            "schools": [
                {"school_name": "RISD", "priority": "主申"},
                {"school_name": "Pratt", "priority": "冲刺"},
            ],
            "tag_ids": tag_ids,
        },
        token=token,
    )
    print(
        "created",
        student["id"],
        student["name"],
        [s["school_name"] for s in student["schools"]],
        [t["name"] for t in student["tags"]],
    )
    listed = call("GET", "/api/students?q=%E6%9D%8E&major=%E5%B7%A5%E4%B8%9A%E8%AE%BE%E8%AE%A1", token=token)
    print("list_total", listed["total"])
    got = call("GET", f"/api/students/{student['id']}", token=token)
    print("detail_stage", got["application_stage"])
    updated = call(
        "PUT",
        f"/api/students/{student['id']}",
        {
            **{k: got[k] for k in [
                "name", "grade", "phone", "parent_phone", "major", "target_country",
                "target_major", "intake_year", "application_stage", "portfolio_started",
                "portfolio_project_count", "portfolio_progress", "personality_notes",
                "family_notes", "communication_notes", "important_events", "next_contact_at",
            ]},
            "portfolio_progress": 75,
            "schools": [{"school_name": s["school_name"], "priority": s["priority"]} for s in got["schools"]],
            "tag_ids": [t["id"] for t in got["tags"]],
        },
        token=token,
    )
    print("updated_progress", updated["portfolio_progress"])


if __name__ == "__main__":
    main()
