import type { JSX } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { AppProviders } from "@/app/providers";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { LoginPage } from "@/features/auth/LoginPage";
import { RegisterPage } from "@/features/auth/RegisterPage";
import { CaseIntakePage as ChemistryCaseIntakePage } from "@/features/clinicalChemistry/CaseIntakePage";
import { InterpretationPage as ChemistryInterpretationPage } from "@/features/clinicalChemistry/InterpretationPage";
import { TestOrderingPage as ChemistryTestOrderingPage } from "@/features/clinicalChemistry/TestOrderingPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { CaseIntakePage } from "@/features/hematology/CaseIntakePage";
import { InterpretationPage } from "@/features/hematology/InterpretationPage";
import { TestOrderingPage } from "@/features/hematology/TestOrderingPage";
import { LecturerDashboardPage } from "@/features/lecturerDashboard/LecturerDashboardPage";
import { ScoringPage } from "@/features/scoring/ScoringPage";

function AppRoutes(): JSX.Element {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/progress"
        element={
          <ProtectedRoute>
            <ScoringPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/hematology/case"
        element={
          <ProtectedRoute>
            <CaseIntakePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/hematology/case/:caseId/tests"
        element={
          <ProtectedRoute>
            <TestOrderingPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/hematology/case/:caseId/interpretation"
        element={
          <ProtectedRoute>
            <InterpretationPage />
          </ProtectedRoute>
        }
      />
      {/* Sprint 7 — Clinical Chemistry: same route shape as hematology, own
          feature module (`@/features/clinicalChemistry`), same generic
          case/test/interpretation endpoints filtered to category=chemistry. */}
      <Route
        path="/chemistry/case"
        element={
          <ProtectedRoute>
            <ChemistryCaseIntakePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/chemistry/case/:caseId/tests"
        element={
          <ProtectedRoute>
            <ChemistryTestOrderingPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/chemistry/case/:caseId/interpretation"
        element={
          <ProtectedRoute>
            <ChemistryInterpretationPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/lecturer"
        element={
          <ProtectedRoute allowedRoles={["lecturer", "admin"]}>
            <LecturerDashboardPage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App(): JSX.Element {
  return (
    <AppProviders>
      <AppRoutes />
    </AppProviders>
  );
}
