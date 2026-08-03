import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { deleteCourse, fetchCourse, formatPrice, type Course } from "../lib/courses";

export function CourseDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const courseId = Number(id);
  const [course, setCourse] = useState<Course | null>(null);
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (!Number.isFinite(courseId)) {
      setError("无效的课程 ID");
      return;
    }
    fetchCourse(courseId)
      .then(setCourse)
      .catch((err) => setError(err instanceof Error ? err.message : "加载失败"));
  }, [courseId]);

  async function onDelete() {
    if (!course) return;
    if (!window.confirm(`确认删除课程「${course.name}」？`)) return;
    setDeleting(true);
    try {
      await deleteCourse(course.id);
      navigate("/courses");
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除失败");
      setDeleting(false);
    }
  }

  if (error && !course) return <p className="text-[var(--danger)]">{error}</p>;
  if (!course) return <p className="text-[var(--muted)]">加载中…</p>;

  return (
    <section className="max-w-4xl">
      <p className="text-sm text-[var(--muted)]">
        <Link to="/courses" className="hover:underline">课程库</Link> / 详情
      </p>

      <div className="mt-2 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-3xl font-semibold tracking-tight">{course.name}</h2>
          <p className="mt-2 text-[var(--muted)]">
            {[course.course_type, course.teacher_name, formatPrice(course.price)]
              .filter(Boolean)
              .join(" · ")}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            to={`/match?courseId=${course.id}`}
            className="rounded-xl border border-[var(--line)] bg-white px-4 py-2.5"
          >
            去匹配学生
          </Link>
          <Link
            to={`/courses/${course.id}/edit`}
            className="rounded-xl bg-[var(--accent)] px-4 py-2.5 text-white"
          >
            编辑
          </Link>
          <button
            type="button"
            onClick={onDelete}
            disabled={deleting}
            className="rounded-xl border border-[var(--line)] bg-white px-4 py-2.5 text-[var(--danger)] disabled:opacity-60"
          >
            {deleting ? "删除中…" : "删除"}
          </button>
        </div>
      </div>

      {error ? <p className="mt-4 text-sm text-[var(--danger)]">{error}</p> : null}

      <div className="mt-8 space-y-4">
        <div className="rounded-3xl border border-[var(--line)] bg-white/70 p-5">
          <h3 className="font-medium">课程目标</h3>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-6">{course.goal || "暂无"}</p>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-3xl border border-[var(--line)] bg-white/70 p-5">
            <h3 className="font-medium">适合专业</h3>
            <div className="mt-3 flex flex-wrap gap-2">
              {course.suitable_majors.length === 0 ? (
                <span className="text-sm text-[var(--muted)]">未设置</span>
              ) : (
                course.suitable_majors.map((item) => (
                  <span
                    key={item}
                    className="rounded-full bg-[var(--accent-soft)] px-3 py-1 text-xs text-[var(--accent)]"
                  >
                    {item}
                  </span>
                ))
              )}
            </div>
          </div>
          <div className="rounded-3xl border border-[var(--line)] bg-white/70 p-5">
            <h3 className="font-medium">适合阶段</h3>
            <div className="mt-3 flex flex-wrap gap-2">
              {course.suitable_stages.length === 0 ? (
                <span className="text-sm text-[var(--muted)]">未设置</span>
              ) : (
                course.suitable_stages.map((item) => (
                  <span
                    key={item}
                    className="rounded-full border border-[var(--line)] bg-white px-3 py-1 text-xs text-[var(--muted)]"
                  >
                    {item}
                  </span>
                ))
              )}
            </div>
          </div>
        </div>

        <div className="rounded-3xl border border-[var(--line)] bg-white/70 p-5">
          <h3 className="font-medium">补充说明</h3>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-6">
            {course.description || "暂无"}
          </p>
        </div>
      </div>
    </section>
  );
}
