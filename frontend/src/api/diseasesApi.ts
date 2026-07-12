import type { DiseaseSummary } from "./casesApi";
import { apiRequest } from "./client";

export const diseasesApi = {
  list: (token: string) => apiRequest<DiseaseSummary[]>("/api/v1/diseases", { token }),
};
