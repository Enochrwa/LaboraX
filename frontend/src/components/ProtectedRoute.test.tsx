import { configureStore } from "@reduxjs/toolkit";
import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";

import type { User } from "@/api/authApi";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import authReducer, { type AuthState } from "@/store/authSlice";

function renderWithAuthState(
  accessToken: string | null,
  options: { user?: User | null; allowedRoles?: User["role"][] } = {},
) {
  const store = configureStore({
    reducer: { auth: authReducer },
    preloadedState: {
      auth: {
        user: options.user ?? null,
        accessToken,
        refreshToken: null,
        status: accessToken ? "authenticated" : "idle",
        error: null,
      } satisfies AuthState,
    },
  });

  return render(
    <Provider store={store}>
      <MemoryRouter initialEntries={["/lecturer"]}>
        <Routes>
          <Route path="/login" element={<div>Login page</div>} />
          <Route path="/" element={<div>Home page</div>} />
          <Route
            path="/lecturer"
            element={
              <ProtectedRoute allowedRoles={options.allowedRoles}>
                <div>Protected content</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    </Provider>,
  );
}

describe("ProtectedRoute", () => {
  it("redirects to /login when there is no access token", () => {
    renderWithAuthState(null);
    expect(screen.getByText("Login page")).toBeInTheDocument();
  });

  it("renders children when an access token is present", () => {
    renderWithAuthState("some-access-token");
    expect(screen.getByText("Protected content")).toBeInTheDocument();
  });

  it("renders children while the user profile hasn't loaded yet, even with allowedRoles set", () => {
    renderWithAuthState("some-access-token", { user: null, allowedRoles: ["lecturer"] });
    expect(screen.getByText("Protected content")).toBeInTheDocument();
  });

  it("renders children when the user's role is allowed", () => {
    const user: User = {
      id: "u1",
      email: "l@laborax.dev",
      full_name: "L",
      role: "lecturer",
      institution: null,
      is_active: true,
      created_at: new Date().toISOString(),
    };
    renderWithAuthState("some-access-token", { user, allowedRoles: ["lecturer", "admin"] });
    expect(screen.getByText("Protected content")).toBeInTheDocument();
  });

  it("redirects home when the user's role is not allowed", () => {
    const user: User = {
      id: "u1",
      email: "s@laborax.dev",
      full_name: "S",
      role: "student",
      institution: null,
      is_active: true,
      created_at: new Date().toISOString(),
    };
    renderWithAuthState("some-access-token", { user, allowedRoles: ["lecturer", "admin"] });
    expect(screen.getByText("Home page")).toBeInTheDocument();
  });
});
