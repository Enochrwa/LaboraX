import { apiRequest } from "./client";

export interface TopicMastery {
  topic: string;
  mastery_score: number;
  attempts_count: number;
  updated_at: string;
}

export interface RecentAttempt {
  id: string;
  case_id: string;
  score: number;
  evaluated_at: string;
}

export interface ScoringSummary {
  topics: TopicMastery[];
  overall_mastery: number;
  total_attempts: number;
  recent_attempts: RecentAttempt[];
}

export const scoringApi = {
  me: (token: string) => apiRequest<ScoringSummary>("/api/v1/scoring/me", { token }),
};
