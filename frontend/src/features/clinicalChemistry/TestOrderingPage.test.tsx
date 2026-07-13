import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { configureStore } from "@reduxjs/toolkit";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Provider } from "react-redux";
import { I18nextProvider } from "react-i18next";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  testsApi,
  type CaseResults,
  type TestCatalogEntry,
  type TestOrderBatch,
} from "@/api/testsApi";
import { TestOrderingPage } from "@/features/clinicalChemistry/TestOrderingPage";
import authReducer, { type AuthState } from "@/store/authSlice";
import i18n from "@/i18n";

vi.mock("@/api/testsApi", () => ({
  testsApi: {
    catalog: vi.fn(),
    order: vi.fn(),
    results: vi.fn(),
  },
}));

const mockedTestsApi = vi.mocked(testsApi);

const CASE_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc";

const sampleCatalog: TestCatalogEntry[] = [
  {
    id: "t1",
    code: "CBC",
    name: "Complete Blood Count",
    category: "hematology",
    cost_weight: 1.0,
  },
  {
    id: "t2",
    code: "LFT",
    name: "Liver Function Test",
    category: "chemistry",
    cost_weight: 2.0,
  },
];

const emptyResults: CaseResults = {
  case_id: CASE_ID,
  total_penalty: 0,
  results: [],
};

const orderBatch: TestOrderBatch = {
  total_penalty: 0,
  orders: [
    {
      id: "o1",
      test: sampleCatalog[0],
      is_appropriate: true,
      penalty_applied: 0,
      ordered_at: new Date().toISOString(),
    },
  ],
};

const resultsAfterOrder: CaseResults = {
  case_id: CASE_ID,
  total_penalty: 0,
  results: [
    {
      id: "r1",
      test: sampleCatalog[0],
      result_payload: {
        values: { hemoglobin_g_dl: 10.2 },
        flags: { hemoglobin_g_dl: "low" },
      },
      generated_at: new Date().toISOString(),
    },
  ],
};

function renderTestOrderingPage() {
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
          <MemoryRouter initialEntries={[`/chemistry/case/${CASE_ID}/tests`]}>
            <Routes>
              <Route path="/chemistry/case/:caseId/tests" element={<TestOrderingPage />} />
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

describe("TestOrderingPage", () => {
  it("renders the test catalog as a checklist", async () => {
    mockedTestsApi.catalog.mockResolvedValueOnce(sampleCatalog);
    mockedTestsApi.results.mockResolvedValueOnce(emptyResults);

    renderTestOrderingPage();

    expect(await screen.findByText("Complete Blood Count")).toBeInTheDocument();
    expect(screen.getByText("Liver Function Test")).toBeInTheDocument();
    expect(
      screen.getByText("No results yet — order a test to see its results here."),
    ).toBeInTheDocument();
  });

  it("orders selected tests and refreshes results", async () => {
    mockedTestsApi.catalog.mockResolvedValueOnce(sampleCatalog);
    mockedTestsApi.results.mockResolvedValueOnce(emptyResults);
    mockedTestsApi.order.mockResolvedValueOnce(orderBatch);
    mockedTestsApi.results.mockResolvedValueOnce(resultsAfterOrder);

    const user = userEvent.setup();
    renderTestOrderingPage();

    await screen.findByText("Complete Blood Count");
    await user.click(screen.getByRole("checkbox", { name: "Complete Blood Count" }));
    await user.click(screen.getByRole("button", { name: "Order selected tests" }));

    await waitFor(() => {
      expect(mockedTestsApi.order).toHaveBeenCalledWith("test-access-token", CASE_ID, ["CBC"]);
    });

    expect(await screen.findByText("10.2")).toBeInTheDocument();
  });

  it("shows an error message when loading fails", async () => {
    mockedTestsApi.catalog.mockRejectedValueOnce(new Error("boom"));
    mockedTestsApi.results.mockResolvedValueOnce(emptyResults);

    renderTestOrderingPage();

    expect(
      await screen.findByText("We couldn't load the test catalog or results. Please try again."),
    ).toBeInTheDocument();
  });
});
