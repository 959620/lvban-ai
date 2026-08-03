import { useEffect, useState, type ReactNode } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { StudentTimeline } from "../components/StudentTimeline";
import {
  CONTACT_WITH_LABEL,
  fetchFollowUps,
  type FollowUp,
} from "../lib/followUps";
import { deleteStudent, fetchStudent, type Student } from "../lib/students";

function formatDateTime(value: string | null) {
  if (!value) return "未设置";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN");
}

export function StudentDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const studentId = Number(id);
  const [student, setStudent] = useState<Student | null>(null);
  const [followUps, setFollowUps] = useState<FollowUp[]>([]);
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (!Number.isFinite(studentId)) {
      setError("无效的学生 ID");
      return;
    }
    Promise.all([fetchStudent(studentId), fetchFollowUps({ student_id: studentId })])
      .then(([studentData, followUpData]) => {
        setStudent(studentData);
        setFollowUps(followUpData.items.slice(0, 5));
      })
      .catch((err) => setError(err instanceof Error ? err.message : "加载失败"));
  }, [studentId]);

  async function onDelete() {
    if (!student) return;
    if (!window.confirm(`确认删除学生「${student.name}」？此操作不可恢复。`)) return;
    setDeleting(true);
    try {
      await deleteStudent(student.id);
      navigate("/students");
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除失败");
      setDeleting(false);
    }
  }

  if (error && !student) {
    return <p className="text-[var(--danger)]">{error}</p>;
  }

  if (!student) {
    return <p className="text-[var(--muted)]">加载中…</p>;
  }

  return (
    <section className="max-w-5xl">
      <p className="text-sm text-[var(--muted)]">
        <Link to="/students" className="hover:underline">学生</Link> / 详情
      </p>

      <div className="mt-2 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-3xl font-semibold tracking-tight">{student.name}</h2>
          <p className="mt-2 text-[var(--muted)]">
            {[student.grade, student.major, student.application_stage]
              .filter(Boolean)
              .join(" · ") || "基础信息待完善"}
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {student.tags.map((tag) => (
              <span
                key={tag.id}
                className="rounded-full bg-[var(--accent-soft)] px-3 py-1 text-xs text-[var(--accent)]"
              >
                {tag.name}
              </span>
            ))}
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            to={`/follow-ups?studentId=${student.id}`}
            className="rounded-xl border border-[var(--line)] bg-white px-4 py-2.5"
          >
            写跟进
          </Link>
          <Link
            to={`/students/${student.id}/edit`}
            className="rounded-xl bg-[var(--accent)] px-4 py-2.5 text-white"
          >
            编辑
          </Link>
          <button
            type="button"
            onClick={onDelete}
            disabled={deleting}
            className="rounded-xl border border-[var(--line)] bg-white px-4 py-2.5 text-[var(--danger)] disabled:opacity-60"
          >
            {deleting ? "删除中…" : "删除"}
          </button>
        </div>
      </div>

      {error ? <p className="mt-4 text-sm text-[var(--danger)]">{error}</p> : null}

      <div className="mt-8 grid gap-4 md:grid-cols-2">
        <InfoCard title="联系方式">
          <Row label="学生" value={student.phone || "—"} />
          <Row label="家长" value={student.parent_phone || "—"} />
          <Row label="下次联系" value={formatDateTime(student.next_contact_at)} />
        </InfoCard>

        <InfoCard title="申请信息">
          <Row label="目标国家" value={student.target_country || "—"} />
          <Row label="目标专业" value={student.target_major || "—"} />
          <Row label="入学年份" value={student.intake_year?.toString() || "—"} />
          <Row label="申请阶段" value={student.application_stage || "—"} />
        </InfoCard>

        <InfoCard title="目标院校">
          {student.schools.length === 0 ? (
            <p className="text-sm text-[var(--muted)]">尚未填写</p>
          ) : (
            <ul className="space-y-2">
              {student.schools.map((school) => (
                <li key={school.id} className="flex items-center justify-between text-sm">
                  <span>{school.school_name}</span>
                  <span className="text-[var(--muted)]">{school.priority || "未分级"}</span>
                </li>
              ))}
            </ul>
          )}
        </InfoCard>

        <InfoCard title="作品集">
          <Row label="是否开始" value={student.portfolio_started ? "是" : "否"} />
          <Row label="项目数量" value={String(student.portfolio_project_count)} />
          <Row label="完成度" value={`${student.portfolio_progress}%`} />
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-[var(--line)]">
            <div
              className="h-full rounded-full bg-[var(--accent)]"
              style={{ width: `${student.portfolio_progress}%` }}
            />
          </div>
        </InfoCard>
      </div>

      <div className="mt-4 grid gap-4">
        <InfoCard title="备注">
          <Note label="学生性格" value={student.personality_notes} />
          <Note label="家庭情况" value={student.family_notes} />
          <Note label="沟通习惯" value={student.communication_notes} />
          <Note label="重要事件" value={student.important_events} />
        </InfoCard>

        <div className="rounded-3xl border border-[var(--line)] bg-white/70 p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h3 className="font-medium">最近跟进</h3>
            <Link
              to={`/follow-ups?studentId=${student.id}`}
              className="text-sm text-[var(--accent)] hover:underline"
            >
              查看全部 / 新建
            </Link>
          </div>
          <div className="mt-4 space-y-3">
            {followUps.length === 0 ? (
              <p className="text-sm text-[var(--muted)]">暂无跟进记录。</p>
            ) : (
              followUps.map((item) => (
                <div key={item.id} className="rounded-2xl border border-[var(--line)] bg-white px-4 py-3">
                  <div className="flex flex-wrap items-center gap-2 text-sm">
                    <span className="rounded-full bg-[var(--accent-soft)] px-2 py-0.5 text-xs text-[var(--accent)]">
                      {CONTACT_WITH_LABEL[item.contact_with]}
                    </span>
                    <span className="text-[var(--muted)]">{formatDateTime(item.contact_date)}</span>
                  </div>
                  <p className="mt-2 whitespace-pre-wrap text-sm leading-6">{item.content}</p>
                  {item.next_remind_at ? (
                    <p className="mt-2 text-xs text-[var(--muted)]">
                      下次提醒：{formatDateTime(item.next_remind_at)}
                    </p>
                  ) : null}
                </div>
              ))
            )}
          </div>
        </div>

        <StudentTimeline studentId={student.id} />
      </div>
    </section>
  );
}

function InfoCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-3xl border border-[var(--line)] bg-white/70 p-5">
      <h3 className="font-medium">{title}</h3>
      <div className="mt-4 space-y-3">{children}</div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 text-sm">
      <span className="text-[var(--muted)]">{label}</span>
      <span className="text-right">{value}</span>
    </div>
  );
}

function Note({ label, value }: { label: string; value: string | null }) {
  return (
    <div>
      <p className="text-sm text-[var(--muted)]">{label}</p>
      <p className="mt-1 whitespace-pre-wrap text-sm leading-6">{value || "暂无"}</p>
    </div>
  );
}
