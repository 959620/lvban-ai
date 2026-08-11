/**
 * Step 4–5 前端：
 * - 自然语言解析预览 → 确认创建 / 一键创建
 * - 任务列表筛选、完成、取消、开始跟进
 */

const $ = (id) => document.getElementById(id);

function toDatetimeLocalValue(isoOrNull) {
  if (!isoOrNull) return "";
  const d = new Date(isoOrNull);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function fromDatetimeLocalValue(value) {
  if (!value) return null;
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return null;
  return d.toISOString();
}

function formatDue(iso) {
  if (!iso) return "无截止时间";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("zh-CN", { hour12: false });
}

function fillPreview(parsed) {
  $("preview-panel").hidden = false;
  $("f-title").value = parsed.task || "";
  $("f-student").value = parsed.student || "";
  $("f-due").value = toDatetimeLocalValue(parsed.deadline);
  $("f-priority").value = parsed.priority || "medium";
  $("parse-meta").textContent = `引擎：${parsed.parse_source || "rule"}｜置信度：${parsed.parse_confidence || "low"}｜原文：${parsed.source_text || ""}`;
  window.__lastParsed = parsed;
}

function showResult(data) {
  $("result-panel").hidden = false;
  $("result-box").textContent = JSON.stringify(data, null, 2);
}

function reminderSummary(reminders) {
  if (!reminders || !reminders.length) return "无提醒";
  const scheduled = reminders.filter((r) => r.status === "scheduled").length;
  return `${reminders.length} 条提醒（待发送 ${scheduled}）`;
}

function renderTasks(payload) {
  const box = $("task-list");
  const items = payload.items || [];
  $("list-meta").textContent = `共 ${payload.total || 0} 条`;

  if (!items.length) {
    box.innerHTML = `<p class="empty">暂无任务，先在上方创建一条吧。</p>`;
    return;
  }

  box.innerHTML = items
    .map((task) => {
      const overdue =
        task.due_at &&
        ["pending", "in_progress"].includes(task.status) &&
        new Date(task.due_at).getTime() < Date.now();
      return `
      <article class="task-item" data-id="${task.id}">
        <div class="task-main">
          <div class="task-title-row">
            <strong>${escapeHtml(task.title)}</strong>
            <span class="badge status-${task.status}">${task.status}</span>
            ${overdue ? `<span class="badge overdue">逾期</span>` : ""}
          </div>
          <div class="task-meta">
            <span>${escapeHtml(task.student_name || "未关联学生")}</span>
            <span>${escapeHtml(task.priority)}</span>
            <span>${escapeHtml(formatDue(task.due_at))}</span>
            <span>${escapeHtml(reminderSummary(task.reminders))}</span>
          </div>
        </div>
        <div class="task-actions">
          ${
            task.status === "pending"
              ? `<button type="button" class="btn tiny" data-action="in_progress">开始</button>`
              : ""
          }
          ${
            ["pending", "in_progress"].includes(task.status)
              ? `<button type="button" class="btn tiny primary" data-action="done">完成</button>
                 <button type="button" class="btn tiny danger" data-action="cancelled">取消</button>`
              : `<button type="button" class="btn tiny" data-action="pending">重新打开</button>`
          }
        </div>
      </article>`;
    })
    .join("");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function parsePreview() {
  const text = $("nl-input").value.trim();
  if (!text) {
    alert("请先输入任务描述");
    return;
  }
  const res = await fetch("/api/tasks/parse", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, auto_create_student: true }),
  });
  if (!res.ok) {
    alert("解析失败：" + (await res.text()));
    return;
  }
  fillPreview(await res.json());
}

async function confirmCreate() {
  const payload = {
    title: $("f-title").value.trim(),
    student_name: $("f-student").value.trim() || null,
    due_at: fromDatetimeLocalValue($("f-due").value),
    priority: $("f-priority").value,
    source_text: (window.__lastParsed && window.__lastParsed.source_text) || $("nl-input").value.trim(),
    parse_confidence: (window.__lastParsed && window.__lastParsed.parse_confidence) || "manual",
    reminder_offsets_minutes: [1440, 120, 0],
    auto_create_student: true,
  };
  if (!payload.title) {
    alert("任务名称不能为空");
    return;
  }
  const res = await fetch("/api/tasks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    alert("创建失败：" + (await res.text()));
    return;
  }
  showResult(await res.json());
  await loadTasks();
}

async function quickCreate() {
  const text = $("nl-input").value.trim();
  if (!text) {
    alert("请先输入任务描述");
    return;
  }
  const res = await fetch("/api/tasks/parse-create", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, auto_create_student: true }),
  });
  if (!res.ok) {
    alert("一键创建失败：" + (await res.text()));
    return;
  }
  const data = await res.json();
  fillPreview(data.parsed);
  showResult(data);
  await loadTasks();
}

async function loadTasks() {
  const params = new URLSearchParams();
  const status = $("filter-status").value;
  const student = $("filter-student").value.trim();
  const q = $("filter-q").value.trim();
  if (status) params.set("status", status);
  if (student) params.set("student_name", student);
  if (q) params.set("q", q);
  if ($("filter-overdue").checked) params.set("overdue", "true");

  const res = await fetch(`/api/tasks?${params.toString()}`);
  if (!res.ok) {
    $("list-meta").textContent = "加载失败";
    return;
  }
  renderTasks(await res.json());
}

