import { Link, useNavigate } from "react-router-dom";
import { StudentForm } from "../components/StudentForm";

export function StudentNewPage() {
  const navigate = useNavigate();

  return (
    <section className="max-w-4xl">
      <p className="text-sm text-[var(--muted)]">
        <Link to="/students" className="hover:underline">学生</Link> / 新建
      </p>
      <h2 className="mt-2 text-3xl font-semibold tracking-tight">新建学生</h2>
      <p className="mt-2 text-[var(--muted)]">录入基础信息、申请目标、作品集与标签。</p>
      <div className="mt-8">
        <StudentForm
          onSuccess={(student) => navigate(`/students/${student.id}`)}
          onCancel={() => navigate("/students")}
        />
      </div>
    </section>
  );
}
