import { apiFetch } from "./api";

export type Tag = {
  id: number;
  name: string;
  category: string;
};

export type StudentSchool = {
  id?: number;
  school_name: string;
  priority: string | null;
};

export type Student = {
  id: number;
  owner_id: number;
  name: string;
  grade: string | null;
  phone: string | null;
  parent_phone: string | null;
  major: string | null;
  target_country: string | null;
  target_major: string | null;
  intake_year: number | null;
  application_stage: string | null;
  portfolio_started: boolean;
  portfolio_project_count: number;
  portfolio_progress: number;
  personality_notes: string | null;
  family_notes: string | null;
  communication_notes: string | null;
  important_events: string | null;
  next_contact_at: string | null;
  schools: StudentSchool[];
  tags: Tag[];
  created_at: string;
  updated_at: string;
};

export type StudentPayload = {
  name: string;
  grade: string | null;
  phone: string | null;
  parent_phone: string | null;
  major: string | null;
  target_country: string | null;
  target_major: string | null;
  intake_year: number | null;
  application_stage: string | null;
  portfolio_started: boolean;
  portfolio_project_count: number;
  portfolio_progress: number;
  personality_notes: string | null;
  family_notes: string | null;
  communication_notes: string | null;
  important_events: string | null;
  next_contact_at: string | null;
  schools: { school_name: string; priority: string | null }[];
  tag_ids: number[];
};

export type StudentOptions = {
  majors: string[];
  application_stages: string[];
  school_priorities: string[];
  tags: Tag[];
};

export type StudentListResponse = {
  items: Student[];
  total: number;
};

export type StudentListQuery = {
  q?: string;
  major?: string;
  application_stage?: string;
  tag_id?: number;
  intake_year?: number;
};

function toQuery(params: StudentListQuery): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    search.set(key, String(value));
  });
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchStudentOptions() {
  return apiFetch<StudentOptions>("/api/students/options");
}

export function fetchStudents(params: StudentListQuery = {}) {
  return apiFetch<StudentListResponse>(`/api/students${toQuery(params)}`);
}

export function fetchStudent(id: number) {
  return apiFetch<Student>(`/api/students/${id}`);
}

export function createStudent(payload: StudentPayload) {
  return apiFetch<Student>("/api/students", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateStudent(id: number, payload: StudentPayload) {
  return apiFetch<Student>(`/api/students/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteStudent(id: number) {
  return apiFetch<void>(`/api/students/${id}`, { method: "DELETE" });
}