async function setStatus(taskId, status) {
  const res = await fetch(`/api/tasks/${taskId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) {
    alert("状态更新失败：" + (await res.text()));
    return;
  }
  showResult(await res.json());
  await loadTasks();
}

$("btn-parse").addEventListener("click", () => parsePreview().catch(console.error));
$("btn-confirm").addEventListener("click", () => confirmCreate().catch(console.error));
$("btn-quick").addEventListener("click", () => quickCreate().catch(console.error));
$("btn-refresh").addEventListener("click", () => loadTasks().catch(console.error));
$("btn-scan").addEventListener("click", () => runScan().catch(console.error));
$("btn-refresh-logs").addEventListener("click", () => loadNotifications().catch(console.error));
$("btn-test-local").addEventListener("click", () => testChannel("local").catch(console.error));
$("btn-test-email").addEventListener("click", () => testChannel("email").catch(console.error));

["filter-status", "filter-student", "filter-q", "filter-overdue"].forEach((id) => {
  $(id).addEventListener("change", () => loadTasks().catch(console.error));
  if ($(id).tagName === "INPUT" && $(id).type === "text") {
    $(id).addEventListener("keydown", (e) => {
      if (e.key === "Enter") loadTasks().catch(console.error);
    });
  }
});

$("task-list").addEventListener("click", (event) => {
  const btn = event.target.closest("button[data-action]");
  if (!btn) return;
  const item = btn.closest(".task-item");
  if (!item) return;
  setStatus(Number(item.dataset.id), btn.dataset.action).catch(console.error);
});

async function loadNotifications() {
  const res = await fetch("/api/notifications?limit=20");
  if (!res.ok) {
    $("notify-meta").textContent = "通知日志加载失败";
    return;
  }
  const data = await res.json();
  $("notify-meta").textContent = `共 ${data.total || 0} 条通知记录`;
  const box = $("notify-list");
  if (!data.items || !data.items.length) {
    box.innerHTML = `<p class="empty">暂无通知。可创建一条即将到期的提醒后点「立即扫描」。</p>`;
    return;
  }
  box.innerHTML = data.items
    .map((log) => {
      const time = log.created_at ? new Date(log.created_at).toLocaleString("zh-CN", { hour12: false }) : "";
      return `
      <article class="notify-item">
        <div class="task-title-row">
          <strong>${escapeHtml(log.title)}</strong>
          <span class="badge status-${log.status === "success" ? "done" : "cancelled"}">${escapeHtml(log.status)}</span>
          <span class="badge">${escapeHtml(log.channel)}</span>
        </div>
        <p class="notify-body">${escapeHtml(log.body)}</p>
        <div class="task-meta"><span>${escapeHtml(time)}</span></div>
      </article>`;
    })
    .join("");
}

async function runScan() {
  const res = await fetch("/api/notifications/run-once", { method: "POST" });
  if (!res.ok) {
    alert("扫描失败：" + (await res.text()));
    return;
  }
  const stats = await res.json();
  showResult(stats);
  await Promise.all([loadTasks(), loadNotifications(), loadChannelStatus()]);
}

async function testChannel(channel) {
  const res = await fetch("/api/notifications/test", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      channel,
      title: `Edu-Agent ${channel} 测试`,
      body: "这是一条来自教务助手的测试通知。",
    }),
  });
  const data = await res.json();
  showResult(data);
  if (!data.ok) {
    alert("测试未完全成功，请查看结果与 .env 配置");
  }
  await Promise.all([loadNotifications(), loadChannelStatus()]);
}

async function loadChannelStatus() {
  try {
    const res = await fetch("/api/notifications/channels");
    if (!res.ok) return;
    const data = await res.json();
    const el = $("channel-status-meta");
    if (!el) return;
    const local = data.local?.enabled ? "local✓" : "local✗";
    const email = data.email?.enabled
      ? `email✓${data.email.dry_run ? "(dry-run)" : ""}`
      : "email✗";
    const wecom = data.wecom?.enabled ? "wecom✓" : "wecom(预留)";
    el.textContent = `通道：${local} / ${email} / ${wecom}｜active=[${(data.active || []).join(", ")}]`;
  } catch (err) {
    console.warn(err);
  }
}

async function loadParserStatus() {
  try {
    const res = await fetch("/api/tasks/parser-status");
    if (!res.ok) return;
    const data = await res.json();
    const el = $("parser-status-meta");
    if (!el) return;
    if (data.openai_configured) {
      el.textContent = `解析引擎：OpenAI（${data.openai_model}），失败时回落规则解析`;
    } else {
      el.textContent = "解析引擎：规则兜底（未配置 OPENAI_API_KEY）";
    }
  } catch (err) {
    console.warn(err);
  }
}

if (!$("nl-input").value) {
  $("nl-input").value = "8月20日下午3点提醒我联系学生王同学确认作品集修改情况";
}

loadParserStatus().catch(console.error);
loadChannelStatus().catch(console.error);
loadTasks().catch(console.error);
loadNotifications().catch(console.error);
