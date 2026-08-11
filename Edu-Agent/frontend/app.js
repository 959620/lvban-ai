/**
 * Step 4 前端：自然语言解析预览 → 确认创建 / 一键创建
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
  // datetime-local 无时区；按本地时间解释后转 ISO
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return null;
  return d.toISOString();
}

function fillPreview(parsed) {
  $("preview-panel").hidden = false;
  $("f-title").value = parsed.task || "";
  $("f-student").value = parsed.student || "";
  $("f-due").value = toDatetimeLocalValue(parsed.deadline);
  $("f-priority").value = parsed.priority || "medium";
  $("parse-meta").textContent = `置信度：${parsed.parse_confidence || "low"}｜原文：${parsed.source_text || ""}`;
  window.__lastParsed = parsed;
}

function showResult(data) {
  $("result-panel").hidden = false;
  $("result-box").textContent = JSON.stringify(data, null, 2);
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
}

$("btn-parse").addEventListener("click", () => parsePreview().catch(console.error));
$("btn-confirm").addEventListener("click", () => confirmCreate().catch(console.error));
$("btn-quick").addEventListener("click", () => quickCreate().catch(console.error));

// 示例填充，方便演示
if (!$("nl-input").value) {
  $("nl-input").value = "8月20日下午3点提醒我联系学生王同学确认作品集修改情况";
}
