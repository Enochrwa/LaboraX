import { configureStore } from "@reduxjs/toolkit";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { I18nextProvider } from "react-i18next";
import { Provider } from "react-redux";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { DiseaseSummary } from "@/api/casesApi";
import { diseasesApi } from "@/api/diseasesApi";
import type { CaseAssignment, CohortAnalytics } from "@/api/lecturerApi";
import { lecturerApi } from "@/api/lecturerApi";
import { LecturerDashboardPage } from "@/features/lecturerDashboard/LecturerDashboardPage";
import i18n from "@/i18n";
import authReducer, { type AuthState } from "@/store/authSlice";

vi.mock("@/api/lecturerApi", () => ({
  lecturerApi: {
    assignCase: vi.fn(),
    myAssignments: vi.fn(),
    cohortAnalytics: vi.fn(),
  },
}));

vi.mock("@/api/diseasesApi", () => ({
  diseasesApi: {
    list: vi.fn(),
  },
}));

const mockedLecturerApi = vi.mocked(lecturerApi);
const mockedDiseasesApi = vi.mocked(diseasesApi);

const diseases: DiseaseSummary[] = [
  { id: "d1", name: "Malaria", category: "hematology" },
  { id: "d2", name: "Iron Deficiency Anemia", category: "hematology" },
];

const sampleCase: CaseAssignment["case"] = {
  id: "case-1",
  patient_pseudo_id: "PT-001",
  age: 30,
  sex: "female",
  clinical_history: "Fever and fatigue.",
  doctor_request: {
    chief_complaint: "Fever",
    duration_days: 3,
    presenting_symptoms: ["fever"],
    vitals: { temp_c: 39 },
  },
  difficulty: "novice",
  seed: 42,
  generated_by: "lecturer",
  created_at: new Date().toISOString(),
  disease: { id: "d1", name: "Malaria", category: "hematology" },
};

const sampleAssignment: CaseAssignment = {
  id: "assignment-1",
  lecturer_id: "lecturer-1",
  assigned_to_group: "BLS-Y3-A",
  due_at: null,
  created_at: new Date().toISOString(),
  case: sampleCase,
};

const sampleAnalytics: CohortAnalytics = {
  group_id: "BLS-Y3-A",
  assignment_count: 1,
  case_count: 1,
  distinct_students: 2,
  total_attempts: 2,
  overall_average_score: 55,
  cases: [
    {
      case_id: "case-1",
      disease_name: "Malaria",
      difficulty: "novice",
      due_at: null,
      attempts_count: 2,
      distinct_students: 2,
      average_score: 55,
    },
  ],
  topics: [{ topic: "red_cell_indices", average_mastery: 60, students_count: 2 }],
  commonly_missed_findings: [{ finding: "Decreased hemoglobin", miss_count: 1 }],
  assignments: [sampleAssignment],
};

function renderPage() {
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
          <MemoryRouter initialEntries={["/lecturer"]}>
            <LecturerDashboardPage />
          </MemoryRouter>
        </I18nextProvider>
      </QueryClientProvider>
    </Provider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  mockedDiseasesApi.list.mockResolvedValue(diseases);
  mockedLecturerApi.myAssignments.mockResolvedValue([]);
  mockedLecturerApi.cohortAnalytics.mockResolvedValue(sampleAnalytics);
});

describe("LecturerDashboardPage", () => {
  it("shows the empty-state copy when the lecturer has no groups yet", async () => {
    renderPage();

    expect(await screen.findByText("You haven't assigned any cases yet.")).toBeInTheDocument();
  });

  it("assigns a case to a group and reports success", async () => {
    const user = userEvent.setup();
    mockedLecturerApi.assignCase.mockResolvedValue(sampleAssignment);

    renderPage();

    await screen.findByText("You haven't assigned any cases yet.");

    await user.click(screen.getByRole("combobox", { name: "Disease" }));
    await user.click(await screen.findByRole("option", { name: "Malaria" }));

    await user.type(screen.getByRole("textbox", { name: "Group" }), "BLS-Y3-A");
    await user.click(screen.getByRole("button", { name: "Assign case" }));

    await waitFor(() => {
      expect(mockedLecturerApi.assignCase).toHaveBeenCalledWith(
        "test-access-token",
        expect.objectContaining({
          diseaseName: "Malaria",
          difficulty: "novice",
          assignedToGroup: "BLS-Y3-A",
        }),
      );
    });

    expect(await screen.findByText("Case assigned to the group.")).toBeInTheDocument();
  });

  it("shows an error when assignment fails", async () => {
    const user = userEvent.setup();
    mockedLecturerApi.assignCase.mockRejectedValue(new Error("boom"));

    renderPage();

    await screen.findByText("You haven't assigned any cases yet.");

    await user.click(screen.getByRole("combobox", { name: "Disease" }));
    await user.click(await screen.findByRole("option", { name: "Malaria" }));
    await user.type(screen.getByRole("textbox", { name: "Group" }), "BLS-Y3-A");
    await user.click(screen.getByRole("button", { name: "Assign case" }));

    expect(
      await screen.findByText("We couldn't assign this case. Please try again."),
    ).toBeInTheDocument();
  });

  it("lists the lecturer's groups and loads cohort analytics on demand", async () => {
    const user = userEvent.setup();
    mockedLecturerApi.myAssignments.mockResolvedValue([sampleAssignment]);
    mockedLecturerApi.cohortAnalytics.mockResolvedValue(sampleAnalytics);

    renderPage();

    expect(await screen.findByText("BLS-Y3-A")).toBeInTheDocument();
    expect(screen.getByText("1 assignment")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "View analytics" }));

    expect(mockedLecturerApi.cohortAnalytics).toHaveBeenCalledWith("test-access-token", "BLS-Y3-A");

    expect(await screen.findByText("Cohort performance — BLS-Y3-A")).toBeInTheDocument();
    expect(screen.getByText("Decreased hemoglobin")).toBeInTheDocument();
    expect(screen.getByText("Missed 1 time")).toBeInTheDocument();
  });

  it("shows an error state when analytics fail to load", async () => {
    const user = userEvent.setup();
    mockedLecturerApi.myAssignments.mockResolvedValue([sampleAssignment]);
    mockedLecturerApi.cohortAnalytics.mockRejectedValue(new Error("boom"));

    renderPage();

    await screen.findByText("BLS-Y3-A");
    await user.click(screen.getByRole("button", { name: "View analytics" }));

    expect(
      await screen.findByText("We couldn't load analytics for this group."),
    ).toBeInTheDocument();
  });

  it("shows an error state when groups fail to load", async () => {
    mockedLecturerApi.myAssignments.mockRejectedValue(new Error("boom"));

    renderPage();

    expect(
      await screen.findByText("We couldn't load your assignments. Please try again."),
    ).toBeInTheDocument();
  });
});
