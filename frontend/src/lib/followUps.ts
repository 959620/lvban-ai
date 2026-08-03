import { apiFetch } from "./api";

export type ContactWith = "student" | "parent";

export type FollowUpStudent = {
  id: number;
  name: string;
};

export type FollowUp = {
  id: number;
  owner_id: number;
  student_id: number;
  student: FollowUpStudent | null;
  contact_date: string;
  contact_with: ContactWith;
  content: string;
  result: string | null;
  next_action: string | null;
  next_remind_at: string | null;
  created_task_id: number | null;
  created_at: string;
  updated_at: string;
};

export type FollowUpPayload = {
  student_id: number;
  contact_date: string;
  contact_with: ContactWith;
  content: string;
  result?: string | null;
  next_action?: string | null;
  next_remind_at?: string | null;
  create_task?: boolean;
};

export type FollowUpListResponse = {
  items: FollowUp[];
  total: number;
};

export const CONTACT_WITH_LABEL: Record<ContactWith, string> = {
  student: "学生",
  parent: "家长",
};

export function fetchFollowUps(params: { student_id?: number; contact_with?: ContactWith } = {}) {
  const search = new URLSearchParams();
  if (params.student_id) search.set("student_id", String(params.student_id));
  if (params.contact_with) search.set("contact_with", params.contact_with);
  const qs = search.toString();
  return apiFetch<FollowUpListResponse>(`/api/follow-ups${qs ? `?${qs}` : ""}`);
}

export function createFollowUp(payload: FollowUpPayload) {
  return apiFetch<FollowUp>("/api/follow-ups", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteFollowUp(id: number) {
  return apiFetch<void>(`/api/follow-ups/${id}`, { method: "DELETE" });
}
