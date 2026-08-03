import { useEffect, useState, type FormEvent } from "react";
import {
  createStudent,
  fetchStudentOptions,
  updateStudent,
  type Student,
  type StudentOptions,
  type StudentPayload,
} from "../lib/students";

type SchoolDraft = { school_name: string; priority: string };

type FormState = {
  name: string;
  grade: string;
  phone: string;
  parent_phone: string;
  major: string;
  target_country: string;
  target_major: string;
  intake_year: string;
  application_stage: string;
  portfolio_started: boolean;
  portfolio_project_count: string;
  portfolio_progress: string;
  personality_notes: string;
  family_notes: string;
  communication_notes: string;
  important_events: string;
  next_contact_at: string;
  schools: SchoolDraft[];
  tag_ids: number[];
};

const emptyForm = (): FormState => ({
  name: "",
  grade: "",
  phone: "",
  parent_phone: "",
  major: "",
  target_country: "",
  target_major: "",
  intake_year: "",
  application_stage: "",
  portfolio_started: false,
  portfolio_project_count: "0",
  portfolio_progress: "0",
  personality_notes: "",
  family_notes: "",
  communication_notes: "",
  important_events: "",
  next_contact_at: "",
  schools: [{ school_name: "", priority: "" }],
  tag_ids: [],
});

function fromStudent(student: Student): FormState {
  return {
    name: student.name,
    grade: student.grade ?? "",
    phone: student.phone ?? "",
    parent_phone: student.parent_phone ?? "",
    major: student.major ?? "",
    target_country: student.target_country ?? "",
    target_major: student.target_major ?? "",
    intake_year: student.intake_year?.toString() ?? "",
    application_stage: student.application_stage ?? "",
    portfolio_started: student.portfolio_started,
    portfolio_project_count: String(student.portfolio_project_count),
    portfolio_progress: String(student.portfolio_progress),
    personality_notes: student.personality_notes ?? "",
    family_notes: student.family_notes ?? "",
    communication_notes: student.communication_notes ?? "",
    important_events: student.important_events ?? "",
    next_contact_at: student.next_contact_at
      ? student.next_contact_at.slice(0, 16)
      : "",
    schools:
      student.schools.length > 0
        ? student.schools.map((s) => ({
            school_name: s.school_name,
            priority: s.priority ?? "",
          }))
        : [{ school_name: "", priority: "" }],
    tag_ids: student.tags.map((t) => t.id),
  };
}

function toPayload(form: FormState): StudentPayload {
  const emptyToNull = (value: string) => {
    const trimmed = value.trim();
    return trimmed ? trimmed : null;
  };

  return {
    name: form.name.trim(),
    grade: emptyToNull(form.grade),
    phone: emptyToNull(form.phone),
    parent_phone: emptyToNull(form.parent_phone),
    major: emptyToNull(form.major),
    target_country: emptyToNull(form.target_country),
    target_major: emptyToNull(form.target_major),
    intake_year: form.intake_year ? Number(form.intake_year) : null,
    application_stage: emptyToNull(form.application_stage),
    portfolio_started: form.portfolio_started,
    portfolio_project_count: Number(form.portfolio_project_count || 0),
    portfolio_progress: Number(form.portfolio_progress || 0),
    personality_notes: emptyToNull(form.personality_notes),
    family_notes: emptyToNull(form.family_notes),
    communication_notes: emptyToNull(form.communication_notes),
    important_events: emptyToNull(form.important_events),
    next_contact_at: form.next_contact_at
      ? new Date(form.next_contact_at).toISOString()
      : null,
    schools: form.schools
      .filter((s) => s.school_name.trim())
      .map((s) => ({
        school_name: s.school_name.trim(),
        priority: s.priority || null,
      })),
    tag_ids: form.tag_ids,
  };
}

const fieldClass =
  "w-full rounded-xl border border-[var(--line)] bg-white px-3 py-2.5 outline-none focus:border-[var(--accent)]";
const labelClass = "mb-1.5 block text-sm text-[var(--muted)]";

type StudentFormProps = {
  student?: Student;
  onSuccess: (student: Student) => void;
  onCancel: () => void;
};

