import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { configureStore } from "@reduxjs/toolkit";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Provider } from "react-redux";
import { I18nextProvider } from "react-i18next";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { casesApi, type Case } from "@/api/casesApi";
import { CaseIntakePage } from "@/features/clinicalChemistry/CaseIntakePage";
import authReducer, { type AuthState } from "@/store/authSlice";
import i18n from "@/i18n";

vi.mock("@/api/casesApi", () => ({
  casesApi: {
    next: vi.fn(),
    get: vi.fn(),
  },
}));

const mockedCasesApi = vi.mocked(casesApi);

const sampleCase: Case = {
  id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  patient_pseudo_id: "PT-482913",
  age: 34,
  sex: "female",
  clinical_history: "A 34-year-old female patient presents with yellowing of the eyes.",
  doctor_request: {
    chief_complaint: "yellowing of the eyes and dark urine for 5 days",
    duration_days: 5,
    presenting_symptoms: ["jaundice", "right upper quadrant pain", "fatigue"],
    vitals: { temperature_c: 37.6, heart_rate_bpm: 92 },
  },
  difficulty: "novice",
  seed: 555,
  generated_by: "system",
  created_at: new Date().toISOString(),
  disease: {
    id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
    name: "Acute Viral Hepatitis",
    category: "chemistry",
  },
};

function renderCaseIntakePage() {
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
          <MemoryRouter>
            <CaseIntakePage />
          </MemoryRouter>
        </I18nextProvider>
      </QueryClientProvider>
    </Provider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("CaseIntakePage", () => {
  it("renders the generated case once loaded", async () => {
    mockedCasesApi.next.mockResolvedValueOnce(sampleCase);
    renderCaseIntakePage();

    expect(await screen.findByText("PT-482913")).toBeInTheDocument();
    expect(screen.getByText(sampleCase.clinical_history)).toBeInTheDocument();
    expect(screen.getByText("jaundice")).toBeInTheDocument();
    expect(screen.getByText("fatigue")).toBeInTheDocument();
  });

  it("shows an error message when case generation fails", async () => {
    mockedCasesApi.next.mockRejectedValueOnce(new Error("boom"));
    renderCaseIntakePage();

    expect(await screen.findByText("boom")).toBeInTheDocument();
  });

  it("requests a new case when the button is clicked", async () => {
    mockedCasesApi.next.mockResolvedValue(sampleCase);
    const user = userEvent.setup();
    renderCaseIntakePage();

    await screen.findByText("PT-482913");
    await user.click(screen.getByRole("button", { name: "Get a new case" }));

    await waitFor(() => {
      expect(mockedCasesApi.next).toHaveBeenCalledTimes(2);
    });
  });
});
