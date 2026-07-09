import type { JSX, ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAppSelector } from "@/hooks/useAppStore";

export function ProtectedRoute({ children }: { children: ReactNode }): JSX.Element {
  const accessToken = useAppSelector((state) => state.auth.accessToken);

  if (!accessToken) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
