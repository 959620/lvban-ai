import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const navItems = [
  { to: "/", label: "工作台", end: true },
  { to: "/students", label: "学生" },
  { to: "/schedule", label: "日程" },
  { to: "/courses", label: "课程库" },
  { to: "/match", label: "课程匹配" },
  { to: "/follow-ups", label: "跟进" },
  { to: "/ai", label: "AI 助手" },
];

export function AppLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[240px_1fr]">
      <aside className="border-b border-[var(--line)] bg-[var(--bg-elevated)] px-5 py-6 lg:border-b-0 lg:border-r">
        <div className="mb-8">
          <p className="text-xs tracking-[0.18em] text-[var(--muted)] uppercase">Jiaowu Desk</p>
          <h1 className="mt-2 text-2xl font-semibold text-[var(--ink)]">教务智能工作台</h1>
          <p className="mt-2 text-sm text-[var(--muted)]">个人教务助手 · 可扩展 CRM</p>
        </div>

        <nav className="flex gap-2 overflow-x-auto pb-2 lg:flex-col lg:gap-1 lg:overflow-visible lg:pb-0">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                [
                  "whitespace-nowrap rounded-xl px-3 py-2 text-sm transition",
                  isActive
                    ? "bg-[var(--accent)] text-white"
                    : "text-[var(--muted)] hover:bg-[var(--accent-soft)] hover:text-[var(--ink)]",
                ].join(" ")
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="mt-8 hidden rounded-2xl border border-[var(--line)] bg-white/70 p-4 lg:block">
          <p className="text-sm font-medium">{user?.display_name}</p>
          <p className="mt-1 text-xs text-[var(--muted)]">@{user?.username}</p>
          <button
            type="button"
            onClick={logout}
            className="mt-4 text-sm text-[var(--accent)] hover:underline"
          >
            退出登录
          </button>
        </div>
      </aside>

      <main className="px-5 py-6 lg:px-10 lg:py-8">
        <div className="mb-4 flex items-center justify-between lg:hidden">
          <div>
            <p className="text-sm font-medium">{user?.display_name}</p>
            <p className="text-xs text-[var(--muted)]">@{user?.username}</p>
          </div>
          <button
            type="button"
            onClick={logout}
            className="rounded-lg border border-[var(--line)] px-3 py-1.5 text-sm"
          >
            退出
          </button>
        </div>
        <Outlet />
      </main>
    </div>
  );
}
