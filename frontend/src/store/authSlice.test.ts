import { configureStore } from "@reduxjs/toolkit";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { TokenPair, User } from "@/api/authApi";
import { authApi } from "@/api/authApi";
import authReducer, { fetchCurrentUser, login, logout } from "@/store/authSlice";
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

const sampleUser: User = {
  id: "11111111-1111-1111-1111-111111111111",
  email: "student@laborax.dev",
  full_name: "Ada Lovelace",
  role: "student",
  institution: null,
  is_active: true,
  created_at: new Date().toISOString(),
};

const sampleTokens: TokenPair = {
  access_token: "access-token",
  refresh_token: "refresh-token",
  token_type: "bearer",
};

function buildStore() {
  return configureStore({ reducer: { auth: authReducer } });
}

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
});

describe("authSlice", () => {
  it("starts unauthenticated with no tokens", () => {
    const store = buildStore();
    expect(store.getState().auth.accessToken).toBeNull();
    expect(store.getState().auth.status).toBe("idle");
  });

  it("stores tokens and user on successful login", async () => {
    mockedAuthApi.login.mockResolvedValueOnce(sampleTokens);
    mockedAuthApi.me.mockResolvedValueOnce(sampleUser);

    const store = buildStore();
    await store.dispatch(login({ email: sampleUser.email, password: testFixtureCredential() }));

    const state = store.getState().auth;
    expect(state.status).toBe("authenticated");
    expect(state.accessToken).toBe(sampleTokens.access_token);
    expect(state.user?.email).toBe(sampleUser.email);
    expect(localStorage.getItem("laborax.accessToken")).toBe(sampleTokens.access_token);
  });

  it("marks status as error when login fails", async () => {
    mockedAuthApi.login.mockRejectedValueOnce(new Error("Incorrect email or password"));

    const store = buildStore();
    await store.dispatch(login({ email: sampleUser.email, password: "wrong" }));

    expect(store.getState().auth.status).toBe("error");
    expect(store.getState().auth.accessToken).toBeNull();
  });

  it("clears state and storage on logout", async () => {
    mockedAuthApi.login.mockResolvedValueOnce(sampleTokens);
    mockedAuthApi.me.mockResolvedValueOnce(sampleUser);

    const store = buildStore();
    await store.dispatch(login({ email: sampleUser.email, password: testFixtureCredential() }));
    store.dispatch(logout());

    const state = store.getState().auth;
    expect(state.user).toBeNull();
    expect(state.accessToken).toBeNull();
    expect(localStorage.getItem("laborax.accessToken")).toBeNull();
  });

  it("clears state when fetchCurrentUser fails (e.g. expired token)", async () => {
    mockedAuthApi.login.mockResolvedValueOnce(sampleTokens);
    mockedAuthApi.me.mockResolvedValueOnce(sampleUser);
    mockedAuthApi.me.mockRejectedValueOnce(new Error("unauthorized"));

    const store = buildStore();
    await store.dispatch(login({ email: sampleUser.email, password: testFixtureCredential() }));
    await store.dispatch(fetchCurrentUser());

    expect(store.getState().auth.user).toBeNull();
    expect(store.getState().auth.accessToken).toBeNull();
  });
});
