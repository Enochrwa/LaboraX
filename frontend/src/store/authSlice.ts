import { createAsyncThunk, createSlice, type PayloadAction } from "@reduxjs/toolkit";

import { authApi, type LoginPayload, type RegisterPayload, type User } from "@/api/authApi";
import { tokenStorage } from "@/api/tokenStorage";

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  status: "idle" | "loading" | "authenticated" | "error";
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  accessToken: tokenStorage.getAccessToken(),
  refreshToken: tokenStorage.getRefreshToken(),
  status: "idle",
  error: null,
};

export const login = createAsyncThunk("auth/login", async (payload: LoginPayload) => {
  const tokens = await authApi.login(payload);
  const user = await authApi.me(tokens.access_token);
  return { tokens, user };
});

export const register = createAsyncThunk("auth/register", async (payload: RegisterPayload) => {
  await authApi.register(payload);
  const tokens = await authApi.login({ email: payload.email, password: payload.password });
  const user = await authApi.me(tokens.access_token);
  return { tokens, user };
});

export const fetchCurrentUser = createAsyncThunk(
  "auth/fetchCurrentUser",
  async (_: void, { getState, rejectWithValue }) => {
    const state = getState() as { auth: AuthState };
    const token = state.auth.accessToken;
    if (!token) return rejectWithValue("no token");
    return authApi.me(token);
  },
);

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    logout: (state) => {
      tokenStorage.clear();
      state.user = null;
      state.accessToken = null;
      state.refreshToken = null;
      state.status = "idle";
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    const handlePending = (state: AuthState) => {
      state.status = "loading";
      state.error = null;
    };
    const handleRejected = (state: AuthState, action: { error: { message?: string } }) => {
      state.status = "error";
      state.error = action.error.message ?? "Something went wrong";
    };

    builder
      .addCase(login.pending, handlePending)
      .addCase(login.fulfilled, (state, action) => {
        const { tokens, user } = action.payload;
        tokenStorage.setTokens(tokens.access_token, tokens.refresh_token);
        state.accessToken = tokens.access_token;
        state.refreshToken = tokens.refresh_token;
        state.user = user;
        state.status = "authenticated";
      })
      .addCase(login.rejected, handleRejected)
      .addCase(register.pending, handlePending)
      .addCase(register.fulfilled, (state, action) => {
        const { tokens, user } = action.payload;
        tokenStorage.setTokens(tokens.access_token, tokens.refresh_token);
        state.accessToken = tokens.access_token;
        state.refreshToken = tokens.refresh_token;
        state.user = user;
        state.status = "authenticated";
      })
      .addCase(register.rejected, handleRejected)
      .addCase(fetchCurrentUser.fulfilled, (state, action: PayloadAction<User>) => {
        state.user = action.payload;
        state.status = "authenticated";
      })
      .addCase(fetchCurrentUser.rejected, (state) => {
        tokenStorage.clear();
        state.user = null;
        state.accessToken = null;
        state.refreshToken = null;
        state.status = "idle";
      });
  },
});

export const { logout } = authSlice.actions;
export default authSlice.reducer;
