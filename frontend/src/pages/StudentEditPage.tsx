import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { StudentForm } from "../components/StudentForm";
import { fetchStudent, type Student } from "../lib/students";

export function StudentEditPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const studentId = Number(id);
  const [student, setStudent] = useState<Student | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!Number.isFinite(studentId)) {
      setError("无效的学生 ID");
      return;
    }
    fetchStudent(studentId)
      .then(setStudent)
      .catch((err) => setError(err instanceof Error ? err.message : "加载失败"));
  }, [studentId]);

  if (error) {
    return <p className="text-[var(--danger)]">{error}</p>;
  }

  if (!student) {
    return <p className="text-[var(--muted)]">加载中…</p>;
  }

  return (
    <section className="max-w-4xl">
      <p className="text-sm text-[var(--muted)]">
        <Link to="/students" className="hover:underline">学生</Link>
        {" / "}
        <Link to={`/students/${student.id}`} className="hover:underline">{student.name}</Link>
        {" / 编辑"}
      </p>
      <h2 className="mt-2 text-3xl font-semibold tracking-tight">编辑学生</h2>
      <div className="mt-8">
        <StudentForm
          student={student}
          onSuccess={(saved) => navigate(`/students/${saved.id}`)}
          onCancel={() => navigate(`/students/${student.id}`)}
        />
      </div>
    </section>
  );
}
