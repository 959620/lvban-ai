import { apiFetch } from "./api";

export type Course = {
  id: number;
  owner_id: number;
  name: string;
  course_type: string;
  suitable_majors: string[];
  suitable_stages: string[];
  goal: string | null;
  price: string | number | null;
  teacher_name: string | null;
  description: string | null;
  created_at: string;
  updated_at: string;
};

export type CoursePayload = {
  name: string;
  course_type: string;
  suitable_majors: string[];
  suitable_stages: string[];
  goal: string | null;
  price: number | null;
  teacher_name: string | null;
  description: string | null;
};

export type CourseOptions = {
  course_types: string[];
  majors: string[];
  suitable_stages: string[];
};

export type CourseListResponse = {
  items: Course[];
  total: number;
};

export type CourseListQuery = {
  q?: string;
  course_type?: string;
  major?: string;
  stage?: string;
};

function toQuery(params: CourseListQuery): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    search.set(key, String(value));
  });
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export function fetchCourseOptions() {
  return apiFetch<CourseOptions>("/api/courses/options");
}

export function fetchCourses(params: CourseListQuery = {}) {
  return apiFetch<CourseListResponse>(`/api/courses${toQuery(params)}`);
}

export function fetchCourse(id: number) {
  return apiFetch<Course>(`/api/courses/${id}`);
}

export function createCourse(payload: CoursePayload) {
  return apiFetch<Course>("/api/courses", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateCourse(id: number, payload: CoursePayload) {
  return apiFetch<Course>(`/api/courses/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteCourse(id: number) {
  return apiFetch<void>(`/api/courses/${id}`, { method: "DELETE" });
}

export function formatPrice(price: string | number | null) {
  if (price === null || price === undefined || price === "") return "未定价";
  const num = typeof price === "number" ? price : Number(price);
  if (Number.isNaN(num)) return String(price);
  return `¥${num.toLocaleString("zh-CN", { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;
}