export function StudentForm({ student, onSuccess, onCancel }: StudentFormProps) {
  const [options, setOptions] = useState<StudentOptions | null>(null);
  const [form, setForm] = useState<FormState>(student ? fromStudent(student) : emptyForm());
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchStudentOptions()
      .then(setOptions)
      .catch((err) => setError(err instanceof Error ? err.message : "加载选项失败"));
  }, []);

  function patch<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function toggleTag(tagId: number) {
    setForm((prev) => ({
      ...prev,
      tag_ids: prev.tag_ids.includes(tagId)
        ? prev.tag_ids.filter((id) => id !== tagId)
        : [...prev.tag_ids, tagId],
    }));
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const payload = toPayload(form);
      const saved = student
        ? await updateStudent(student.id, payload)
        : await createStudent(payload);
      onSuccess(saved);
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="space-y-8" onSubmit={onSubmit}>
      <section className="rounded-3xl border border-[var(--line)] bg-white/70 p-6">
        <h3 className="text-lg font-medium">基础信息</h3>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <label>
            <span className={labelClass}>学生姓名 *</span>
            <input className={fieldClass} required value={form.name} onChange={(e) => patch("name", e.target.value)} />
          </label>
          <label>
            <span className={labelClass}>年级</span>
            <input className={fieldClass} value={form.grade} onChange={(e) => patch("grade", e.target.value)} placeholder="如：高二 / 大一" />
          </label>
          <label>
            <span className={labelClass}>学生联系方式</span>
            <input className={fieldClass} value={form.phone} onChange={(e) => patch("phone", e.target.value)} />
          </label>
          <label>
            <span className={labelClass}>家长联系方式</span>
            <input className={fieldClass} value={form.parent_phone} onChange={(e) => patch("parent_phone", e.target.value)} />
          </label>
        </div>
      </section>

      <section className="rounded-3xl border border-[var(--line)] bg-white/70 p-6">
        <h3 className="text-lg font-medium">专业与申请</h3>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <label>
            <span className={labelClass}>艺术专业方向</span>
            <select className={fieldClass} value={form.major} onChange={(e) => patch("major", e.target.value)}>
              <option value="">未选择</option>
              {options?.majors.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </label>
          <label>
            <span className={labelClass}>目标国家</span>
            <input className={fieldClass} value={form.target_country} onChange={(e) => patch("target_country", e.target.value)} placeholder="如：美国 / 英国" />
          </label>
          <label>
            <span className={labelClass}>目标专业</span>
            <input className={fieldClass} value={form.target_major} onChange={(e) => patch("target_major", e.target.value)} />
          </label>
          <label>
            <span className={labelClass}>入学年份</span>
            <input className={fieldClass} type="number" min={2020} max={2040} value={form.intake_year} onChange={(e) => patch("intake_year", e.target.value)} />
          </label>
          <label className="md:col-span-2">
            <span className={labelClass}>当前申请阶段</span>
            <select className={fieldClass} value={form.application_stage} onChange={(e) => patch("application_stage", e.target.value)}>
              <option value="">未选择</option>
              {options?.application_stages.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </label>
        </div>

        <div className="mt-6">
          <div className="mb-3 flex items-center justify-between">
            <h4 className="font-medium">目标院校（可多条）</h4>
            <button
              type="button"
              className="text-sm text-[var(--accent)] hover:underline"
              onClick={() =>
                patch("schools", [...form.schools, { school_name: "", priority: "" }])
              }
            >
              + 添加院校
            </button>
          </div>
          <div className="space-y-3">
            {form.schools.map((school, index) => (
              <div key={index} className="grid gap-3 md:grid-cols-[1fr_160px_auto]">
                <input
                  className={fieldClass}
                  placeholder="院校名称，如 RISD"
                  value={school.school_name}
                  onChange={(e) => {
                    const next = [...form.schools];
                    next[index] = { ...next[index], school_name: e.target.value };
                    patch("schools", next);
                  }}
                />
                <select
                  className={fieldClass}
                  value={school.priority}
                  onChange={(e) => {
                    const next = [...form.schools];
                    next[index] = { ...next[index], priority: e.target.value };
                    patch("schools", next);
                  }}
                >
                  <option value="">优先级</option>
                  {options?.school_priorities.map((item) => (
                    <option key={item} value={item}>{item}</option>
                  ))}
                </select>
                <button
                  type="button"
                  className="rounded-xl border border-[var(--line)] px-3 text-sm text-[var(--muted)] hover:text-[var(--danger)]"
                  onClick={() => {
                    const next = form.schools.filter((_, i) => i !== index);
                    patch("schools", next.length ? next : [{ school_name: "", priority: "" }]);
                  }}
                >
                  删除
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="rounded-3xl border border-[var(--line)] bg-white/70 p-6">
        <h3 className="text-lg font-medium">作品集</h3>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <label className="flex items-center gap-3 rounded-xl border border-[var(--line)] bg-white px-3 py-2.5">
            <input
              type="checkbox"
              checked={form.portfolio_started}
              onChange={(e) => patch("portfolio_started", e.target.checked)}
            />
            <span className="text-sm">已开始制作作品集</span>
          </label>
          <label>
            <span className={labelClass}>当前项目数量</span>
            <input className={fieldClass} type="number" min={0} value={form.portfolio_project_count} onChange={(e) => patch("portfolio_project_count", e.target.value)} />
          </label>
          <label>
            <span className={labelClass}>完成度（0-100）</span>
            <input className={fieldClass} type="number" min={0} max={100} value={form.portfolio_progress} onChange={(e) => patch("portfolio_progress", e.target.value)} />
          </label>
        </div>
      </section>

      <section className="rounded-3xl border border-[var(--line)] bg-white/70 p-6">
        <h3 className="text-lg font-medium">学生标签</h3>
        <div className="mt-4 flex flex-wrap gap-2">
          {options?.tags.map((tag) => {
            const active = form.tag_ids.includes(tag.id);
            return (
              <button
                key={tag.id}
                type="button"
                onClick={() => toggleTag(tag.id)}
                className={[
                  "rounded-full px-3 py-1.5 text-sm transition",
                  active
                    ? "bg-[var(--accent)] text-white"
                    : "border border-[var(--line)] bg-white text-[var(--muted)] hover:border-[var(--accent)]",
                ].join(" ")}
              >
                {tag.name}
              </button>
            );
          })}
          {!options ? <p className="text-sm text-[var(--muted)]">标签加载中…</p> : null}
        </div>
      </section>

      <section className="rounded-3xl border border-[var(--line)] bg-white/70 p-6">
        <h3 className="text-lg font-medium">备注</h3>
        <div className="mt-4 grid gap-4">
          <label>
            <span className={labelClass}>学生性格</span>
            <textarea className={`${fieldClass} min-h-20`} value={form.personality_notes} onChange={(e) => patch("personality_notes", e.target.value)} />
          </label>
          <label>
            <span className={labelClass}>家庭情况</span>
            <textarea className={`${fieldClass} min-h-20`} value={form.family_notes} onChange={(e) => patch("family_notes", e.target.value)} />
          </label>
          <label>
            <span className={labelClass}>沟通习惯</span>
            <textarea className={`${fieldClass} min-h-20`} value={form.communication_notes} onChange={(e) => patch("communication_notes", e.target.value)} />
          </label>
          <label>
            <span className={labelClass}>重要事件</span>
            <textarea className={`${fieldClass} min-h-20`} value={form.important_events} onChange={(e) => patch("important_events", e.target.value)} />
          </label>
          <label>
            <span className={labelClass}>下次应联系时间</span>
            <input className={fieldClass} type="datetime-local" value={form.next_contact_at} onChange={(e) => patch("next_contact_at", e.target.value)} />
          </label>
        </div>
      </section>

      {error ? <p className="text-sm text-[var(--danger)]">{error}</p> : null}

      <div className="flex flex-wrap gap-3">
        <button
          type="submit"
          disabled={submitting}
          className="rounded-xl bg-[var(--accent)] px-5 py-2.5 text-white disabled:opacity-60"
        >
          {submitting ? "保存中…" : student ? "保存修改" : "创建学生"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-xl border border-[var(--line)] bg-white px-5 py-2.5"
        >
          取消
        </button>
      </div>
    </form>
  );
}
