import { apiFetch } from "./api";

export type SessionStatus = "scheduled" | "completed" | "cancelled" | "absent";

export type ClassSession = {
  id: number;
  owner_id: number;
  student_id: number;
  student: { id: number; name: string } | null;
  course_id: number | null;
  course: { id: number; name: string } | null;
  session_date: string;
  start_time: string;
  end_time: string;
  classroom: string | null;
  teacher_name: string | null;
  session_type: string;
  status: SessionStatus;
  notes: string | null;
  classroom_conflict: boolean;
};

export type ScheduleDayResponse = {
  items: ClassSession[];
  total: number;
  query_date: string | null;
  occupied_classrooms: string[];
  absent_count: number;
};

export type ScheduleOptions = {
  session_types: string[];
  statuses: { value: string; label: string }[];
};

export type SessionPayload = {
  student_id: number;
  course_id?: number | null;
  session_date: string;
  start_time: string;
  end_time: string;
  classroom?: string | null;
  teacher_name?: string | null;
  session_type: string;
  status?: SessionStatus;
  notes?: string | null;
};

export const STATUS_LABEL: Record<SessionStatus, string> = {
  scheduled: "已安排",
  completed: "已完成",
  cancelled: "已取消",
  absent: "缺课",
};

export function fetchScheduleOptions() {
  return apiFetch<ScheduleOptions>("/api/schedule/options");
}

export function fetchScheduleDay(day?: string) {
  const qs = day ? `?day=${day}` : "";
  return apiFetch<ScheduleDayResponse>(`/api/schedule/day${qs}`);
}

export function fetchScheduleWeek(start?: string) {
  const qs = start ? `?start=${start}` : "";
  return apiFetch<ScheduleDayResponse>(`/api/schedule/week${qs}`);
}

export function createSession(payload: SessionPayload) {
  return apiFetch<ClassSession>("/api/schedule", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateSessionStatus(id: number, status: SessionStatus) {
  return apiFetch<ClassSession>(`/api/schedule/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export function markAbsent(id: number) {
  return apiFetch<ClassSession>(`/api/schedule/${id}/absent`, { method: "POST" });
}

export function markComplete(id: number) {
  return apiFetch<ClassSession>(`/api/schedule/${id}/complete`, { method: "POST" });
}

export function deleteSession(id: number) {
  return apiFetch<void>(`/api/schedule/${id}`, { method: "DELETE" });
}

export function todayDateInput() {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 10);
}
