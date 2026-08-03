import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  fetchStudentOptions,
  fetchStudents,
  type Student,
  type StudentOptions,
} from "../lib/students";

export function StudentsPage() {
  const [options, setOptions] = useState<StudentOptions | null>(null);
  const [items, setItems] = useState<Student[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [q, setQ] = useState("");
  const [major, setMajor] = useState("");
  const [applicationStage, setApplicationStage] = useState("");
  const [tagId, setTagId] = useState("");

  async function load(params?: {
    q?: string;
    major?: string;
    application_stage?: string;
    tag_id?: number;
  }) {
    setLoading(true);
    setError("");
    try {
      const data = await fetchStudents(params ?? {});
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchStudentOptions()
      .then(setOptions)
      .catch(() => undefined);
    void load();
  }, []);

  function applyFilters() {
    void load({
      q: q.trim() || undefined,
      major: major || undefined,
      application_stage: applicationStage || undefined,
      tag_id: tagId ? Number(tagId) : undefined,
    });
  }

  return (
    <section className="max-w-6xl">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm text-[var(--muted)]">学生 CRM</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight">学生管理</h2>
          <p className="mt-2 text-[var(--muted)]">共 {total} 名学生</p>
        </div>
        <Link
          to="/students/new"
          className="rounded-xl bg-[var(--accent)] px-4 py-2.5 text-white hover:opacity-90"
        >
          新建学生
        </Link>
      </div>

      <div className="mt-6 grid gap-3 rounded-3xl border border-[var(--line)] bg-white/70 p-4 md:grid-cols-[1.4fr_1fr_1fr_1fr_auto]">
        <input
          className="rounded-xl border border-[var(--line)] bg-white px-3 py-2.5 outline-none focus:border-[var(--accent)]"
          placeholder="搜索姓名 / 专业 / 国家"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && applyFilters()}
        />
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
          value={applicationStage}
          onChange={(e) => setApplicationStage(e.target.value)}
        >
          <option value="">全部阶段</option>
          {options?.application_stages.map((item) => (
            <option key={item} value={item}>{item}</option>
          ))}
        </select>
        <select
          className="rounded-xl border border-[var(--line)] bg-white px-3 py-2.5"
          value={tagId}
          onChange={(e) => setTagId(e.target.value)}
        >
          <option value="">全部标签</option>
          {options?.tags.map((tag) => (
            <option key={tag.id} value={tag.id}>{tag.name}</option>
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

      <div className="mt-6 overflow-hidden rounded-3xl border border-[var(--line)] bg-white/80">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="border-b border-[var(--line)] bg-[var(--bg)] text-[var(--muted)]">
            <tr>
              <th className="px-4 py-3 font-medium">姓名</th>
              <th className="px-4 py-3 font-medium">专业</th>
              <th className="px-4 py-3 font-medium">申请阶段</th>
              <th className="px-4 py-3 font-medium">目标院校</th>
              <th className="px-4 py-3 font-medium">作品集</th>
              <th className="px-4 py-3 font-medium">标签</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td className="px-4 py-8 text-[var(--muted)]" colSpan={6}>加载中…</td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td className="px-4 py-8 text-[var(--muted)]" colSpan={6}>
                  暂无学生，点击右上角新建。
                </td>
              </tr>
            ) : (
              items.map((student) => (
                <tr key={student.id} className="border-b border-[var(--line)] last:border-b-0 hover:bg-[var(--accent-soft)]/40">
                  <td className="px-4 py-3">
                    <Link className="font-medium text-[var(--accent)] hover:underline" to={`/students/${student.id}`}>
                      {student.name}
                    </Link>
                    <p className="text-xs text-[var(--muted)]">{student.grade || "年级未填"}</p>
                  </td>
                  <td className="px-4 py-3">{student.major || "—"}</td>
                  <td className="px-4 py-3">{student.application_stage || "—"}</td>
                  <td className="px-4 py-3">
                    {student.schools.length
                      ? student.schools.map((s) => s.school_name).join("、")
                      : "—"}
                  </td>
                  <td className="px-4 py-3">
                    {student.portfolio_started ? `${student.portfolio_progress}%` : "未开始"}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {student.tags.length === 0 ? (
                        <span className="text-[var(--muted)]">—</span>
                      ) : (
                        student.tags.map((tag) => (
                          <span
                            key={tag.id}
                            className="rounded-full bg-[var(--accent-soft)] px-2 py-0.5 text-xs text-[var(--accent)]"
                          >
                            {tag.name}
                          </span>
                        ))
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
