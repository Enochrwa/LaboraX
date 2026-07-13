import {
  Box,
  Button,
  Card,
  CardActionArea,
  CardContent,
  Chip,
  Container,
  Stack,
  Typography,
} from "@mui/material";
import type { JSX, ReactNode } from "react";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Link as RouterLink } from "react-router-dom";

import { useAppDispatch, useAppSelector } from "@/hooks/useAppStore";
import { fetchCurrentUser, logout } from "@/store/authSlice";

interface ModuleCardProps {
  title: string;
  description: string;
  to: string;
  glyph: ReactNode;
  comingSoon?: boolean;
}

/**
 * A single module-launcher tile. Deliberately its own component (rather than
 * inlined per-module JSX) so that adding a future department — Microbiology,
 * Parasitology, etc. per `docs/SPRINT_PLAN.md` Phase 2/3 — is a one-entry
 * addition to the module list in `DashboardPage` below, not a copy-pasted
 * block. `glyph` is a plain text/emoji marker rather than an icon-font
 * dependency, keeping the module's bundle footprint unchanged.
 */
function ModuleCard({ title, description, to, glyph, comingSoon }: ModuleCardProps): JSX.Element {
  const { t } = useTranslation();

  const body = (
    <CardContent sx={{ p: 0, width: "100%" }}>
      <Stack direction="row" alignItems="center" justifyContent="space-between" mb={1.5}>
        <Box
          sx={{
            width: 40,
            height: 40,
            borderRadius: 2,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            bgcolor: "primary.main",
            color: "primary.contrastText",
            fontSize: 20,
          }}
          aria-hidden
        >
          {glyph}
        </Box>
        {comingSoon && <Chip size="small" label={t("dashboard.comingSoon")} />}
      </Stack>
      <Typography variant="h6" component="h2" fontWeight={700} gutterBottom>
        {title}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {description}
      </Typography>
    </CardContent>
  );

  return (
    <Card
      elevation={1}
      sx={{
        height: "100%",
        opacity: comingSoon ? 0.6 : 1,
        transition: "transform 150ms ease, box-shadow 150ms ease",
        "&:hover": comingSoon ? undefined : { transform: "translateY(-2px)", boxShadow: 4 },
      }}
    >
      {comingSoon ? (
        <Box sx={{ p: 3 }}>{body}</Box>
      ) : (
        <CardActionArea
          component={RouterLink}
          to={to}
          sx={{
            height: "100%",
            p: 3,
            display: "flex",
            flexDirection: "column",
            alignItems: "flex-start",
          }}
        >
          {body}
        </CardActionArea>
      )}
    </Card>
  );
}

export function DashboardPage(): JSX.Element {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const user = useAppSelector((state) => state.auth.user);

  useEffect(() => {
    if (!user) {
      void dispatch(fetchCurrentUser());
    }
  }, [dispatch, user]);

  const isStudent = !user || user.role === "student";
  const isStaff = user && (user.role === "lecturer" || user.role === "admin");

  return (
    <Container maxWidth="lg" sx={{ py: { xs: 4, sm: 6, md: 8 } }}>
      <Stack spacing={{ xs: 3, sm: 4 }}>
        <Stack
          direction={{ xs: "column", sm: "row" }}
          justifyContent="space-between"
          alignItems={{ xs: "flex-start", sm: "center" }}
          spacing={2}
        >
          <Box>
            <Typography variant="h4" component="h1" fontWeight={700}>
              {t("dashboard.welcome", { name: user?.full_name ?? "" })}
            </Typography>
            <Typography variant="body1" color="text.secondary" mt={0.5}>
              {t("dashboard.subtitle")}
            </Typography>
          </Box>
          <Button variant="outlined" onClick={() => dispatch(logout())}>
            {t("dashboard.logout")}
          </Button>
        </Stack>

        {isStudent && (
          <Box>
            <Typography variant="overline" color="text.secondary" fontWeight={600}>
              {t("dashboard.practiceModulesHeading")}
            </Typography>
            <Box
              display="grid"
              gridTemplateColumns={{ xs: "1fr", sm: "repeat(2, 1fr)", lg: "repeat(3, 1fr)" }}
              gap={2.5}
              mt={1}
            >
              <ModuleCard
                title={t("dashboard.hematologyModule.title")}
                description={t("dashboard.hematologyModule.description")}
                to="/hematology/case"
                glyph="🩸"
              />
              <ModuleCard
                title={t("dashboard.chemistryModule.title")}
                description={t("dashboard.chemistryModule.description")}
                to="/chemistry/case"
                glyph="🧪"
              />
              <ModuleCard
                title={t("dashboard.microbiologyModule.title")}
                description={t("dashboard.microbiologyModule.description")}
                to="/microbiology/case"
                glyph="🔬"
                comingSoon
              />
            </Box>
          </Box>
        )}

        <Box>
          <Typography variant="overline" color="text.secondary" fontWeight={600}>
            {t("dashboard.moreHeading")}
          </Typography>
          <Box
            display="grid"
            gridTemplateColumns={{ xs: "1fr", sm: "repeat(2, 1fr)", lg: "repeat(3, 1fr)" }}
            gap={2.5}
            mt={1}
          >
            {isStudent && (
              <ModuleCard
                title={t("dashboard.progressModule.title")}
                description={t("dashboard.progressModule.description")}
                to="/progress"
                glyph="📈"
              />
            )}
            {isStaff && (
              <ModuleCard
                title={t("dashboard.lecturerModule.title")}
                description={t("dashboard.lecturerModule.description")}
                to="/lecturer"
                glyph="🎓"
              />
            )}
          </Box>
        </Box>
      </Stack>
    </Container>
  );
}
