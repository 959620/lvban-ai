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
    status = call("GET", "/api/match/status", token=token)
    print("ready", status["ready"], status["engine"])
    courses = call("GET", "/api/courses", token=token)
    if not courses["items"]:
        raise SystemExit("no courses")
    course_id = courses["items"][0]["id"]
    run = call("POST", "/api/match/run", {"course_id": course_id, "min_score": 20}, token=token)
    print("run", run["id"], "total", run["total"])
    if run["results"]:
        top = run["results"][0]
        print("top", top["student"]["name"], top["score"], top["reasons"][:2])
        scripts = call(
            "POST",
            "/api/match/scripts",
            {"course_id": course_id, "student_id": top["student_id"], "match_result_id": top["id"]},
            token=token,
        )
        print("scripts_ok", len(scripts["wechat_student"]) > 10, len(scripts["parent"]) > 10)
        task = call(
            "POST",
            "/api/match/create-task",
            {"course_id": course_id, "student_id": top["student_id"]},
            token=token,
        )
        print("task", task["id"], task["title"][:20])
    else:
        print("no_results")


if __name__ == "__main__":
    main()
