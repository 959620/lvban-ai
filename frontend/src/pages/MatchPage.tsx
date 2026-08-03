import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { fetchCourses, type Course } from "../lib/courses";
import {
  createMatchTask,
  fetchMatchStatus,
  generateScripts,
  runMatch,
  type MatchResult,
  type MatchRun,
  type ScriptBundle,
} from "../lib/match";

export function MatchPage() {
  const [searchParams] = useSearchParams();
  const presetCourseId = searchParams.get("courseId") || "";

  const [courses, setCourses] = useState<Course[]>([]);
  const [courseId, setCourseId] = useState(presetCourseId);
  const [minScore, setMinScore] = useState(25);
  const [statusText, setStatusText] = useState("加载引擎状态…");
  const [run, setRun] = useState<MatchRun | null>(null);
  const [selected, setSelected] = useState<MatchResult | null>(null);
  const [scripts, setScripts] = useState<ScriptBundle | null>(null);
  const [loading, setLoading] = useState(false);
  const [scriptLoading, setScriptLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetchMatchStatus()
      .then((data) => setStatusText(data.message))
      .catch(() => setStatusText("无法获取匹配引擎状态"));
    fetchCourses()
      .then((data) => setCourses(data.items))
      .catch((err) => setError(err instanceof Error ? err.message : "课程加载失败"));
  }, []);

  useEffect(() => {
    if (presetCourseId) setCourseId(presetCourseId);
  }, [presetCourseId]);

  async function onRun() {
    if (!courseId) {
      setError("请先选择课程");
      return;
    }
    setLoading(true);
    setError("");
    setMessage("");
    setScripts(null);
    setSelected(null);
    try {
      const result = await runMatch(Number(courseId), minScore);
      setRun(result);
      setMessage(`匹配完成：推荐 ${result.total} 名学生（引擎 ${result.engine_version}）`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "匹配失败");
    } finally {
      setLoading(false);
    }
  }

  async function onGenerateScripts(result: MatchResult) {
    if (!run) return;
    setSelected(result);
    setScriptLoading(true);
    setError("");
    try {
      const bundle = await generateScripts(run.course_id, result.student_id, result.id);
      setScripts(bundle);
    } catch (err) {
      setError(err instanceof Error ? err.message : "话术生成失败");
    } finally {
      setScriptLoading(false);
    }
  }

  async function onCreateTask(result: MatchResult) {
    if (!run) return;
    setError("");
    setMessage("");
    try {
      const task = await createMatchTask(run.course_id, result.student_id);
      setMessage(`已创建待办：${task.title}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建待办失败");
    }
  }

  return (
    <section className="max-w-6xl">
      <p className="text-sm text-[var(--muted)]">核心功能</p>
      <h2 className="mt-2 text-3xl font-semibold tracking-tight">课程匹配</h2>
      <p className="mt-2 text-[var(--muted)]">
        选择课程后一键分析学生库，按专业、阶段、作品集、标签与目标院校生成推荐名单与沟通话术。
      </p>
      <p className="mt-2 text-sm text-[var(--accent)]">{statusText}</p>

      <div className="mt-6 grid gap-3 rounded-3xl border border-[var(--line)] bg-white/80 p-4 md:grid-cols-[1.5fr_140px_auto]">
        <select
          className="rounded-xl border border-[var(--line)] bg-white px-3 py-2.5"
          value={courseId}
          onChange={(e) => setCourseId(e.target.value)}
        >
          <option value="">选择课程</option>
          {courses.map((course) => (
            <option key={course.id} value={course.id}>
              {course.name}
            </option>
          ))}
        </select>
        <label className="flex items-center gap-2 rounded-xl border border-[var(--line)] bg-white px-3 text-sm">
          <span className="text-[var(--muted)]">最低分</span>
          <input
            type="number"
            min={0}
            max={100}
            className="w-16 bg-transparent outline-none"
            value={minScore}
            onChange={(e) => setMinScore(Number(e.target.value) || 0)}
          />
        </label>
        <button
          type="button"
          onClick={onRun}
          disabled={loading || !courseId}
          className="rounded-xl bg-[var(--accent)] px-4 py-2.5 text-white disabled:opacity-60"
        >
          {loading ? "匹配中…" : "开始匹配"}
        </button>
      </div>

      {courses.length === 0 ? (
        <p className="mt-3 text-sm text-[var(--muted)]">
          还没有课程，
          <Link className="text-[var(--accent)] hover:underline" to="/courses/new">
            先去新建
          </Link>
        </p>
      ) : null}

      {error ? <p className="mt-4 text-sm text-[var(--danger)]">{error}</p> : null}
      {message ? <p className="mt-4 text-sm text-[var(--accent)]">{message}</p> : null}

      <div className="mt-6 grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <section className="rounded-3xl border border-[var(--line)] bg-white/70 p-5">
          <h3 className="text-lg font-medium">推荐名单</h3>
          <p className="mt-1 text-sm text-[var(--muted)]">
            {run?.course ? `课程：${run.course.name}` : "运行匹配后显示结果"}
          </p>
          <div className="mt-4 space-y-3">
            {!run ? (
              <p className="text-sm text-[var(--muted)]">请选择课程并点击「开始匹配」。</p>
            ) : run.results.length === 0 ? (
              <p className="text-sm text-[var(--muted)]">
                没有达到最低分的学生。可降低最低分，或完善学生专业/阶段/院校信息。
              </p>
            ) : (
              run.results.map((item) => (
                <article
                  key={item.id}
                  className={[
                    "rounded-2xl border px-4 py-3",
                    selected?.id === item.id
                      ? "border-[var(--accent)] bg-[var(--accent-soft)]/40"
                      : "border-[var(--line)] bg-white",
                  ].join(" ")}
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-xs text-[var(--muted)]">#{item.rank}</span>
                        {item.student ? (
                          <Link
                            to={`/students/${item.student.id}`}
                            className="font-medium text-[var(--accent)] hover:underline"
                          >
                            {item.student.name}
                          </Link>
                        ) : (
                          <span className="font-medium">未知学生</span>
                        )}
                        <span className="rounded-full bg-[var(--bg)] px-2 py-0.5 text-xs">
                          {item.score} 分
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-[var(--muted)]">
                        {[item.student?.major, item.student?.application_stage, `作品集 ${item.student?.portfolio_progress ?? 0}%`]
                          .filter(Boolean)
                          .join(" · ")}
                      </p>
                      {item.schools.length > 0 ? (
                        <p className="mt-1 text-xs text-[var(--muted)]">院校：{item.schools.join("、")}</p>
                      ) : null}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={() => onGenerateScripts(item)}
                        className="rounded-lg border border-[var(--line)] px-3 py-1.5 text-sm"
                      >
                        生成话术
                      </button>
                      <button
                        type="button"
                        onClick={() => onCreateTask(item)}
                        className="rounded-lg bg-[var(--accent)] px-3 py-1.5 text-sm text-white"
                      >
                        创建待办
                      </button>
                      <Link
                        to={`/follow-ups?studentId=${item.student_id}`}
                        className="rounded-lg border border-[var(--line)] px-3 py-1.5 text-sm"
                      >
                        写跟进
                      </Link>
                    </div>
                  </div>
                  <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-[var(--muted)]">
                    {item.reasons.map((reason) => (
                      <li key={reason}>{reason}</li>
                    ))}
                  </ul>
                  {item.tags.length > 0 ? (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {item.tags.map((tag) => (
                        <span
                          key={tag}
                          className="rounded-full bg-[var(--accent-soft)] px-2 py-0.5 text-xs text-[var(--accent)]"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </article>
              ))
            )}
          </div>
        </section>

        <section className="rounded-3xl border border-[var(--line)] bg-white/70 p-5">
          <h3 className="text-lg font-medium">销售话术</h3>
          <p className="mt-1 text-sm text-[var(--muted)]">
            {selected?.student
              ? `针对 ${selected.student.name}（模板引擎）`
              : "点选推荐学生的「生成话术」"}
          </p>

          {scriptLoading ? (
            <p className="mt-6 text-sm text-[var(--muted)]">生成中…</p>
          ) : scripts ? (
            <div className="mt-4 space-y-4">
              <ScriptBlock title="1. 给学生微信话术" content={scripts.wechat_student} />
              <ScriptBlock title="2. 给家长沟通话术" content={scripts.parent} />
              <ScriptBlock title="3. 电话沟通提纲" content={scripts.phone_outline} />
            </div>
          ) : (
            <p className="mt-6 text-sm text-[var(--muted)]">
              话术风格：自然、不强推；家长版含情况、必要性、风险与价值。
            </p>
          )}
        </section>
      </div>
    </section>
  );
}

function ScriptBlock({ title, content }: { title: string; content: string }) {
  async function copyText() {
    try {
      await navigator.clipboard.writeText(content);
    } catch {
      // ignore
    }
  }

  return (
    <div className="rounded-2xl border border-[var(--line)] bg-white p-4">
      <div className="flex items-center justify-between gap-3">
        <h4 className="text-sm font-medium">{title}</h4>
        <button type="button" onClick={copyText} className="text-xs text-[var(--accent)] hover:underline">
          复制
        </button>
      </div>
      <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-[var(--ink)]">{content}</p>
    </div>
  );
}
