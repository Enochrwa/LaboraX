import {
  Alert,
  Box,
  Button,
  Link as MuiLink,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import type { JSX } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { Link as RouterLink, useNavigate } from "react-router-dom";

import type { UserRole } from "@/api/authApi";
import { useAppDispatch, useAppSelector } from "@/hooks/useAppStore";
import { register as registerUser } from "@/store/authSlice";

interface RegisterFormValues {
  fullName: string;
  email: string;
  password: string;
  institution: string;
  role: UserRole;
}

export function RegisterPage(): JSX.Element {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const status = useAppSelector((state) => state.auth.status);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    defaultValues: { fullName: "", email: "", password: "", institution: "", role: "student" },
  });

  const onSubmit = handleSubmit(async (values) => {
    const result = await dispatch(
      registerUser({
        email: values.email,
        password: values.password,
        full_name: values.fullName,
        institution: values.institution || undefined,
        role: values.role,
      }),
    );
    if (registerUser.fulfilled.match(result)) {
      navigate("/", { replace: true });
    }
  });

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh" px={2}>
      <Paper component="form" onSubmit={onSubmit} elevation={2} sx={{ p: 4, width: 420 }}>
        <Stack spacing={2}>
          <Typography variant="h5" component="h1" fontWeight={700}>
            {t("auth.register.title")}
          </Typography>

          {status === "error" && <Alert severity="error">{t("auth.register.error")}</Alert>}

          <TextField
            label={t("auth.register.fullName")}
            error={!!errors.fullName}
            helperText={errors.fullName?.message}
            fullWidth
            {...register("fullName", { required: "Full name is required" })}
          />

          <TextField
            label={t("auth.register.email")}
            type="email"
            autoComplete="email"
            error={!!errors.email}
            helperText={errors.email?.message}
            fullWidth
            {...register("email", { required: "Email is required" })}
          />

          <TextField
            label={t("auth.register.password")}
            type="password"
            autoComplete="new-password"
            error={!!errors.password}
            helperText={errors.password?.message}
            fullWidth
            {...register("password", {
              required: "Password is required",
              minLength: { value: 8, message: "Use at least 8 characters" },
            })}
          />

          <TextField
            label={t("auth.register.institution")}
            fullWidth
            {...register("institution")}
          />

          <TextField label={t("auth.register.role")} select fullWidth {...register("role")}>
            <MenuItem value="student">{t("auth.register.roleStudent")}</MenuItem>
            <MenuItem value="lecturer">{t("auth.register.roleLecturer")}</MenuItem>
          </TextField>

          <Button type="submit" variant="contained" size="large" disabled={status === "loading"}>
            {t("auth.register.submit")}
          </Button>

          <Typography variant="body2">
            {t("auth.register.haveAccount")}{" "}
            <MuiLink component={RouterLink} to="/login">
              {t("auth.register.loginLink")}
            </MuiLink>
          </Typography>
        </Stack>
      </Paper>
    </Box>
  );
}
