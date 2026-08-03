import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { fetchCourses, type Course } from "../lib/courses";
import {
  createTimelineEvent,
  deleteTimelineEvent,
  fetchTimeline,
  fetchTimelineOptions,
  todayDateInput,
  updateTimelineEvent,
  type TimelineItem,
  type TimelineOptions,
  type TimelineResponse,
} from "../lib/timeline";

const fieldClass =
  "w-full rounded-xl border border-[var(--line)] bg-white px-3 py-2.5 outline-none focus:border-[var(--accent)]";

function statusClass(status: string) {
  if (status === "done") return "bg-[var(--accent-soft)] text-[var(--accent)]";
  if (status === "current") return "bg-amber-50 text-[var(--warn)]";
  if (status === "absent") return "bg-red-50 text-[var(--danger)]";
  if (status === "cancelled") return "bg-[var(--bg)] text-[var(--muted)]";
  return "bg-white text-[var(--muted)] border border-[var(--line)]";
}

function formatDate(value: string) {
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("zh-CN");
}

function manualId(item: TimelineItem): number | null {
  if (!item.id.startsWith("manual:")) return null;
  const num = Number(item.id.slice(7));
  return Number.isFinite(num) ? num : null;
}

type StudentTimelineProps = {
  studentId: number;
};

