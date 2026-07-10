import { apiRequest } from "./client";

export type DiseaseCategory = "hematology" | "chemistry" | "microbiology" | "parasitology";
export type CaseDifficulty = "novice" | "intermediate" | "advanced";

export interface DiseaseSummary {
  id: string;
  name: string;
  category: DiseaseCategory;
}

export interface CaseVitals {
  [key: string]: number;
}

export interface DoctorRequest {
  chief_complaint: string;
  duration_days: number;
  presenting_symptoms: string[];
  vitals: CaseVitals;
}

export interface Case {
  id: string;
  patient_pseudo_id: string;
  age: number;
  sex: "male" | "female";
  clinical_history: string;
  doctor_request: DoctorRequest;
  difficulty: CaseDifficulty;
  seed: number;
  generated_by: "system" | "lecturer";
  created_at: string;
  disease: DiseaseSummary;
}

export interface NextCaseParams {
  category?: string;
  diseaseName?: string;
  difficulty?: CaseDifficulty;
  seed?: number;
}

export const casesApi = {
  next: (token: string, params: NextCaseParams = {}) =>
    apiRequest<Case>("/api/v1/cases/next", {
      token,
      params: {
        category: params.category,
        disease_name: params.diseaseName,
        difficulty: params.difficulty,
        seed: params.seed,
      },
    }),

  get: (token: string, caseId: string) => apiRequest<Case>(`/api/v1/cases/${caseId}`, { token }),
};
