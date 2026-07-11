import { apiRequest } from "./client";
import type { DiseaseCategory } from "./casesApi";

export interface TestCatalogEntry {
  id: string;
  code: string;
  name: string;
  category: DiseaseCategory;
  cost_weight: number;
}

export interface TestOrder {
  id: string;
  test: TestCatalogEntry;
  is_appropriate: boolean;
  penalty_applied: number;
  ordered_at: string;
}

export interface TestOrderBatch {
  orders: TestOrder[];
  total_penalty: number;
}

export interface ResultPayload {
  values?: Record<string, number>;
  flags?: Record<string, "low" | "normal" | "high">;
  findings?: string[];
  flag?: "normal" | "abnormal";
}

export interface Result {
  id: string;
  test: TestCatalogEntry;
  result_payload: ResultPayload;
  generated_at: string;
}

export interface CaseResults {
  case_id: string;
  total_penalty: number;
  results: Result[];
}

export const testsApi = {
  catalog: (token: string) => apiRequest<TestCatalogEntry[]>("/api/v1/tests/catalog", { token }),

  order: (token: string, caseId: string, testCodes: string[]) =>
    apiRequest<TestOrderBatch>("/api/v1/tests/order", {
      method: "POST",
      token,
      body: { case_id: caseId, test_codes: testCodes },
    }),

  results: (token: string, caseId: string) =>
    apiRequest<CaseResults>(`/api/v1/results/${caseId}`, { token }),
};
