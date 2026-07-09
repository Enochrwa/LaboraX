import {
  Alert,
  Box,
  Button,
  Link as MuiLink,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import type { JSX } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { Link as RouterLink, useNavigate } from "react-router-dom";

import { useAppDispatch, useAppSelector } from "@/hooks/useAppStore";
import { login } from "@/store/authSlice";

interface LoginFormValues {
  email: string;
  password: string;
}

export function LoginPage(): JSX.Element {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const status = useAppSelector((state) => state.auth.status);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({ defaultValues: { email: "", password: "" } });

  const onSubmit = handleSubmit(async (values) => {
    const result = await dispatch(login(values));
    if (login.fulfilled.match(result)) {
      navigate("/", { replace: true });
    }
  });

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh" px={2}>
      <Paper component="form" onSubmit={onSubmit} elevation={2} sx={{ p: 4, width: 400 }}>
        <Stack spacing={2}>
          <Typography variant="h5" component="h1" fontWeight={700}>
            {t("auth.login.title")}
          </Typography>

          {status === "error" && <Alert severity="error">{t("auth.login.error")}</Alert>}

          <TextField
            label={t("auth.login.email")}
            type="email"
            autoComplete="email"
            error={!!errors.email}
            helperText={errors.email?.message}
            fullWidth
            {...register("email", { required: "Email is required" })}
          />

          <TextField
            label={t("auth.login.password")}
            type="password"
            autoComplete="current-password"
            error={!!errors.password}
            helperText={errors.password?.message}
            fullWidth
            {...register("password", { required: "Password is required" })}
          />

          <Button type="submit" variant="contained" size="large" disabled={status === "loading"}>
            {t("auth.login.submit")}
          </Button>

          <Typography variant="body2">
            {t("auth.login.noAccount")}{" "}
            <MuiLink component={RouterLink} to="/register">
              {t("auth.login.registerLink")}
            </MuiLink>
          </Typography>
        </Stack>
      </Paper>
    </Box>
  );
}
