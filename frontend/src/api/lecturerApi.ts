import type { Case, CaseDifficulty } from "./casesApi";
import { apiRequest } from "./client";

export interface CaseAssignment {
  id: string;
  lecturer_id: string;
  assigned_to_group: string;
  due_at: string | null;
  created_at: string;
  case: Case;
}

export interface AssignCasePayload {
  caseId?: string;
  diseaseName?: string;
  difficulty?: CaseDifficulty;
  seed?: number;
  assignedToGroup: string;
  dueAt?: string;
}

export interface CohortCaseBreakdown {
  case_id: string;
  disease_name: string;
  difficulty: CaseDifficulty;
  due_at: string | null;
  attempts_count: number;
  distinct_students: number;
  average_score: number;
}

export interface CohortTopicBreakdown {
  topic: string;
  average_mastery: number;
  students_count: number;
}

export interface CommonlyMissedFinding {
  finding: string;
  miss_count: number;
}

export interface CohortAnalytics {
  group_id: string;
  assignment_count: number;
  case_count: number;
  distinct_students: number;
  total_attempts: number;
  overall_average_score: number;
  cases: CohortCaseBreakdown[];
  topics: CohortTopicBreakdown[];
  commonly_missed_findings: CommonlyMissedFinding[];
  assignments: CaseAssignment[];
}

export const lecturerApi = {
  assignCase: (token: string, payload: AssignCasePayload) =>
    apiRequest<CaseAssignment>("/api/v1/lecturer/cases/assign", {
      method: "POST",
      token,
      body: {
        case_id: payload.caseId,
        disease_name: payload.diseaseName,
        difficulty: payload.difficulty,
        seed: payload.seed,
        assigned_to_group: payload.assignedToGroup,
        due_at: payload.dueAt,
      },
    }),

  myAssignments: (token: string) =>
    apiRequest<CaseAssignment[]>("/api/v1/lecturer/assignments", { token }),

  cohortAnalytics: (token: string, groupId: string) =>
    apiRequest<CohortAnalytics>(`/api/v1/lecturer/analytics/${encodeURIComponent(groupId)}`, {
      token,
    }),
};
