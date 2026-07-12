import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { configureStore } from "@reduxjs/toolkit";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Provider } from "react-redux";
import { I18nextProvider } from "react-i18next";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { interpretationsApi, type InterpretationResult } from "@/api/interpretationsApi";
import { InterpretationPage } from "@/features/hematology/InterpretationPage";
import authReducer, { type AuthState } from "@/store/authSlice";
import i18n from "@/i18n";

vi.mock("@/api/interpretationsApi", () => ({
  interpretationsApi: {
    submit: vi.fn(),
    history: vi.fn(),
  },
}));

const mockedInterpretationsApi = vi.mocked(interpretationsApi);

const CASE_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc";

const strongResult: InterpretationResult = {
  id: "i1",
  case_id: CASE_ID,
  submitted_text: "Hemoglobin is decreased.",
  score: 80,
  confirmed_findings: [
    {
      expected_finding: "Hemoglobin is decreased",
      matched_statement: "Hemoglobin is decreased.",
      similarity: 0.9,
    },
  ],
  missing_findings: [],
  incorrect_findings: [],
  tutor_feedback: "Strong interpretation.",
  evaluated_at: new Date().toISOString(),
};

const weakResult: InterpretationResult = {
  id: "i2",
  case_id: CASE_ID,
  submitted_text: "Platelets are increased.",
  score: 10,
  confirmed_findings: [],
  missing_findings: [
    { expected_finding: "Hemoglobin is decreased", matched_statement: null, similarity: 0.1 },
  ],
  incorrect_findings: [
    { statement: "Platelets are increased.", reason: "Expected platelets to be decreased." },
  ],
  tutor_feedback: "This interpretation is missing most of the expected findings.",
  evaluated_at: new Date().toISOString(),
};

function renderInterpretationPage() {
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
          <MemoryRouter initialEntries={[`/hematology/case/${CASE_ID}/interpretation`]}>
            <Routes>
              <Route
                path="/hematology/case/:caseId/interpretation"
                element={<InterpretationPage />}
              />
            </Routes>
          </MemoryRouter>
        </I18nextProvider>
      </QueryClientProvider>
    </Provider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("InterpretationPage", () => {
  it("submits free text and displays the score and feedback", async () => {
    mockedInterpretationsApi.history.mockResolvedValue([]);
    mockedInterpretationsApi.submit.mockResolvedValueOnce(strongResult);

    const user = userEvent.setup();
    renderInterpretationPage();

    const input = await screen.findByLabelText("Your interpretation");
    await user.type(input, "Hemoglobin is decreased.");
    await user.click(screen.getByRole("button", { name: "Submit interpretation" }));

    await waitFor(() => {
      expect(mockedInterpretationsApi.submit).toHaveBeenCalledWith(
        "test-access-token",
        CASE_ID,
        "Hemoglobin is decreased.",
      );
    });

    expect(await screen.findByText("80 / 100")).toBeInTheDocument();
    expect(screen.getByText("Strong interpretation.")).toBeInTheDocument();
  });

  it("shows missing and incorrect findings for a weak submission", async () => {
    mockedInterpretationsApi.history.mockResolvedValue([]);
    mockedInterpretationsApi.submit.mockResolvedValueOnce(weakResult);

    const user = userEvent.setup();
    renderInterpretationPage();

    const input = await screen.findByLabelText("Your interpretation");
    await user.type(input, "Platelets are increased.");
    await user.click(screen.getByRole("button", { name: "Submit interpretation" }));

    expect(await screen.findByText("10 / 100")).toBeInTheDocument();
    expect(screen.getByText("Hemoglobin is decreased")).toBeInTheDocument();
    expect(screen.getByText("Platelets are increased.")).toBeInTheDocument();
    expect(screen.getByText(/Expected platelets to be decreased\./)).toBeInTheDocument();
  });

  it("disables submit while the text box is empty", async () => {
    mockedInterpretationsApi.history.mockResolvedValue([]);

    renderInterpretationPage();

    await screen.findByLabelText("Your interpretation");
    expect(screen.getByRole("button", { name: "Submit interpretation" })).toBeDisabled();
  });

  it("shows an error message when loading history fails", async () => {
    mockedInterpretationsApi.history.mockRejectedValueOnce(new Error("boom"));

    renderInterpretationPage();

    expect(
      await screen.findByText("We couldn't load your interpretation history. Please try again."),
    ).toBeInTheDocument();
  });

  it("renders previous attempts from history", async () => {
    mockedInterpretationsApi.history.mockResolvedValueOnce([weakResult, strongResult]);

    renderInterpretationPage();

    expect(await screen.findByText("10 / 100")).toBeInTheDocument();
    expect(screen.getByText("Previous attempts (1)")).toBeInTheDocument();
    expect(screen.getByText("80 / 100")).toBeInTheDocument();
  });
});
