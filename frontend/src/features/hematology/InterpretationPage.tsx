import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  LinearProgress,
  List,
  ListItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import type { JSX } from "react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link as RouterLink, useParams } from "react-router-dom";

import type { InterpretationResult } from "@/api/interpretationsApi";
import { useInterpretationHistory } from "./useInterpretationHistory";
import { useSubmitInterpretation } from "./useSubmitInterpretation";

function scoreColor(score: number): "success" | "warning" | "error" {
  if (score >= 70) return "success";
  if (score >= 40) return "warning";
  return "error";
}

function InterpretationResultCard({ result }: { result: InterpretationResult }): JSX.Element {
  const { t } = useTranslation();

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Stack spacing={2}>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="subtitle2" fontWeight={600}>
            {t("hematology.interpretation.scoreLabel")}
          </Typography>
          <Chip
            label={t("hematology.interpretation.scoreValue", { score: result.score })}
            color={scoreColor(result.score)}
          />
        </Stack>
        <LinearProgress
          variant="determinate"
          value={result.score}
          color={scoreColor(result.score)}
          sx={{ height: 8, borderRadius: 4 }}
        />

        <Typography variant="body2">{result.tutor_feedback}</Typography>

        {result.confirmed_findings.length > 0 && (
          <Box>
            <Typography variant="subtitle2" color="success.main" gutterBottom>
              {t("hematology.interpretation.confirmed")}
            </Typography>
            <List dense disablePadding>
              {result.confirmed_findings.map((finding) => (
                <ListItem
                  key={finding.expected_finding}
                  disableGutters
                  sx={{ display: "list-item", pl: 2 }}
                >
                  <Typography variant="body2">{finding.expected_finding}</Typography>
                  {finding.explanation && (
                    <Typography variant="caption" color="text.secondary" component="p">
                      {finding.explanation}
                    </Typography>
                  )}
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        {result.missing_findings.length > 0 && (
          <Box>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              {t("hematology.interpretation.missing")}
            </Typography>
            <List dense disablePadding>
              {result.missing_findings.map((finding) => (
                <ListItem
                  key={finding.expected_finding}
                  disableGutters
                  sx={{ display: "list-item", pl: 2 }}
                >
                  <Typography variant="body2">{finding.expected_finding}</Typography>
                  {finding.explanation && (
                    <Typography variant="caption" color="text.secondary" component="p">
                      {finding.explanation}
                    </Typography>
                  )}
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        {result.incorrect_findings.length > 0 && (
          <Box>
            <Typography variant="subtitle2" color="error.main" gutterBottom>
              {t("hematology.interpretation.incorrect")}
            </Typography>
            <List dense disablePadding>
              {result.incorrect_findings.map((incorrect) => (
                <ListItem
                  key={incorrect.statement}
                  disableGutters
                  sx={{ display: "list-item", pl: 2 }}
                >
                  <Typography variant="body2">
                    <strong>{incorrect.statement}</strong> — {incorrect.reason}
                  </Typography>
                </ListItem>
              ))}
            </List>
          </Box>
        )}
      </Stack>
    </Paper>
  );
}

export function InterpretationPage(): JSX.Element {
  const { t } = useTranslation();
  const { caseId } = useParams<{ caseId: string }>();
  const [freeText, setFreeText] = useState("");

  const {
    data: history,
    isLoading: historyLoading,
    isError: historyError,
  } = useInterpretationHistory(caseId ?? "");
  const submitInterpretation = useSubmitInterpretation(caseId ?? "");

  const handleSubmit = (): void => {
    if (!caseId || freeText.trim().length === 0) return;
    submitInterpretation.mutate(freeText, {
      onSuccess: () => setFreeText(""),
    });
  };

  const latestResult = submitInterpretation.data ?? history?.[0];

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
                {t("hematology.interpretation.title")}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t("hematology.interpretation.subtitle")}
              </Typography>
            </Box>
            <Button component={RouterLink} to="/" variant="text">
              {t("hematology.caseIntake.backToDashboard")}
            </Button>
          </Stack>

          <Button
            component={RouterLink}
            to="/progress"
            variant="outlined"
            size="small"
            sx={{ alignSelf: "flex-start" }}
          >
            {t("scoring.viewProgress")}
          </Button>

          {historyLoading && (
            <Box display="flex" justifyContent="center" py={6}>
              <CircularProgress aria-label={t("common.loading")} />
            </Box>
          )}

          {historyError && (
            <Alert severity="error">{t("hematology.interpretation.loadError")}</Alert>
          )}

          {submitInterpretation.isError && (
            <Alert severity="error">
              {submitInterpretation.error instanceof Error
                ? submitInterpretation.error.message
                : t("hematology.interpretation.submitError")}
            </Alert>
          )}

          <Stack spacing={1}>
            <Typography variant="subtitle2">{t("hematology.interpretation.inputLabel")}</Typography>
            <TextField
              value={freeText}
              onChange={(event) => setFreeText(event.target.value)}
              multiline
              minRows={5}
              placeholder={t("hematology.interpretation.inputPlaceholder")}
              disabled={submitInterpretation.isPending}
              inputProps={{ "aria-label": t("hematology.interpretation.inputLabel") }}
            />
            <Button
              variant="contained"
              onClick={handleSubmit}
              disabled={freeText.trim().length === 0 || submitInterpretation.isPending}
              sx={{ alignSelf: "flex-start" }}
            >
              {submitInterpretation.isPending
                ? t("hematology.interpretation.submitting")
                : t("hematology.interpretation.submit")}
            </Button>
          </Stack>

          {latestResult && (
            <>
              <Divider />
              <InterpretationResultCard result={latestResult} />
            </>
          )}

          {history && history.length > 1 && (
            <>
              <Divider />
              <Typography variant="subtitle2">
                {t("hematology.interpretation.previousAttempts", { count: history.length - 1 })}
              </Typography>
              <Stack spacing={2}>
                {history.slice(1).map((attempt) => (
                  <InterpretationResultCard key={attempt.id} result={attempt} />
                ))}
              </Stack>
            </>
          )}
        </Stack>
      </Paper>
    </Box>
  );
}
