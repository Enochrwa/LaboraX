import { Box, Button, Paper, Stack, Typography } from "@mui/material";
import type { JSX } from "react";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Link as RouterLink } from "react-router-dom";

import { useAppDispatch, useAppSelector } from "@/hooks/useAppStore";
import { fetchCurrentUser, logout } from "@/store/authSlice";

export function DashboardPage(): JSX.Element {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const user = useAppSelector((state) => state.auth.user);

  useEffect(() => {
    if (!user) {
      void dispatch(fetchCurrentUser());
    }
  }, [dispatch, user]);

  return (
    <Box display="flex" justifyContent="center" px={2} py={8}>
      <Paper elevation={2} sx={{ p: 4, width: 480 }}>
        <Stack spacing={2}>
          <Typography variant="h5" component="h1" fontWeight={700}>
            {t("dashboard.welcome", { name: user?.full_name ?? "" })}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {t("dashboard.subtitle")}
          </Typography>
          {(!user || user.role === "student") && (
            <Button
              component={RouterLink}
              to="/hematology/case"
              variant="contained"
              sx={{ alignSelf: "flex-start" }}
            >
              {t("dashboard.startHematologyCase")}
            </Button>
          )}
          {(!user || user.role === "student") && (
            <Button
              component={RouterLink}
              to="/progress"
              variant="outlined"
              sx={{ alignSelf: "flex-start" }}
            >
              {t("dashboard.viewProgress")}
            </Button>
          )}
          <Button
            variant="outlined"
            onClick={() => dispatch(logout())}
            sx={{ alignSelf: "flex-start" }}
          >
            {t("dashboard.logout")}
          </Button>
        </Stack>
      </Paper>
    </Box>
  );
}
