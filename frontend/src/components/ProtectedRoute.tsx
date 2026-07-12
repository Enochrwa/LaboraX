import type { JSX, ReactNode } from "react";
import { Navigate } from "react-router-dom";

import type { UserRole } from "@/api/authApi";
import { useAppSelector } from "@/hooks/useAppStore";

export function ProtectedRoute({
  children,
  allowedRoles,
}: {
  children: ReactNode;
  /** When omitted, any authenticated user may view the route. */
  allowedRoles?: UserRole[];
}): JSX.Element {
  const accessToken = useAppSelector((state) => state.auth.accessToken);
  const user = useAppSelector((state) => state.auth.user);

  if (!accessToken) {
    return <Navigate to="/login" replace />;
  }

  // `user` is only populated once `/auth/me` resolves, so a role check is
  // skipped (not denied) until then — `fetchCurrentUser` runs on mount from
  // `DashboardPage`/this route's own page, and a real 403 from the API is
  // still the authoritative guard either way.
  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
