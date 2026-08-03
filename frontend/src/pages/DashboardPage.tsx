import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { fetchScheduleDay, STATUS_LABEL, type ClassSession } from "../lib/schedule";
import { fetchStudents, type Student } from "../lib/students";
import {
  PRIORITY_LABEL,
  createTask,
  deleteTask,
  fetchDashboard,
  toggleTask,
  type DashboardData,
  type TaskItem,
  type TaskPriority,
} from "../lib/tasks";

function formatDateTime(value: string | null) {
  if (!value) return "未设置截止";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function todayLocalInputValue() {
  const now = new Date();
  const offset = now.getTimezoneOffset();
  const local = new Date(now.getTime() - offset * 60_000);
  return local.toISOString().slice(0, 16);
}

function priorityClass(priority: TaskPriority) {
  if (priority === "urgent") return "text-[var(--danger)] bg-red-50";
  if (priority === "low") return "text-[var(--muted)] bg-[var(--bg)]";
  return "text-[var(--warn)] bg-amber-50";
}

export function DashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [todaySessions, setTodaySessions] = useState<ClassSession[]>([]);
  const [occupiedRooms, setOccupiedRooms] = useState<string[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [error, setError] = useState("");
  const [studentError, setStudentError] = useState("");
  const [loading, setLoading] = useState(true);
  const [studentsLoading, setStudentsLoading] = useState(true);
  const [title, setTitle] = useState("");
  const [studentId, setStudentId] = useState("");
  const [dueAt, setDueAt] = useState(todayLocalInputValue());
  const [priority, setPriority] = useState<TaskPriority>("normal");
  const [submitting, setSubmitting] = useState(false);

  async function loadDashboard() {
    setLoading(true);
    setError("");
    try {
      const dashboard = await fetchDashboard(3);
      setData(dashboard);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }

  async function loadStudents() {
    setStudentsLoading(true);
    setStudentError("");
    try {
      const studentList = await fetchStudents();
      setStudents(studentList.items);
    } catch (err) {
      setStudents([]);
      setStudentError(err instanceof Error ? err.message : "学生列表加载失败");
    } finally {
      setStudentsLoading(false);
    }
  }

  async function loadSchedule() {
    try {
      const schedule = await fetchScheduleDay();
      setTodaySessions(schedule.items);
      setOccupiedRooms(schedule.occupied_classrooms);
    } catch {
      setTodaySessions([]);
      setOccupiedRooms([]);
    }
  }

  async function load() {
    await Promise.all([loadDashboard(), loadStudents(), loadSchedule()]);
  }

  useEffect(() => {
    void load();
  }, []);

  const stats = useMemo(
    () =>
      data?.stats ?? {
        today_count: 0,
        contact_count: 0,
        upcoming_count: 0,
        incomplete_count: 0,
        todo_total: 0,
      },
    [data],
  );

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    if (!title.trim()) return;
    setSubmitting(true);
    setError("");
    try {
      await createTask({
        title: title.trim(),
        student_id: studentId ? Number(studentId) : null,
        due_at: dueAt ? new Date(dueAt).toISOString() : null,
        priority,
        status: "todo",
        source: "manual",
      });
      setTitle("");
      setStudentId("");
      setPriority("normal");
      setDueAt(todayLocalInputValue());
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建失败");
    } finally {
      setSubmitting(false);
    }
  }

  async function onToggle(task: TaskItem) {
    try {
      await toggleTask(task.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新失败");
    }
  }

  async function onDelete(task: TaskItem) {
    if (!window.confirm(`删除任务「${task.title}」？`)) return;
    try {
      await deleteTask(task.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除失败");
    }
  }

  return (
    <section className="max-w-6xl">
      <p className="text-sm text-[var(--muted)]">首页工作台</p>
      <h2 className="mt-2 text-3xl font-semibold tracking-tight">
        你好，{user?.display_name}
      </h2>
      <p className="mt-2 text-[var(--muted)]">
        今天待办 {stats.today_count} · 需联系 {stats.contact_count} · 即将截止{" "}
        {stats.upcoming_count} · 未完成 {stats.incomplete_count}
      </p>

      {error ? <p className="mt-4 text-sm text-[var(--danger)]">{error}</p> : null}
      {studentError ? <p className="mt-2 text-sm text-[var(--danger)]">{studentError}</p> : null}

      <form
        onSubmit={onCreate}
        className="mt-6 space-y-3 rounded-3xl border border-[var(--line)] bg-white/80 p-4"
      >
        <div className="grid gap-3 lg:grid-cols-[1.5fr_1.2fr]">
          <input
            className="rounded-xl border border-[var(--line)] bg-white px-3 py-2.5 outline-none focus:border-[var(--accent)]"
            placeholder="添加今日任务，例如：催交作品集草图"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
          <label className="flex min-w-0 items-center gap-2 rounded-xl border border-[var(--line)] bg-white px-3 py-2">
            <span className="shrink-0 text-sm text-[var(--muted)]">关联学生：</span>
            <select
              className="min-w-0 flex-1 bg-transparent py-1 outline-none"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              disabled={studentsLoading}
            >
              <option value="">不关联学生</option>
              {students.map((student) => (
                <option key={student.id} value={String(student.id)}>
                  {student.name}
                  {student.major ? `（${student.major}）` : ""}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="grid gap-3 sm:grid-cols-[1.4fr_140px_auto]">
          <label className="flex min-w-0 items-center gap-2 rounded-xl border border-[var(--line)] bg-white px-3 py-2">
            <span className="shrink-0 text-sm text-[var(--muted)]">截止时间：</span>
            <input
              type="datetime-local"
              className="min-w-0 flex-1 bg-transparent py-1 outline-none"
              value={dueAt}
              onChange={(e) => setDueAt(e.target.value)}
            />
          </label>
          <select
            className="rounded-xl border border-[var(--line)] bg-white px-3 py-2.5"
            value={priority}
            onChange={(e) => setPriority(e.target.value as TaskPriority)}
          >
            <option value="urgent">紧急</option>
            <option value="normal">普通</option>
            <option value="low">低</option>
          </select>
          <button
            type="submit"
            disabled={submitting}
            className="rounded-xl bg-[var(--accent)] px-4 py-2.5 text-white disabled:opacity-60"
          >
            {submitting ? "添加中…" : "添加"}
          </button>
        </div>

        {!studentsLoading && students.length === 0 ? (
          <p className="text-sm text-[var(--muted)]">
            当前账号下还没有学生，下拉只能选「不关联学生」。
            <Link className="ml-1 text-[var(--accent)] hover:underline" to="/students/new">
              去新建学生
            </Link>
          </p>
        ) : null}
      </form>

      <div className="mt-6 grid gap-4 xl:grid-cols-[1.2fr_1fr]">
        <Panel title="今日待办" subtitle="截止日为今天，或你刚添加的今日任务">
          {loading ? (
            <Empty text="加载中…" />
          ) : data && data.today_tasks.length > 0 ? (
            <TaskList items={data.today_tasks} onToggle={onToggle} onDelete={onDelete} />
          ) : (
            <Empty text="今天暂无待办，上方快速添加一条吧。" />
          )}
        </Panel>

        <Panel title="今日提醒" subtitle="联系学生 · 即将截止 · 未完成">
          <ReminderBlock
            title="今天需要联系"
            empty="今天没有安排联系的学生"
            count={data?.contact_students.length ?? 0}
          >
            {data?.contact_students.map((student) => (
              <Link
                key={student.id}
                to={`/students/${student.id}`}
                className="block rounded-2xl border border-[var(--line)] bg-white px-3 py-2.5 hover:border-[var(--accent)]"
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="font-medium">{student.name}</span>
                  <span className="text-xs text-[var(--muted)]">
                    {formatDateTime(student.next_contact_at)}
                  </span>
                </div>
                <p className="mt-1 text-xs text-[var(--muted)]">
                  {[student.major, student.application_stage].filter(Boolean).join(" · ") ||
                    "档案待完善"}
                </p>
              </Link>
            ))}
          </ReminderBlock>

          <ReminderBlock
            title="即将截止（3 天内）"
            empty="暂无即将截止任务"
            count={data?.upcoming_tasks.length ?? 0}
          >
            <TaskList
              items={data?.upcoming_tasks ?? []}
              onToggle={onToggle}
              onDelete={onDelete}
              compact
            />
          </ReminderBlock>

          <ReminderBlock
            title="未完成事项"
            empty="没有逾期或未安排截止的任务"
            count={data?.incomplete_tasks.length ?? 0}
          >
            <TaskList
              items={data?.incomplete_tasks ?? []}
              onToggle={onToggle}
              onDelete={onDelete}
              compact
            />
          </ReminderBlock>
        </Panel>
      </div>

      <div className="mt-4 rounded-3xl border border-[var(--line)] bg-white/70 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-medium">今日课表</h3>
            <p className="mt-1 text-sm text-[var(--muted)]">
              {todaySessions.length} 节课
              {occupiedRooms.length > 0 ? ` · 占用教室 ${occupiedRooms.join("、")}` : ""}
            </p>
          </div>
          <Link to="/schedule" className="text-sm text-[var(--accent)] hover:underline">
            管理排课
          </Link>
        </div>
        <div className="mt-4 space-y-2">
          {todaySessions.length === 0 ? (
            <p className="text-sm text-[var(--muted)]">今天暂无排课。</p>
          ) : (
            todaySessions.map((session) => (
              <div
                key={session.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-[var(--line)] bg-white px-3 py-2.5 text-sm"
              >
                <div>
                  <p className="font-medium">
                    {session.start_time}-{session.end_time}
                    {session.classroom ? ` · ${session.classroom}` : ""}
                    {session.classroom_conflict ? " · 冲突" : ""}
                  </p>
                  <p className="mt-1 text-xs text-[var(--muted)]">
                    {session.student?.name || "学生"} · {session.session_type}
                    {session.teacher_name ? ` · ${session.teacher_name}` : ""}
                  </p>
                </div>
                <span className="text-xs text-[var(--muted)]">{STATUS_LABEL[session.status]}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </section>
  );
}

function Panel({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-3xl border border-[var(--line)] bg-white/70 p-5">
      <h3 className="text-lg font-medium">{title}</h3>
      <p className="mt-1 text-sm text-[var(--muted)]">{subtitle}</p>
      <div className="mt-4 space-y-3">{children}</div>
    </section>
  );
}

function ReminderBlock({
  title,
  empty,
  count,
  children,
}: {
  title: string;
  empty: string;
  count: number;
  children: ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-[var(--line)] bg-[var(--bg)]/60 p-3">
      <div className="mb-2 flex items-center justify-between">
        <h4 className="text-sm font-medium">{title}</h4>
        <span className="text-xs text-[var(--muted)]">{count}</span>
      </div>
      {count === 0 ? <Empty text={empty} /> : <div className="space-y-2">{children}</div>}
    </div>
  );
}

function Empty({ text }: { text: string }) {
  return <p className="text-sm text-[var(--muted)]">{text}</p>;
}

function TaskList({
  items,
  onToggle,
  onDelete,
  compact = false,
}: {
  items: TaskItem[];
  onToggle: (task: TaskItem) => void;
  onDelete: (task: TaskItem) => void;
  compact?: boolean;
}) {
  return (
    <ul className="space-y-2">
      {items.map((task) => (
        <li
          key={task.id}
          className={[
            "rounded-2xl border border-[var(--line)] bg-white",
            compact ? "px-3 py-2" : "px-3 py-3",
          ].join(" ")}
        >
          <div className="flex items-start gap-3">
            <input
              type="checkbox"
              className="mt-1"
              checked={task.status === "done"}
              onChange={() => onToggle(task)}
            />
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <p
                  className={[
                    "font-medium",
                    task.status === "done" ? "text-[var(--muted)] line-through" : "",
                  ].join(" ")}
                >
                  {task.title}
                </p>
                <span className={`rounded-full px-2 py-0.5 text-xs ${priorityClass(task.priority)}`}>
                  {PRIORITY_LABEL[task.priority]}
                </span>
              </div>
              <p className="mt-1 text-xs text-[var(--muted)]">
                {task.student ? (
                  <Link className="text-[var(--accent)] hover:underline" to={`/students/${task.student.id}`}>
                    {task.student.name}
                  </Link>
                ) : (
                  "未关联学生"
                )}
                {" · "}
                {formatDateTime(task.due_at)}
              </p>
            </div>
            <button
              type="button"
              onClick={() => onDelete(task)}
              className="text-xs text-[var(--muted)] hover:text-[var(--danger)]"
            >
              删除
            </button>
          </div>
        </li>
      ))}
    </ul>
  );
}
