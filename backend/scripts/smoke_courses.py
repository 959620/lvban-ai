import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8002"


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
    opts = call("GET", "/api/courses/options", token=token)
    print("types", len(opts["course_types"]), "majors", len(opts["majors"]))
    course = call(
        "POST",
        "/api/courses",
        {
            "name": "RISD作品集提升训练营",
            "course_type": "训练营",
            "suitable_majors": ["工业设计", "建筑设计"],
            "suitable_stages": ["作品集制作", "申请前6个月"],
            "goal": "提升作品集完整度",
            "price": 12800,
            "teacher_name": "王老师",
            "description": "针对冲刺 RISD 的强化训练",
        },
        token=token,
    )
    print("created", course["id"], course["name"])
    listed = call("GET", "/api/courses?major=%E5%B7%A5%E4%B8%9A%E8%AE%BE%E8%AE%A1", token=token)
    print("list_total", listed["total"])
    updated = call(
        "PUT",
        f"/api/courses/{course['id']}",
        {**{k: course[k] for k in [
            "name", "course_type", "suitable_majors", "suitable_stages",
            "goal", "price", "teacher_name", "description",
        ]}, "price": 13800},
        token=token,
    )
    print("updated_price", updated["price"])


if __name__ == "__main__":
    main()