export function StudentTimeline({ studentId }: StudentTimelineProps) {
  const [data, setData] = useState<TimelineResponse | null>(null);
  const [options, setOptions] = useState<TimelineOptions | null>(null);
  const [courses, setCourses] = useState<Course[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [eventType, setEventType] = useState("portfolio_milestone");
  const [title, setTitle] = useState("");
  const [eventDate, setEventDate] = useState(todayDateInput());
  const [status, setStatus] = useState("upcoming");
  const [notes, setNotes] = useState("");
  const [courseId, setCourseId] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const timeline = await fetchTimeline(studentId);
      setData(timeline);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    fetchTimelineOptions()
      .then((opts) => {
        setOptions(opts);
        if (opts.event_types[0]) setEventType(opts.event_types[0].value);
        if (opts.statuses[0]) setStatus(opts.statuses[0].value);
      })
      .catch(() => undefined);
    fetchCourses()
      .then((res) => setCourses(res.items))
      .catch(() => undefined);
  }, [studentId]);

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    if (!title.trim()) return;
    setSubmitting(true);
    setError("");
    try {
      await createTimelineEvent(studentId, {
        event_type: eventType,
        title: title.trim(),
        event_date: eventDate,
        status,
        notes: notes.trim() || null,
        related_course_id: courseId ? Number(courseId) : null,
      });
      setTitle("");
      setNotes("");
      setCourseId("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSubmitting(false);
    }
  }

  async function onMarkDone(item: TimelineItem) {
    const id = manualId(item);
    if (id == null) return;
    try {
      await updateTimelineEvent(id, { status: "done" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新失败");
    }
  }

  async function onDelete(item: TimelineItem) {
    const id = manualId(item);
    if (id == null) return;
    if (!window.confirm(`删除节点「${item.title}」？`)) return;
    try {
      await deleteTimelineEvent(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除失败");
    }
  }

  const summary = data?.summary;

  return (
    <div className="rounded-3xl border border-[var(--line)] bg-white/70 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-medium">学生时间轴</h3>
          <p className="mt-1 text-sm text-[var(--muted)]">
            聚合排课、作品集/申请节点与档案状态
            {summary
              ? ` · 共 ${summary.total}（完成 ${summary.done} / 进行中 ${summary.current} / 待办 ${summary.upcoming}）`
              : ""}
          </p>
        </div>
        <Link to="/schedule" className="text-sm text-[var(--accent)] hover:underline">
          去排课
        </Link>
      </div>

      <form onSubmit={onCreate} className="mt-4 space-y-3 rounded-2xl border border-[var(--line)] bg-white p-4">
        <p className="text-sm font-medium">添加节点</p>
        <div className="grid gap-3 md:grid-cols-3">
          <select className={fieldClass} value={eventType} onChange={(e) => setEventType(e.target.value)}>
            {(options?.event_types ?? []).map((item) => (
              <option key={item.value} value={item.value}>{item.label}</option>
            ))}
          </select>
          <select className={fieldClass} value={status} onChange={(e) => setStatus(e.target.value)}>
            {(options?.statuses ?? []).map((item) => (
              <option key={item.value} value={item.value}>{item.label}</option>
            ))}
          </select>
          <input className={fieldClass} type="date" value={eventDate} onChange={(e) => setEventDate(e.target.value)} required />
        </div>
        <input
          className={fieldClass}
          placeholder="节点标题，例如：完成项目一初稿"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />
        <div className="grid gap-3 md:grid-cols-[1fr_auto]">
          <select className={fieldClass} value={courseId} onChange={(e) => setCourseId(e.target.value)}>
            <option value="">关联课程（可选）</option>
            {courses.map((course) => (
              <option key={course.id} value={course.id}>{course.name}</option>
            ))}
          </select>
          <button
            type="submit"
            disabled={submitting}
            className="rounded-xl bg-[var(--accent)] px-4 py-2.5 text-white disabled:opacity-60"
          >
            {submitting ? "保存中…" : "添加"}
          </button>
        </div>
        <textarea
          className={`${fieldClass} min-h-16`}
          placeholder="备注（可选）"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
      </form>

      {error ? <p className="mt-3 text-sm text-[var(--danger)]">{error}</p> : null}

      <div className="mt-5 space-y-0">
        {loading ? (
          <p className="text-sm text-[var(--muted)]">加载中…</p>
        ) : !data || data.items.length === 0 ? (
          <p className="text-sm text-[var(--muted)]">暂无时间轴内容，可添加作品集/申请节点，或先去排课。</p>
        ) : (
          data.items.map((item, index) => (
            <div key={item.id} className="relative flex gap-4 pb-5 last:pb-0">
              <div className="flex w-6 flex-col items-center">
                <span
                  className={[
                    "mt-1 h-3 w-3 rounded-full",
                    item.status === "current"
                      ? "bg-[var(--warn)]"
                      : item.status === "done"
                        ? "bg-[var(--accent)]"
                        : item.status === "absent"
                          ? "bg-[var(--danger)]"
                          : "bg-[var(--line)]",
                  ].join(" ")}
                />
                {index < data.items.length - 1 ? (
                  <span className="mt-1 w-px flex-1 bg-[var(--line)]" />
                ) : null}
              </div>
              <div className="min-w-0 flex-1 rounded-2xl border border-[var(--line)] bg-white px-4 py-3">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs text-[var(--muted)]">{formatDate(item.event_date)}</span>
                      <span className={`rounded-full px-2 py-0.5 text-xs ${statusClass(item.status)}`}>
                        {item.status_label}
                      </span>
                      <span className="rounded-full bg-[var(--bg)] px-2 py-0.5 text-xs text-[var(--muted)]">
                        {item.event_type_label}
                      </span>
                    </div>
                    <p className="mt-2 font-medium">{item.title}</p>
                    {item.notes ? (
                      <p className="mt-1 whitespace-pre-wrap text-sm text-[var(--muted)]">{item.notes}</p>
                    ) : null}
                    {(item.classroom || item.teacher_name || item.course_name) && item.source === "session" ? (
                      <p className="mt-1 text-xs text-[var(--muted)]">
                        {[item.course_name, item.classroom ? `教室 ${item.classroom}` : null, item.teacher_name]
                          .filter(Boolean)
                          .join(" · ")}
                      </p>
                    ) : null}
                  </div>
                  {item.editable ? (
                    <div className="flex gap-2">
                      {item.status !== "done" ? (
                        <button
                          type="button"
                          className="text-xs text-[var(--accent)] hover:underline"
                          onClick={() => onMarkDone(item)}
                        >
                          标为完成
                        </button>
                      ) : null}
                      <button
                        type="button"
                        className="text-xs text-[var(--danger)] hover:underline"
                        onClick={() => onDelete(item)}
                      >
                        删除
                      </button>
                    </div>
                  ) : null}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
