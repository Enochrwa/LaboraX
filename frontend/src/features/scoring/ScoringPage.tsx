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
  ListItemText,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import type { JSX } from "react";
import { useTranslation } from "react-i18next";
import { Link as RouterLink } from "react-router-dom";

import type { RecentAttempt, TopicMastery } from "@/api/scoringApi";
import { useScoringSummary } from "./useScoringSummary";

function masteryColor(score: number): "success" | "warning" | "error" {
  if (score >= 70) return "success";
  if (score >= 40) return "warning";
  return "error";
}

function TopicMasteryRow({ topic }: { topic: TopicMastery }): JSX.Element {
  const { t } = useTranslation();
  const label = t(`scoring.topics.${topic.topic}`, { defaultValue: topic.topic });

  return (
    <Stack spacing={0.5}>
      <Stack direction="row" justifyContent="space-between" alignItems="baseline">
        <Typography variant="body2" fontWeight={600}>
          {label}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {t("scoring.attemptsCount", { count: topic.attempts_count })}
        </Typography>
      </Stack>
      <Stack direction="row" spacing={2} alignItems="center">
        <LinearProgress
          variant="determinate"
          value={topic.mastery_score}
          color={masteryColor(topic.mastery_score)}
          sx={{ height: 8, borderRadius: 4, flexGrow: 1 }}
        />
        <Chip
          size="small"
          label={t("scoring.masteryValue", { score: Math.round(topic.mastery_score) })}
          color={masteryColor(topic.mastery_score)}
        />
      </Stack>
    </Stack>
  );
}

function RecentAttemptRow({ attempt }: { attempt: RecentAttempt }): JSX.Element {
  const { t } = useTranslation();
  return (
    <ListItem disableGutters divider>
      <ListItemText
        primary={t("scoring.attemptScore", { score: attempt.score })}
        secondary={new Date(attempt.evaluated_at).toLocaleString()}
      />
    </ListItem>
  );
}

export function ScoringPage(): JSX.Element {
  const { t } = useTranslation();
  const { data, isLoading, isError } = useScoringSummary();

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
                {t("scoring.title")}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t("scoring.subtitle")}
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

          {isError && <Alert severity="error">{t("scoring.loadError")}</Alert>}

          {data && (
            <>
              <Stack direction="row" spacing={4}>
                <Box>
                  <Typography variant="overline" color="text.secondary">
                    {t("scoring.overallMastery")}
                  </Typography>
                  <Typography variant="h4" fontWeight={700}>
                    {t("scoring.masteryValue", { score: Math.round(data.overall_mastery) })}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="overline" color="text.secondary">
                    {t("scoring.totalAttempts")}
                  </Typography>
                  <Typography variant="h4" fontWeight={700}>
                    {data.total_attempts}
                  </Typography>
                </Box>
              </Stack>

              <Divider />

              <Stack spacing={1}>
                <Typography variant="subtitle2">{t("scoring.byTopic")}</Typography>
                {data.topics.length === 0 ? (
                  <Typography variant="body2" color="text.secondary">
                    {t("scoring.noTopicsYet")}
                  </Typography>
                ) : (
                  <Stack spacing={2}>
                    {data.topics.map((topic) => (
                      <TopicMasteryRow key={topic.topic} topic={topic} />
                    ))}
                  </Stack>
                )}
              </Stack>

              <Divider />

              <Stack spacing={1}>
                <Typography variant="subtitle2">{t("scoring.recentAttempts")}</Typography>
                {data.recent_attempts.length === 0 ? (
                  <Typography variant="body2" color="text.secondary">
                    {t("scoring.noAttemptsYet")}
                  </Typography>
                ) : (
                  <List dense disablePadding>
                    {data.recent_attempts.map((attempt) => (
                      <RecentAttemptRow key={attempt.id} attempt={attempt} />
                    ))}
                  </List>
                )}
              </Stack>
            </>
          )}
        </Stack>
      </Paper>
    </Box>
  );
}
