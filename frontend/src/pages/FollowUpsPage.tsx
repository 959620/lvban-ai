import { useEffect, useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  CONTACT_WITH_LABEL,
  createFollowUp,
  deleteFollowUp,
  fetchFollowUps,
  type ContactWith,
  type FollowUp,
} from "../lib/followUps";
import { fetchStudents, type Student } from "../lib/students";

function formatDateTime(value: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN");
}

function nowLocalInputValue() {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 16);
}

const fieldClass =
  "w-full rounded-xl border border-[var(--line)] bg-white px-3 py-2.5 outline-none focus:border-[var(--accent)]";

export function FollowUpsPage() {
  const [searchParams] = useSearchParams();
  const presetStudentId = searchParams.get("studentId") || "";

  const [items, setItems] = useState<FollowUp[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [filterStudentId, setFilterStudentId] = useState(presetStudentId);
  const [filterContactWith, setFilterContactWith] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [studentId, setStudentId] = useState(presetStudentId);
  const [contactDate, setContactDate] = useState(nowLocalInputValue());
  const [contactWith, setContactWith] = useState<ContactWith>("student");
  const [content, setContent] = useState("");
  const [result, setResult] = useState("");
  const [nextAction, setNextAction] = useState("");
  const [nextRemindAt, setNextRemindAt] = useState("");
  const [createTask, setCreateTask] = useState(true);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [list, studentList] = await Promise.all([
        fetchFollowUps({
          student_id: filterStudentId ? Number(filterStudentId) : undefined,
          contact_with: (filterContactWith as ContactWith) || undefined,
        }),
        fetchStudents(),
      ]);
      setItems(list.items);
      setStudents(studentList.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [filterStudentId, filterContactWith]);

  useEffect(() => {
    if (presetStudentId) {
      setStudentId(presetStudentId);
      setFilterStudentId(presetStudentId);
    }
  }, [presetStudentId]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!studentId) {
      setError("请选择学生");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      await createFollowUp({
        student_id: Number(studentId),
        contact_date: new Date(contactDate).toISOString(),
        contact_with: contactWith,
        content: content.trim(),
        result: result.trim() || null,
        next_action: nextAction.trim() || null,
        next_remind_at: nextRemindAt ? new Date(nextRemindAt).toISOString() : null,
        create_task: createTask,
      });
      setContent("");
      setResult("");
      setNextAction("");
      setNextRemindAt("");
      setContactDate(nowLocalInputValue());
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSubmitting(false);
    }
  }

  async function onDelete(item: FollowUp) {
    if (!window.confirm("确认删除这条跟进记录？")) return;
    try {
      await deleteFollowUp(item.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除失败");
    }
  }

  return (
    <section className="max-w-5xl">
      <p className="text-sm text-[var(--muted)]">学生跟进</p>
      <h2 className="mt-2 text-3xl font-semibold tracking-tight">跟进记录</h2>
      <p className="mt-2 text-[var(--muted)]">
        记录沟通内容与下一步；填写下次提醒后，会同步到工作台「今天需要联系」，并可自动生成待办。
      </p>

      {error ? <p className="mt-4 text-sm text-[var(--danger)]">{error}</p> : null}

      <form onSubmit={onSubmit} className="mt-6 space-y-4 rounded-3xl border border-[var(--line)] bg-white/80 p-5">
        <h3 className="text-lg font-medium">新建跟进</h3>
        <div className="grid gap-4 md:grid-cols-3">
          <label className="text-sm">
            <span className="mb-1.5 block text-[var(--muted)]">学生 *</span>
            <select className={fieldClass} value={studentId} onChange={(e) => setStudentId(e.target.value)} required>
              <option value="">选择学生</option>
              {students.map((student) => (
                <option key={student.id} value={student.id}>
                  {student.name}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            <span className="mb-1.5 block text-[var(--muted)]">沟通对象</span>
            <select
              className={fieldClass}
              value={contactWith}
              onChange={(e) => setContactWith(e.target.value as ContactWith)}
            >
              <option value="student">学生</option>
              <option value="parent">家长</option>
            </select>
          </label>
          <label className="text-sm">
            <span className="mb-1.5 block text-[var(--muted)]">沟通日期</span>
            <input
              type="datetime-local"
              className={fieldClass}
              value={contactDate}
              onChange={(e) => setContactDate(e.target.value)}
              required
            />
          </label>
        </div>

        <label className="block text-sm">
          <span className="mb-1.5 block text-[var(--muted)]">沟通内容 *</span>
          <textarea
            className={`${fieldClass} min-h-24`}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            required
            placeholder="本次沟通说了什么"
          />
        </label>

        <div className="grid gap-4 md:grid-cols-2">
          <label className="text-sm">
            <span className="mb-1.5 block text-[var(--muted)]">结果</span>
            <textarea
              className={`${fieldClass} min-h-20`}
              value={result}
              onChange={(e) => setResult(e.target.value)}
              placeholder="对方态度、是否达成一致等"
            />
          </label>
          <label className="text-sm">
            <span className="mb-1.5 block text-[var(--muted)]">下一步</span>
            <textarea
              className={`${fieldClass} min-h-20`}
              value={nextAction}
              onChange={(e) => setNextAction(e.target.value)}
              placeholder="例如：三天后催交草图"
            />
          </label>
        </div>

        <div className="grid gap-4 md:grid-cols-[1.4fr_auto] md:items-end">
          <label className="text-sm">
            <span className="mb-1.5 block text-[var(--muted)]">下次提醒时间</span>
            <input
              type="datetime-local"
              className={fieldClass}
              value={nextRemindAt}
              onChange={(e) => setNextRemindAt(e.target.value)}
            />
          </label>
          <label className="flex items-center gap-2 rounded-xl border border-[var(--line)] bg-white px-3 py-2.5 text-sm">
            <input
              type="checkbox"
              checked={createTask}
              onChange={(e) => setCreateTask(e.target.checked)}
              disabled={!nextRemindAt}
            />
            自动生成待办
          </label>
        </div>

        {students.length === 0 ? (
          <p className="text-sm text-[var(--muted)]">
            还没有学生，
            <Link className="text-[var(--accent)] hover:underline" to="/students/new">
              先去新建
            </Link>
          </p>
        ) : null}

        <button
          type="submit"
          disabled={submitting || students.length === 0}
          className="rounded-xl bg-[var(--accent)] px-5 py-2.5 text-white disabled:opacity-60"
        >
          {submitting ? "保存中…" : "保存跟进"}
        </button>
      </form>

      <div className="mt-8 flex flex-wrap gap-3">
        <select
          className="rounded-xl border border-[var(--line)] bg-white px-3 py-2.5 text-sm"
          value={filterStudentId}
          onChange={(e) => setFilterStudentId(e.target.value)}
        >
          <option value="">全部学生</option>
          {students.map((student) => (
            <option key={student.id} value={student.id}>
              {student.name}
            </option>
          ))}
        </select>
        <select
          className="rounded-xl border border-[var(--line)] bg-white px-3 py-2.5 text-sm"
          value={filterContactWith}
          onChange={(e) => setFilterContactWith(e.target.value)}
        >
          <option value="">全部对象</option>
          <option value="student">学生</option>
          <option value="parent">家长</option>
        </select>
      </div>

      <div className="mt-4 space-y-3">
        {loading ? (
          <p className="text-sm text-[var(--muted)]">加载中…</p>
        ) : items.length === 0 ? (
          <p className="rounded-3xl border border-dashed border-[var(--line)] bg-white/50 p-6 text-sm text-[var(--muted)]">
            暂无跟进记录。
          </p>
        ) : (
          items.map((item) => (
            <article key={item.id} className="rounded-3xl border border-[var(--line)] bg-white/80 p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    {item.student ? (
                      <Link
                        to={`/students/${item.student.id}`}
                        className="text-lg font-medium text-[var(--accent)] hover:underline"
                      >
                        {item.student.name}
                      </Link>
                    ) : (
                      <span className="text-lg font-medium">未知学生</span>
                    )}
                    <span className="rounded-full bg-[var(--accent-soft)] px-2 py-0.5 text-xs text-[var(--accent)]">
                      {CONTACT_WITH_LABEL[item.contact_with]}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-[var(--muted)]">{formatDateTime(item.contact_date)}</p>
                </div>
                <button
                  type="button"
                  onClick={() => onDelete(item)}
                  className="text-sm text-[var(--muted)] hover:text-[var(--danger)]"
                >
                  删除
                </button>
              </div>
              <p className="mt-3 whitespace-pre-wrap text-sm leading-6">{item.content}</p>
              <div className="mt-4 grid gap-3 text-sm md:grid-cols-3">
                <div>
                  <p className="text-[var(--muted)]">结果</p>
                  <p className="mt-1 whitespace-pre-wrap">{item.result || "—"}</p>
                </div>
                <div>
                  <p className="text-[var(--muted)]">下一步</p>
                  <p className="mt-1 whitespace-pre-wrap">{item.next_action || "—"}</p>
                </div>
                <div>
                  <p className="text-[var(--muted)]">下次提醒</p>
                  <p className="mt-1">{formatDateTime(item.next_remind_at)}</p>
                  {item.created_task_id ? (
                    <p className="mt-1 text-xs text-[var(--accent)]">已生成待办 #{item.created_task_id}</p>
                  ) : null}
                </div>
              </div>
            </article>
          ))
        )}
      </div>
    </section>
  );
}
