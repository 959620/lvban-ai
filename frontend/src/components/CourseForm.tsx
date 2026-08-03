import { useEffect, useState, type FormEvent } from "react";
import {
  createCourse,
  fetchCourseOptions,
  updateCourse,
  type Course,
  type CourseOptions,
  type CoursePayload,
} from "../lib/courses";

type FormState = {
  name: string;
  course_type: string;
  suitable_majors: string[];
  suitable_stages: string[];
  goal: string;
  price: string;
  teacher_name: string;
  description: string;
};

const emptyForm = (): FormState => ({
  name: "",
  course_type: "训练营",
  suitable_majors: [],
  suitable_stages: [],
  goal: "",
  price: "",
  teacher_name: "",
  description: "",
});

function fromCourse(course: Course): FormState {
  return {
    name: course.name,
    course_type: course.course_type,
    suitable_majors: course.suitable_majors ?? [],
    suitable_stages: course.suitable_stages ?? [],
    goal: course.goal ?? "",
    price: course.price === null || course.price === undefined ? "" : String(course.price),
    teacher_name: course.teacher_name ?? "",
    description: course.description ?? "",
  };
}

function toPayload(form: FormState): CoursePayload {
  const emptyToNull = (value: string) => {
    const trimmed = value.trim();
    return trimmed ? trimmed : null;
  };
  return {
    name: form.name.trim(),
    course_type: form.course_type,
    suitable_majors: form.suitable_majors,
    suitable_stages: form.suitable_stages,
    goal: emptyToNull(form.goal),
    price: form.price.trim() === "" ? null : Number(form.price),
    teacher_name: emptyToNull(form.teacher_name),
    description: emptyToNull(form.description),
  };
}

const fieldClass =
  "w-full rounded-xl border border-[var(--line)] bg-white px-3 py-2.5 outline-none focus:border-[var(--accent)]";
const labelClass = "mb-1.5 block text-sm text-[var(--muted)]";

type CourseFormProps = {
  course?: Course;
  onSuccess: (course: Course) => void;
  onCancel: () => void;
};

export function CourseForm({ course, onSuccess, onCancel }: CourseFormProps) {
  const [options, setOptions] = useState<CourseOptions | null>(null);
  const [form, setForm] = useState<FormState>(course ? fromCourse(course) : emptyForm());
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchCourseOptions()
      .then((data) => {
        setOptions(data);
        if (!course) {
          setForm((prev) => ({
            ...prev,
            course_type: data.course_types[0] ?? "其他",
          }));
        }
      })
      .catch((err) => setError(err instanceof Error ? err.message : "加载选项失败"));
  }, [course]);

  function toggleInList(key: "suitable_majors" | "suitable_stages", value: string) {
    setForm((prev) => {
      const list = prev[key];
      return {
        ...prev,
        [key]: list.includes(value) ? list.filter((item) => item !== value) : [...list, value],
      };
    });
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const payload = toPayload(form);
      const saved = course
        ? await updateCourse(course.id, payload)
        : await createCourse(payload);
      onSuccess(saved);
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="space-y-6" onSubmit={onSubmit}>
      <section className="rounded-3xl border border-[var(--line)] bg-white/70 p-6">
        <h3 className="text-lg font-medium">基本信息</h3>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <label className="md:col-span-2">
            <span className={labelClass}>课程名称 *</span>
            <input
              className={fieldClass}
              required
              value={form.name}
              onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
              placeholder="例如：RISD作品集提升训练营"
            />
          </label>
          <label>
            <span className={labelClass}>课程类型</span>
            <select
              className={fieldClass}
              value={form.course_type}
              onChange={(e) => setForm((prev) => ({ ...prev, course_type: e.target.value }))}
            >
              {options?.course_types.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </label>
          <label>
            <span className={labelClass}>授课老师</span>
            <input
              className={fieldClass}
              value={form.teacher_name}
              onChange={(e) => setForm((prev) => ({ ...prev, teacher_name: e.target.value }))}
            />
          </label>
          <label>
            <span className={labelClass}>价格（元）</span>
            <input
              className={fieldClass}
              type="number"
              min={0}
              step="0.01"
              value={form.price}
              onChange={(e) => setForm((prev) => ({ ...prev, price: e.target.value }))}
            />
          </label>
          <label className="md:col-span-2">
            <span className={labelClass}>课程目标</span>
            <textarea
              className={`${fieldClass} min-h-20`}
              value={form.goal}
              onChange={(e) => setForm((prev) => ({ ...prev, goal: e.target.value }))}
              placeholder="例如：提升作品集完整度"
            />
          </label>
          <label className="md:col-span-2">
            <span className={labelClass}>补充说明</span>
            <textarea
              className={`${fieldClass} min-h-20`}
              value={form.description}
              onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))}
            />
          </label>
        </div>
      </section>

      <section className="rounded-3xl border border-[var(--line)] bg-white/70 p-6">
        <h3 className="text-lg font-medium">适合专业</h3>
        <div className="mt-4 flex flex-wrap gap-2">
          {options?.majors.map((major) => {
            const active = form.suitable_majors.includes(major);
            return (
              <button
                key={major}
                type="button"
                onClick={() => toggleInList("suitable_majors", major)}
                className={[
                  "rounded-full px-3 py-1.5 text-sm transition",
                  active
                    ? "bg-[var(--accent)] text-white"
                    : "border border-[var(--line)] bg-white text-[var(--muted)] hover:border-[var(--accent)]",
                ].join(" ")}
              >
                {major}
              </button>
            );
          })}
        </div>
      </section>

      <section className="rounded-3xl border border-[var(--line)] bg-white/70 p-6">
        <h3 className="text-lg font-medium">适合阶段</h3>
        <div className="mt-4 flex flex-wrap gap-2">
          {options?.suitable_stages.map((stage) => {
            const active = form.suitable_stages.includes(stage);
            return (
              <button
                key={stage}
                type="button"
                onClick={() => toggleInList("suitable_stages", stage)}
                className={[
                  "rounded-full px-3 py-1.5 text-sm transition",
                  active
                    ? "bg-[var(--accent)] text-white"
                    : "border border-[var(--line)] bg-white text-[var(--muted)] hover:border-[var(--accent)]",
                ].join(" ")}
              >
                {stage}
              </button>
            );
          })}
        </div>
      </section>

      {error ? <p className="text-sm text-[var(--danger)]">{error}</p> : null}

      <div className="flex flex-wrap gap-3">
        <button
          type="submit"
          disabled={submitting}
          className="rounded-xl bg-[var(--accent)] px-5 py-2.5 text-white disabled:opacity-60"
        >
          {submitting ? "保存中…" : course ? "保存修改" : "创建课程"}
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
