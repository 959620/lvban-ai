import { apiFetch } from "./api";

export type TaskPriority = "urgent" | "normal" | "low";
export type TaskStatus = "todo" | "done";

export type TaskStudent = {
  id: number;
  name: string;
};

export type TaskItem = {
  id: number;
  owner_id: number;
  title: string;
  student_id: number | null;
  student: TaskStudent | null;
  due_at: string | null;
  priority: TaskPriority;
  status: TaskStatus;
  source: string;
  created_at: string;
  updated_at: string;
};

export type ContactStudent = {
  id: number;
  name: string;
  major: string | null;
  application_stage: string | null;
  next_contact_at: string | null;
  tags: { id: number; name: string; category: string }[];
};

export type DashboardData = {
  today_tasks: TaskItem[];
  contact_students: ContactStudent[];
  upcoming_tasks: TaskItem[];
  incomplete_tasks: TaskItem[];
  stats: {
    today_count: number;
    contact_count: number;
    upcoming_count: number;
    incomplete_count: number;
    todo_total: number;
  };
};

export type TaskPayload = {
  title: string;
  student_id?: number | null;
  due_at?: string | null;
  priority?: TaskPriority;
  status?: TaskStatus;
  source?: string;
};

export const PRIORITY_LABEL: Record<TaskPriority, string> = {
  urgent: "紧急",
  normal: "普通",
  low: "低",
};

export function fetchDashboard(upcomingDays = 3) {
  return apiFetch<DashboardData>(`/api/tasks/dashboard?upcoming_days=${upcomingDays}`);
}

export function createTask(payload: TaskPayload) {
  return apiFetch<TaskItem>("/api/tasks", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function toggleTask(id: number) {
  return apiFetch<TaskItem>(`/api/tasks/${id}/toggle`, { method: "POST" });
}

export function deleteTask(id: number) {
  return apiFetch<void>(`/api/tasks/${id}`, { method: "DELETE" });
}
