import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { CourseForm } from "../components/CourseForm";
import { fetchCourse, type Course } from "../lib/courses";

export function CourseEditPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const courseId = Number(id);
  const [course, setCourse] = useState<Course | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!Number.isFinite(courseId)) {
      setError("无效的课程 ID");
      return;
    }
    fetchCourse(courseId)
      .then(setCourse)
      .catch((err) => setError(err instanceof Error ? err.message : "加载失败"));
  }, [courseId]);

  if (error) return <p className="text-[var(--danger)]">{error}</p>;
  if (!course) return <p className="text-[var(--muted)]">加载中…</p>;

  return (
    <section className="max-w-4xl">
      <p className="text-sm text-[var(--muted)]">
        <Link to="/courses" className="hover:underline">课程库</Link>
        {" / "}
        <Link to={`/courses/${course.id}`} className="hover:underline">{course.name}</Link>
        {" / 编辑"}
      </p>
      <h2 className="mt-2 text-3xl font-semibold tracking-tight">编辑课程</h2>
      <div className="mt-8">
        <CourseForm
          course={course}
          onSuccess={(saved) => navigate(`/courses/${saved.id}`)}
          onCancel={() => navigate(`/courses/${course.id}`)}
        />
      </div>
    </section>
  );
}
