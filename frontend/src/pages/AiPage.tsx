import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { apiFetch } from "../lib/api";
import { fetchCourses, type Course } from "../lib/courses";
import { fetchStudents, type Student } from "../lib/students";

type AiStatus = {
  configured: boolean;
  model: string;
  base_url: string;
  message: string;
};

type AiChatResponse = {
  engine: string;
  reply: string;
  model: string;
  context: {
    has_student?: boolean;
    has_course?: boolean;
    course_count?: number;
  };
};

const QUICK_PROMPTS = [
  "分析这个学生适合什么课程",
  "帮我写家长沟通话术",
  "总结这个学生的申请进度和下一步",
  "针对这门课，给我一段不强推的学生微信话术",
];

export function AiPage() {
  const [status, setStatus] = useState<AiStatus | null>(null);
  const [students, setStudents] = useState<Student[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [studentId, setStudentId] = useState("");
  const [courseId, setCourseId] = useState("");
  const [message, setMessage] = useState(QUICK_PROMPTS[0]);
  const [reply, setReply] = useState("");
  const [meta, setMeta] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiFetch<AiStatus>("/api/ai/status")
      .then(setStatus)
      .catch((err) => setError(err instanceof Error ? err.message : "加载失败"));
    fetchStudents()
      .then((data) => setStudents(data.items))
      .catch(() => undefined);
    fetchCourses()
      .then((data) => setCourses(data.items))
      .catch(() => undefined);
  }, []);

  async function send(prompt: string) {
    setError("");
    setLoading(true);
    setMeta("");
    try {
      const result = await apiFetch<AiChatResponse>("/api/ai/chat", {
        method: "POST",
        body: JSON.stringify({
          message: prompt,
          student_id: studentId ? Number(studentId) : null,
          course_id: courseId ? Number(courseId) : null,
        }),
      });
      setReply(result.reply);
      setMeta(`引擎：${result.engine} · 模型：${result.model}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "请求失败");
    } finally {
      setLoading(false);
    }
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    await send(message.trim());
  }

  return (
    <section className="max-w-3xl">
      <p className="text-sm text-[var(--muted)]">AI Assistant</p>
      <h2 className="mt-2 text-3xl font-semibold tracking-tight">AI 助手</h2>
      <p className="mt-3 text-[var(--muted)]">
        可绑定学生/课程上下文。已配置 API Key 时调用大模型（AIHubMix / OpenAI 兼容）；未配置时使用本地匹配与话术模板兜底。
      </p>

      <div className="mt-6 rounded-3xl border border-[var(--line)] bg-white/70 p-5 text-sm">
        <p>
          状态：
          <span className="ml-2 text-[var(--accent)]">
            {status ? status.message : "加载中…"}
          </span>
        </p>
        {status ? (
          <p className="mt-2 text-[var(--muted)]">
            模型 {status.model} · {status.base_url}
            {status.configured ? "" : " · 在 backend/.env 填写 OPENAI_API_KEY 启用真实模型"}
          </p>
        ) : null}
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <label className="text-sm">
          <span className="mb-1.5 block text-[var(--muted)]">学生上下文</span>
          <select
            className="w-full rounded-xl border border-[var(--line)] bg-white px-3 py-2.5"
            value={studentId}
            onChange={(e) => setStudentId(e.target.value)}
          >
            <option value="">不指定学生</option>
            {students.map((student) => (
              <option key={student.id} value={student.id}>
                {student.name}
                {student.major ? `（${student.major}）` : ""}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          <span className="mb-1.5 block text-[var(--muted)]">课程上下文</span>
          <select
            className="w-full rounded-xl border border-[var(--line)] bg-white px-3 py-2.5"
            value={courseId}
            onChange={(e) => setCourseId(e.target.value)}
          >
            <option value="">不指定课程</option>
            {courses.map((course) => (
              <option key={course.id} value={course.id}>
                {course.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      {students.length === 0 || courses.length === 0 ? (
        <p className="mt-3 text-sm text-[var(--muted)]">
          {students.length === 0 ? (
            <>
              还没有学生，
              <Link className="text-[var(--accent)] hover:underline" to="/students/new">
                去新建
              </Link>
              。{" "}
            </>
          ) : null}
          {courses.length === 0 ? (
            <>
              还没有课程，
              <Link className="text-[var(--accent)] hover:underline" to="/courses/new">
                去新建
              </Link>
              。
            </>
          ) : null}
        </p>
      ) : null}

      <div className="mt-4 flex flex-wrap gap-2">
        {QUICK_PROMPTS.map((prompt) => (
          <button
            key={prompt}
            type="button"
            className="rounded-full border border-[var(--line)] bg-white px-3 py-1.5 text-xs text-[var(--muted)] hover:border-[var(--accent)] hover:text-[var(--accent)]"
            onClick={() => {
              setMessage(prompt);
              void send(prompt);
            }}
          >
            {prompt}
          </button>
        ))}
      </div>

      <form className="mt-6 space-y-4" onSubmit={onSubmit}>
        <textarea
          className="min-h-28 w-full rounded-2xl border border-[var(--line)] bg-white px-4 py-3 outline-none focus:border-[var(--accent)]"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        {error ? <p className="text-sm text-[var(--danger)]">{error}</p> : null}
        <button
          type="submit"
          disabled={loading || !message.trim()}
          className="rounded-xl bg-[var(--accent)] px-4 py-2.5 text-white disabled:opacity-60"
        >
          {loading ? "思考中…" : "发送"}
        </button>
      </form>

      {meta ? <p className="mt-4 text-xs text-[var(--muted)]">{meta}</p> : null}

      {reply ? (
        <div className="mt-4 whitespace-pre-wrap rounded-3xl border border-[var(--line)] bg-white/80 p-5 text-sm leading-7">
          {reply}
        </div>
      ) : null}
    </section>
  );
}
