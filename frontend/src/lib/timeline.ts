import { apiFetch } from "./api";

export type TimelineItem = {
  id: string;
  source: "manual" | "session" | "derived" | string;
  event_type: string;
  event_type_label: string;
  title: string;
  event_date: string;
  status: string;
  status_label: string;
  notes: string | null;
  related_session_id: number | null;
  related_course_id: number | null;
  course_name: string | null;
  classroom: string | null;
  teacher_name: string | null;
  editable: boolean;
};

export type TimelineResponse = {
  student_id: number;
  items: TimelineItem[];
  total: number;
  summary: {
    total: number;
    done: number;
    current: number;
    upcoming: number;
    absent: number;
    course_sessions: number;
    manual: number;
  };
};

export type TimelineOptions = {
  event_types: { value: string; label: string }[];
  statuses: { value: string; label: string }[];
};

export type TimelinePayload = {
  event_type: string;
  title: string;
  event_date: string;
  status: string;
  notes?: string | null;
  related_course_id?: number | null;
};

export function fetchTimeline(studentId: number) {
  return apiFetch<TimelineResponse>(`/api/students/${studentId}/timeline`);
}

export function fetchTimelineOptions() {
  return apiFetch<TimelineOptions>("/api/timeline/options");
}

export function createTimelineEvent(studentId: number, payload: TimelinePayload) {
  return apiFetch<TimelineItem>(`/api/students/${studentId}/timeline`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateTimelineEvent(
  eventId: number,
  payload: Partial<TimelinePayload> & { clear_course?: boolean },
) {
  return apiFetch<TimelineItem>(`/api/timeline/events/${eventId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteTimelineEvent(eventId: number) {
  return apiFetch<void>(`/api/timeline/events/${eventId}`, { method: "DELETE" });
}

export function todayDateInput() {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 10);
}
