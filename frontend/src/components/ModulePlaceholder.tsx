type ModulePlaceholderProps = {
  title: string;
  description: string;
  nextHint?: string;
};

export function ModulePlaceholder({ title, description, nextHint }: ModulePlaceholderProps) {
  return (
    <section className="max-w-3xl">
      <p className="text-sm text-[var(--muted)]">模块占位</p>
      <h2 className="mt-2 text-3xl font-semibold tracking-tight">{title}</h2>
      <p className="mt-3 max-w-2xl text-[var(--muted)]">{description}</p>
      <div className="mt-8 rounded-3xl border border-dashed border-[var(--line)] bg-white/60 p-6">
        <p className="text-sm text-[var(--muted)]">
          {nextHint ?? "业务逻辑将在后续 Step 中逐个实现。当前仅完成路由与布局骨架。"}
        </p>
      </div>
    </section>
  );
}
