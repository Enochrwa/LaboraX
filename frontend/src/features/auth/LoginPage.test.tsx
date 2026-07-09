import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Provider } from "react-redux";
import { I18nextProvider } from "react-i18next";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { authApi } from "@/api/authApi";
import { LoginPage } from "@/features/auth/LoginPage";
import i18n from "@/i18n";
import { store } from "@/store";
import { testFixtureCredential } from "@/test-utils/fixtures";

vi.mock("@/api/authApi", () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
    me: vi.fn(),
    refresh: vi.fn(),
  },
}));

const mockedAuthApi = vi.mocked(authApi);

function renderLoginPage() {
  return render(
    <Provider store={store}>
      <I18nextProvider i18n={i18n}>
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      </I18nextProvider>
    </Provider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
});

describe("LoginPage", () => {
  it("shows validation errors when submitted empty", async () => {
    const user = userEvent.setup();
    renderLoginPage();

    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByText("Email is required")).toBeInTheDocument();
    expect(screen.getByText("Password is required")).toBeInTheDocument();
    expect(mockedAuthApi.login).not.toHaveBeenCalled();
  });

  it("submits credentials and calls the auth API", async () => {
    mockedAuthApi.login.mockResolvedValueOnce({
      access_token: "access-token",
      refresh_token: "refresh-token",
      token_type: "bearer",
    });
    mockedAuthApi.me.mockResolvedValueOnce({
      id: "11111111-1111-1111-1111-111111111111",
      email: "student@laborax.dev",
      full_name: "Ada Lovelace",
      role: "student",
      institution: null,
      is_active: true,
      created_at: new Date().toISOString(),
    });

    const user = userEvent.setup();
    const password = testFixtureCredential();
    renderLoginPage();

    await user.type(screen.getByLabelText("Email"), "student@laborax.dev");
    await user.type(screen.getByLabelText("Password"), password);
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(mockedAuthApi.login).toHaveBeenCalledWith({
        email: "student@laborax.dev",
        password,
      });
    });
  });
});
