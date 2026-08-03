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
    day = call("GET", "/api/schedule/day", token=token)
    date = day["query_date"]
    s1 = call(
        "POST",
        "/api/schedule",
        {
            "student_id": student_id,
            "course_id": None,
            "session_date": date,
            "start_time": "10:00",
            "end_time": "12:00",
            "classroom": "A101",
            "teacher_name": "王老师",
            "session_type": "作品集辅导",
            "status": "scheduled",
            "notes": "草图点评",
        },
        token=token,
    )
    print("created", s1["id"], "conflict", s1["classroom_conflict"])
    s2 = call(
        "POST",
        "/api/schedule",
        {
            "student_id": student_id,
            "course_id": None,
            "session_date": date,
            "start_time": "11:00",
            "end_time": "13:00",
            "classroom": "A101",
            "teacher_name": "李老师",
            "session_type": "一对一",
            "status": "scheduled",
            "notes": None,
        },
        token=token,
    )
    print("overlap_conflict", s2["classroom_conflict"])
    day2 = call("GET", "/api/schedule/day", token=token)
    print("day_total", day2["total"], "rooms", day2["occupied_classrooms"], "absent", day2["absent_count"])
    marked = call("POST", f"/api/schedule/{s1['id']}/absent", token=token)
    print("absent_status", marked["status"])


if __name__ == "__main__":
    main()
