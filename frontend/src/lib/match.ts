import { apiFetch } from "./api";

export type MatchResult = {
  id: number;
  student_id: number;
  student: {
    id: number;
    name: string;
    major: string | null;
    application_stage: string | null;
    portfolio_progress: number;
    target_country: string | null;
  } | null;
  score: number;
  rank: number;
  reasons: string[];
  schools: string[];
  tags: string[];
};

export type MatchRun = {
  id: number;
  course_id: number;
  course: {
    id: number;
    name: string;
    course_type: string;
    goal: string | null;
  } | null;
  engine_version: string;
  created_at: string;
  results: MatchResult[];
  total: number;
};

export type ScriptBundle = {
  student_id: number;
  course_id: number;
  engine_version: string;
  wechat_student: string;
  parent: string;
  phone_outline: string;
};

export function fetchMatchStatus() {
  return apiFetch<{ engine: string; ready: boolean; message: string }>("/api/match/status");
}

export function runMatch(courseId: number, minScore = 25) {
  return apiFetch<MatchRun>("/api/match/run", {
    method: "POST",
    body: JSON.stringify({ course_id: courseId, min_score: minScore }),
  });
}

export function generateScripts(courseId: number, studentId: number, matchResultId?: number) {
  return apiFetch<ScriptBundle>("/api/match/scripts", {
    method: "POST",
    body: JSON.stringify({
      course_id: courseId,
      student_id: studentId,
      match_result_id: matchResultId ?? null,
    }),
  });
}

export function createMatchTask(courseId: number, studentId: number) {
  return apiFetch<{ id: number; title: string }>("/api/match/create-task", {
    method: "POST",
    body: JSON.stringify({ course_id: courseId, student_id: studentId }),
  });
}
