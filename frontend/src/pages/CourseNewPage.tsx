import { Link, useNavigate } from "react-router-dom";
import { CourseForm } from "../components/CourseForm";

export function CourseNewPage() {
  const navigate = useNavigate();

  return (
    <section className="max-w-4xl">
      <p className="text-sm text-[var(--muted)]">
        <Link to="/courses" className="hover:underline">课程库</Link> / 新建
      </p>
      <h2 className="mt-2 text-3xl font-semibold tracking-tight">新建课程</h2>
      <p className="mt-2 text-[var(--muted)]">录入课程类型、适合专业与阶段，供后续匹配使用。</p>
      <div className="mt-8">
        <CourseForm
          onSuccess={(course) => navigate(`/courses/${course.id}`)}
          onCancel={() => navigate("/courses")}
        />
      </div>
    </section>
  );
}
