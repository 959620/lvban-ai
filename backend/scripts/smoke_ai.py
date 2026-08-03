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
    status = call("GET", "/api/ai/status", token=token)
    print("configured", status["configured"], status["message"][:40])
    students = call("GET", "/api/students", token=token)
    courses = call("GET", "/api/courses", token=token)
    student_id = students["items"][0]["id"] if students["items"] else None
    course_id = courses["items"][0]["id"] if courses["items"] else None
    result = call(
        "POST",
        "/api/ai/chat",
        {
            "message": "分析这个学生适合什么课程",
            "student_id": student_id,
            "course_id": course_id,
        },
        token=token,
    )
    print("engine", result["engine"], "model", result["model"])
    print("reply_head", result["reply"][:120].replace("\n", " / "))


if __name__ == "__main__":
    main()
