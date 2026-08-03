import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  fetchCourseOptions,
  fetchCourses,
  formatPrice,
  type Course,
  type CourseOptions,
} from "../lib/courses";

export function CoursesPage() {
  const [options, setOptions] = useState<CourseOptions | null>(null);
  const [items, setItems] = useState<Course[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [q, setQ] = useState("");
  const [courseType, setCourseType] = useState("");
  const [major, setMajor] = useState("");
  const [stage, setStage] = useState("");

  async function load(params?: {
    q?: string;
    course_type?: string;
    major?: string;
    stage?: string;
  }) {
    setLoading(true);
    setError("");
    try {
      const data = await fetchCourses(params ?? {});
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchCourseOptions()
      .then(setOptions)
      .catch(() => undefined);
    void load();
  }, []);

  function applyFilters() {
    void load({
      q: q.trim() || undefined,
      course_type: courseType || undefined,
      major: major || undefined,
      stage: stage || undefined,
    });
  }

  return (
    <section className="max-w-6xl">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm text-[var(--muted)]">课程库</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight">课程管理</h2>
          <p className="mt-2 text-[var(--muted)]">共 {total} 门课程</p>
        </div>
        <Link
          to="/courses/new"
          className="rounded-xl bg-[var(--accent)] px-4 py-2.5 text-white hover:opacity-90"
        >
          新建课程
        </Link>
      </div>

      <div className="mt-6 grid gap-3 rounded-3xl border border-[var(--line)] bg-white/70 p-4 md:grid-cols-[1.3fr_1fr_1fr_1fr_auto]">
        <input
          className="rounded-xl border border-[var(--line)] bg-white px-3 py-2.5 outline-none focus:border-[var(--accent)]"
          placeholder="搜索课程名 / 老师 / 目标"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && applyFilters()}
        />
        <select
          className="rounded-xl border border-[var(--line)] bg-white px-3 py-2.5"
          value={courseType}
          onChange={(e) => setCourseType(e.target.value)}
        >
          <option value="">全部类型</option>
          {options?.course_types.map((item) => (
            <option key={item} value={item}>{item}</option>
          ))}
        </select>
        <select
          className="rounded-xl border border-[var(--line)] bg-white px-3 py-2.5"
          value={major}
          onChange={(e) => setMajor(e.target.value)}
        >
          <option value="">全部专业</option>
          {options?.majors.map((item) => (
            <option key={item} value={item}>{item}</option>
          ))}
        </select>
        <select
          className="rounded-xl border border-[var(--line)] bg-white px-3 py-2.5"
          value={stage}
          onChange={(e) => setStage(e.target.value)}
        >
          <option value="">全部阶段</option>
          {options?.suitable_stages.map((item) => (
            <option key={item} value={item}>{item}</option>
          ))}
        </select>
        <button
          type="button"
          onClick={applyFilters}
          className="rounded-xl bg-[var(--accent)] px-4 py-2.5 text-white"
        >
          筛选
        </button>
      </div>

      {error ? <p className="mt-4 text-sm text-[var(--danger)]">{error}</p> : null}

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {loading ? (
          <p className="text-sm text-[var(--muted)]">加载中…</p>
        ) : items.length === 0 ? (
          <p className="rounded-3xl border border-dashed border-[var(--line)] bg-white/50 p-6 text-sm text-[var(--muted)] md:col-span-2">
            暂无课程，点击右上角新建。
          </p>
        ) : (
          items.map((course) => (
            <Link
              key={course.id}
              to={`/courses/${course.id}`}
              className="rounded-3xl border border-[var(--line)] bg-white/80 p-5 transition hover:border-[var(--accent)]"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-lg font-medium">{course.name}</h3>
                  <p className="mt-1 text-sm text-[var(--muted)]">
                    {course.course_type}
                    {course.teacher_name ? ` · ${course.teacher_name}` : ""}
                  </p>
                </div>
                <span className="shrink-0 text-sm text-[var(--accent)]">{formatPrice(course.price)}</span>
              </div>
              <p className="mt-3 line-clamp-2 text-sm text-[var(--muted)]">
                {course.goal || "暂无课程目标"}
              </p>
              <div className="mt-4 flex flex-wrap gap-1">
                {course.suitable_majors.slice(0, 4).map((item) => (
                  <span
                    key={item}
                    className="rounded-full bg-[var(--accent-soft)] px-2 py-0.5 text-xs text-[var(--accent)]"
                  >
                    {item}
                  </span>
                ))}
                {course.suitable_majors.length > 4 ? (
                  <span className="text-xs text-[var(--muted)]">+{course.suitable_majors.length - 4}</span>
                ) : null}
              </div>
            </Link>
          ))
        )}
      </div>
    </section>
  );
}
