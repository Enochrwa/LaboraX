import { configureStore } from "@reduxjs/toolkit";
import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import authReducer, { type AuthState } from "@/store/authSlice";

function renderWithAuthState(accessToken: string | null) {
  const store = configureStore({
    reducer: { auth: authReducer },
    preloadedState: {
      auth: {
        user: null,
        accessToken,
        refreshToken: null,
        status: accessToken ? "authenticated" : "idle",
        error: null,
      } satisfies AuthState,
    },
  });

  return render(
    <Provider store={store}>
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route path="/login" element={<div>Login page</div>} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
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
});
