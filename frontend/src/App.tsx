import type { JSX } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { AppProviders } from "@/app/providers";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { LoginPage } from "@/features/auth/LoginPage";
import { RegisterPage } from "@/features/auth/RegisterPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { CaseIntakePage } from "@/features/hematology/CaseIntakePage";
import { TestOrderingPage } from "@/features/hematology/TestOrderingPage";

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
