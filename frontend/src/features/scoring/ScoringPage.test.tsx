import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { configureStore } from "@reduxjs/toolkit";
import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { I18nextProvider } from "react-i18next";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { scoringApi, type ScoringSummary } from "@/api/scoringApi";
import { ScoringPage } from "@/features/scoring/ScoringPage";
import authReducer, { type AuthState } from "@/store/authSlice";
import i18n from "@/i18n";

vi.mock("@/api/scoringApi", () => ({
  scoringApi: {
    me: vi.fn(),
  },
}));

const mockedScoringApi = vi.mocked(scoringApi);

const summary: ScoringSummary = {
  topics: [
    {
      topic: "red_cell_indices",
      mastery_score: 82.5,
      attempts_count: 3,
      updated_at: new Date().toISOString(),
    },
    {
      topic: "platelet_count",
      mastery_score: 20,
      attempts_count: 1,
      updated_at: new Date().toISOString(),
    },
  ],
  overall_mastery: 65.4,
  total_attempts: 4,
  recent_attempts: [
    {
      id: "i1",
      case_id: "c1",
      score: 80,
      evaluated_at: new Date().toISOString(),
    },
  ],
};

function renderScoringPage() {
  const store = configureStore({
    reducer: { auth: authReducer },
    preloadedState: {
      auth: {
        user: null,
        accessToken: "test-access-token",
        refreshToken: null,
        status: "authenticated",
        error: null,
      } satisfies AuthState,
    },
  });
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  return render(
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <I18nextProvider i18n={i18n}>
          <MemoryRouter initialEntries={["/progress"]}>
            <ScoringPage />
          </MemoryRouter>
        </I18nextProvider>
      </QueryClientProvider>
    </Provider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("ScoringPage", () => {
  it("renders overall mastery, per-topic mastery, and recent attempts", async () => {
    mockedScoringApi.me.mockResolvedValue(summary);

    renderScoringPage();

    expect(await screen.findByText("65%")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText("Red cell indices")).toBeInTheDocument();
    expect(screen.getByText("Platelet count")).toBeInTheDocument();
    expect(screen.getByText("83%")).toBeInTheDocument();
    expect(screen.getByText("20%")).toBeInTheDocument();
    expect(screen.getByText("Score: 80 / 100")).toBeInTheDocument();
  });

  it("shows empty-state copy for a student with no attempts yet", async () => {
    mockedScoringApi.me.mockResolvedValue({
      topics: [],
      overall_mastery: 0,
      total_attempts: 0,
      recent_attempts: [],
    });

    renderScoringPage();

    expect(
      await screen.findByText("Submit an interpretation to start building your topic mastery."),
    ).toBeInTheDocument();
    expect(screen.getByText("No attempts yet.")).toBeInTheDocument();
  });

  it("shows an error state when the summary fails to load", async () => {
    mockedScoringApi.me.mockRejectedValue(new Error("network error"));

    renderScoringPage();

    expect(
      await screen.findByText("We couldn't load your progress. Please try again."),
    ).toBeInTheDocument();
  });
});
