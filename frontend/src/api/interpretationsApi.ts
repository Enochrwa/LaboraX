import { apiRequest } from "./client";

export interface FindingMatch {
  expected_finding: string;
  matched_statement: string | null;
  similarity: number;
}

export interface IncorrectStatement {
  statement: string;
  reason: string;
}

export interface InterpretationResult {
  id: string;
  case_id: string;
  submitted_text: string;
  score: number;
  confirmed_findings: FindingMatch[];
  missing_findings: FindingMatch[];
  incorrect_findings: IncorrectStatement[];
  tutor_feedback: string;
  evaluated_at: string;
}

export const interpretationsApi = {
  submit: (token: string, caseId: string, freeText: string) =>
    apiRequest<InterpretationResult>("/api/v1/interpretations", {
      method: "POST",
      token,
      body: { case_id: caseId, free_text: freeText },
    }),

  history: (token: string, caseId: string) =>
    apiRequest<InterpretationResult[]>(`/api/v1/interpretations/${caseId}`, { token }),
};
