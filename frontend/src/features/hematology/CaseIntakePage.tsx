import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  Grid,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import type { JSX } from "react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link as RouterLink } from "react-router-dom";

import { useNextCase } from "./useNextCase";

const DIFFICULTY_COLOR: Record<string, "success" | "warning" | "error"> = {
  novice: "success",
  intermediate: "warning",
  advanced: "error",
};

export function CaseIntakePage(): JSX.Element {
  const { t } = useTranslation();
  const [requestId, setRequestId] = useState(0);
  const { data: patientCase, isLoading, isError, error, isFetching } = useNextCase({ requestId });

  const handleNewCase = (): void => setRequestId((id) => id + 1);

  return (
    <Box display="flex" justifyContent="center" px={2} py={6}>
      <Paper elevation={2} sx={{ p: 4, width: "100%", maxWidth: 720 }}>
        <Stack spacing={3}>
          <Stack
            direction="row"
            justifyContent="space-between"
            alignItems="center"
            flexWrap="wrap"
            gap={2}
          >
            <Box>
              <Typography variant="h5" component="h1" fontWeight={700}>
                {t("hematology.caseIntake.title")}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t("hematology.caseIntake.subtitle")}
              </Typography>
            </Box>
            <Button component={RouterLink} to="/" variant="text">
              {t("hematology.caseIntake.backToDashboard")}
            </Button>
          </Stack>

          {isLoading && (
            <Box display="flex" justifyContent="center" py={6}>
              <CircularProgress aria-label={t("common.loading")} />
            </Box>
          )}

          {isError && (
            <Alert severity="error">
              {error instanceof Error ? error.message : t("hematology.caseIntake.error")}
            </Alert>
          )}

          {patientCase && (
            <Stack spacing={2}>
              <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                <Typography variant="subtitle1" fontWeight={600}>
                  {patientCase.patient_pseudo_id}
                </Typography>
                <Chip
                  size="small"
                  label={t(`hematology.caseIntake.difficulty.${patientCase.difficulty}`)}
                  color={DIFFICULTY_COLOR[patientCase.difficulty]}
                />
                <Chip
                  size="small"
                  variant="outlined"
                  label={t(`hematology.caseIntake.sex.${patientCase.sex}`)}
                />
                <Chip
                  size="small"
                  variant="outlined"
                  label={t("hematology.caseIntake.age", { age: patientCase.age })}
                />
              </Stack>

              <Divider />

              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  {t("hematology.caseIntake.clinicalHistory")}
                </Typography>
                <Typography variant="body1">{patientCase.clinical_history}</Typography>
              </Box>

              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  {t("hematology.caseIntake.presentingSymptoms")}
                </Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                  {patientCase.doctor_request.presenting_symptoms.map((symptom) => (
                    <Chip key={symptom} label={symptom} size="small" />
                  ))}
                </Stack>
              </Box>

              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  {t("hematology.caseIntake.vitals")}
                </Typography>
                <Grid container spacing={1}>
                  {Object.entries(patientCase.doctor_request.vitals).map(([key, value]) => (
                    <Grid item xs={6} sm={4} key={key}>
                      <Paper variant="outlined" sx={{ p: 1.5, textAlign: "center" }}>
                        <Typography variant="caption" color="text.secondary" display="block">
                          {t(`hematology.caseIntake.vitalLabels.${key}`, { defaultValue: key })}
                        </Typography>
                        <Typography variant="body1" fontWeight={600}>
                          {value}
                        </Typography>
                      </Paper>
                    </Grid>
                  ))}
                </Grid>
              </Box>

              <Button
                variant="contained"
                onClick={handleNewCase}
                disabled={isFetching}
                sx={{ alignSelf: "flex-start" }}
              >
                {t("hematology.caseIntake.newCase")}
              </Button>
            </Stack>
          )}
        </Stack>
      </Paper>
    </Box>
  );
}
