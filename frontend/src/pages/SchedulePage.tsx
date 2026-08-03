import { useEffect, useMemo, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { fetchCourses, type Course } from "../lib/courses";
import {
  STATUS_LABEL,
  createSession,
  deleteSession,
  fetchScheduleDay,
  fetchScheduleOptions,
  fetchScheduleWeek,
  markAbsent,
  markComplete,
  todayDateInput,
  updateSessionStatus,
  type ClassSession,
  type ScheduleOptions,
  type SessionStatus,
} from "../lib/schedule";
import { fetchStudents, type Student } from "../lib/students";

const fieldClass =
  "w-full rounded-xl border border-[var(--line)] bg-white px-3 py-2.5 outline-none focus:border-[var(--accent)]";

function shiftDate(base: string, days: number) {
  const date = new Date(`${base}T00:00:00`);
  date.setDate(date.getDate() + days);
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 10);
}

function statusClass(status: SessionStatus) {
  if (status === "absent") return "text-[var(--danger)] bg-red-50";
  if (status === "completed") return "text-[var(--accent)] bg-[var(--accent-soft)]";
  if (status === "cancelled") return "text-[var(--muted)] bg-[var(--bg)]";
  return "text-[var(--warn)] bg-amber-50";
}

export function SchedulePage() {
  const [view, setView] = useState<"day" | "week">("day");
  const [day, setDay] = useState(todayDateInput());
  const [items, setItems] = useState<ClassSession[]>([]);
  const [occupied, setOccupied] = useState<string[]>([]);
  const [absentCount, setAbsentCount] = useState(0);
  const [students, setStudents] = useState<Student[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [options, setOptions] = useState<ScheduleOptions | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [studentId, setStudentId] = useState("");
  const [courseId, setCourseId] = useState("");
  const [sessionDate, setSessionDate] = useState(todayDateInput());
  const [startTime, setStartTime] = useState("10:00");
  const [endTime, setEndTime] = useState("12:00");
  const [classroom, setClassroom] = useState("");
  const [teacherName, setTeacherName] = useState("");
  const [sessionType, setSessionType] = useState("一对一");
  const [notes, setNotes] = useState("");

  const titleDate = useMemo(() => {
    if (view === "day") return day;
    return `周视图（含 ${day}）`;
  }, [view, day]);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const data = view === "day" ? await fetchScheduleDay(day) : await fetchScheduleWeek(day);
      setItems(data.items);
      setOccupied(data.occupied_classrooms);
      setAbsentCount(data.absent_count);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchStudents()
      .then((data) => setStudents(data.items))
      .catch(() => undefined);
    fetchCourses()
      .then((data) => setCourses(data.items))
      .catch(() => undefined);
    fetchScheduleOptions()
      .then((data) => {
        setOptions(data);
        if (data.session_types[0]) setSessionType(data.session_types[0]);
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    void load();
  }, [day, view]);

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    if (!studentId) {
      setError("请选择学生");
      return;
    }
    setSubmitting(true);
    setError("");
    setMessage("");
    try {
      const created = await createSession({
        student_id: Number(studentId),
        course_id: courseId ? Number(courseId) : null,
        session_date: sessionDate,
        start_time: startTime,
        end_time: endTime,
        classroom: classroom.trim() || null,
        teacher_name: teacherName.trim() || null,
        session_type: sessionType,
        status: "scheduled",
        notes: notes.trim() || null,
      });
      if (created.classroom_conflict) {
        setMessage("已创建，但检测到教室时段冲突，请核对安排。");
      } else {
        setMessage("排课已创建");
      }
      setNotes("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建失败");
    } finally {
      setSubmitting(false);
    }
  }

  async function onStatus(session: ClassSession, status: SessionStatus) {
    try {
      if (status === "absent") await markAbsent(session.id);
      else if (status === "completed") await markComplete(session.id);
      else await updateSessionStatus(session.id, status);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新失败");
    }
  }

  async function onDelete(session: ClassSession) {
    if (!window.confirm("确认删除这节课？")) return;
    try {
      await deleteSession(session.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除失败");
    }
  }

  return (
    <section className="max-w-6xl">
      <p className="text-sm text-[var(--muted)]">学生日程</p>
      <h2 className="mt-2 text-3xl font-semibold tracking-tight">排课管理</h2>
      <p className="mt-2 text-[var(--muted)]">
        预约课程、查看教室占用、标记完成或缺课。当前查看：{titleDate}
      </p>

      <form onSubmit={onCreate} className="mt-6 space-y-4 rounded-3xl border border-[var(--line)] bg-white/80 p-5">
        <h3 className="text-lg font-medium">新建预约</h3>
        <div className="grid gap-3 md:grid-cols-3">
          <select className={fieldClass} value={studentId} onChange={(e) => setStudentId(e.target.value)} required>
            <option value="">选择学生</option>
            {students.map((student) => (
              <option key={student.id} value={student.id}>{student.name}</option>
            ))}
          </select>
          <select className={fieldClass} value={courseId} onChange={(e) => setCourseId(e.target.value)}>
            <option value="">关联课程（可选）</option>
            {courses.map((course) => (
              <option key={course.id} value={course.id}>{course.name}</option>
            ))}
          </select>
          <select className={fieldClass} value={sessionType} onChange={(e) => setSessionType(e.target.value)}>
            {(options?.session_types ?? ["一对一"]).map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </div>
        <div className="grid gap-3 md:grid-cols-4">
          <input className={fieldClass} type="date" value={sessionDate} onChange={(e) => setSessionDate(e.target.value)} required />
          <input className={fieldClass} type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} required />
          <input className={fieldClass} type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)} required />
          <input className={fieldClass} placeholder="教室（自由文本）" value={classroom} onChange={(e) => setClassroom(e.target.value)} />
        </div>
        <div className="grid gap-3 md:grid-cols-[1fr_1.4fr_auto]">
          <input className={fieldClass} placeholder="老师（自由文本）" value={teacherName} onChange={(e) => setTeacherName(e.target.value)} />
          <input className={fieldClass} placeholder="备注" value={notes} onChange={(e) => setNotes(e.target.value)} />
          <button
            type="submit"
            disabled={submitting || students.length === 0}
            className="rounded-xl bg-[var(--accent)] px-4 py-2.5 text-white disabled:opacity-60"
          >
            {submitting ? "保存中…" : "添加排课"}
          </button>
        </div>
        {students.length === 0 ? (
          <p className="text-sm text-[var(--muted)]">
            还没有学生，
            <Link className="text-[var(--accent)] hover:underline" to="/students/new">先去新建</Link>
          </p>
        ) : null}
      </form>

      {error ? <p className="mt-4 text-sm text-[var(--danger)]">{error}</p> : null}
      {message ? <p className="mt-4 text-sm text-[var(--accent)]">{message}</p> : null}

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <div className="flex rounded-xl border border-[var(--line)] bg-white p-1">
          <button
            type="button"
            className={`rounded-lg px-3 py-1.5 text-sm ${view === "day" ? "bg-[var(--accent)] text-white" : "text-[var(--muted)]"}`}
            onClick={() => setView("day")}
          >
            日视图
          </button>
          <button
            type="button"
            className={`rounded-lg px-3 py-1.5 text-sm ${view === "week" ? "bg-[var(--accent)] text-white" : "text-[var(--muted)]"}`}
            onClick={() => setView("week")}
          >
            周视图
          </button>
        </div>
        <button type="button" className="rounded-xl border border-[var(--line)] bg-white px-3 py-2 text-sm" onClick={() => setDay(shiftDate(day, -1))}>
          前一天
        </button>
        <input
          type="date"
          className="rounded-xl border border-[var(--line)] bg-white px-3 py-2 text-sm"
          value={day}
          onChange={(e) => setDay(e.target.value)}
        />
        <button type="button" className="rounded-xl border border-[var(--line)] bg-white px-3 py-2 text-sm" onClick={() => setDay(shiftDate(day, 1))}>
          后一天
        </button>
        <button type="button" className="rounded-xl border border-[var(--line)] bg-white px-3 py-2 text-sm" onClick={() => setDay(todayDateInput())}>
          回到今天
        </button>
      </div>

      <div className="mt-4 grid gap-4 md:grid-cols-[1.4fr_0.8fr]">
        <section className="rounded-3xl border border-[var(--line)] bg-white/70 p-5">
          <h3 className="text-lg font-medium">课表</h3>
          <p className="mt-1 text-sm text-[var(--muted)]">
            共 {items.length} 节 · 缺课 {absentCount}
          </p>
          <div className="mt-4 space-y-3">
            {loading ? (
              <p className="text-sm text-[var(--muted)]">加载中…</p>
            ) : items.length === 0 ? (
              <p className="text-sm text-[var(--muted)]">该时段暂无排课。</p>
            ) : (
              items.map((session) => (
                <article key={session.id} className="rounded-2xl border border-[var(--line)] bg-white px-4 py-3">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-medium">
                          {session.start_time}-{session.end_time}
                        </span>
                        <span className={`rounded-full px-2 py-0.5 text-xs ${statusClass(session.status)}`}>
                          {STATUS_LABEL[session.status]}
                        </span>
                        {session.classroom_conflict ? (
                          <span className="rounded-full bg-red-50 px-2 py-0.5 text-xs text-[var(--danger)]">
                            教室冲突
                          </span>
                        ) : null}
                      </div>
                      <p className="mt-1 text-sm">
                        {session.student ? (
                          <Link className="text-[var(--accent)] hover:underline" to={`/students/${session.student.id}`}>
                            {session.student.name}
                          </Link>
                        ) : (
                          "未知学生"
                        )}
                        {" · "}
                        {session.session_type}
                        {session.course ? ` · ${session.course.name}` : ""}
                      </p>
                      <p className="mt-1 text-xs text-[var(--muted)]">
                        {session.session_date} · 教室 {session.classroom || "未填"} · 老师 {session.teacher_name || "未填"}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <button type="button" className="rounded-lg border border-[var(--line)] px-2.5 py-1 text-xs" onClick={() => onStatus(session, "completed")}>
                        完成
                      </button>
                      <button type="button" className="rounded-lg border border-[var(--line)] px-2.5 py-1 text-xs" onClick={() => onStatus(session, "absent")}>
                        缺课
                      </button>
                      <button type="button" className="rounded-lg border border-[var(--line)] px-2.5 py-1 text-xs" onClick={() => onStatus(session, "cancelled")}>
                        取消
                      </button>
                      <button type="button" className="rounded-lg px-2.5 py-1 text-xs text-[var(--danger)]" onClick={() => onDelete(session)}>
                        删除
                      </button>
                    </div>
                  </div>
                </article>
              ))
            )}
          </div>
        </section>

        <section className="rounded-3xl border border-[var(--line)] bg-white/70 p-5">
          <h3 className="text-lg font-medium">教室占用</h3>
          <p className="mt-1 text-sm text-[var(--muted)]">当前视图内已使用教室</p>
          <div className="mt-4 space-y-2">
            {occupied.length === 0 ? (
              <p className="text-sm text-[var(--muted)]">暂无教室占用记录</p>
            ) : (
              occupied.map((room) => (
                <div key={room} className="rounded-xl border border-[var(--line)] bg-white px-3 py-2 text-sm">
                  {room}
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </section>
  );
}
