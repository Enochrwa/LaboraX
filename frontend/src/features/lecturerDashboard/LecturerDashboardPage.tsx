import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  Grid,
  List,
  ListItem,
  ListItemText,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import type { FormEvent, JSX } from "react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link as RouterLink } from "react-router-dom";

import type { CaseDifficulty } from "@/api/casesApi";
import { ApiError } from "@/api/client";
import { useAssignCase, useCohortAnalytics, useMyAssignments } from "./useLecturerDashboard";
import { useDiseases } from "./useDiseases";

const DIFFICULTIES: CaseDifficulty[] = ["novice", "intermediate", "advanced"];

function masteryColor(score: number): "success" | "warning" | "error" {
  if (score >= 70) return "success";
  if (score >= 40) return "warning";
  return "error";
}

function AssignCaseForm({ onAssigned }: { onAssigned: (groupId: string) => void }): JSX.Element {
  const { t } = useTranslation();
  const { data: diseases } = useDiseases();
  const assignCase = useAssignCase();

  const [diseaseName, setDiseaseName] = useState("");
  const [difficulty, setDifficulty] = useState<CaseDifficulty>("novice");
  const [seed, setSeed] = useState("");
  const [assignedToGroup, setAssignedToGroup] = useState("");
  const [dueAt, setDueAt] = useState("");

  const canSubmit = diseaseName.trim().length > 0 && assignedToGroup.trim().length > 0;

  const handleSubmit = (event: FormEvent): void => {
    event.preventDefault();
    if (!canSubmit) return;

    assignCase.mutate(
      {
        diseaseName,
        difficulty,
        seed: seed.trim() === "" ? undefined : Number(seed),
        assignedToGroup: assignedToGroup.trim(),
        dueAt: dueAt === "" ? undefined : new Date(dueAt).toISOString(),
      },
      {
        onSuccess: (assignment) => {
          setAssignedToGroup("");
          setSeed("");
          setDueAt("");
          onAssigned(assignment.assigned_to_group);
        },
      },
    );
  };

  return (
    <Paper elevation={2} sx={{ p: 4 }}>
      <Stack spacing={3} component="form" onSubmit={handleSubmit}>
        <Typography variant="h6" fontWeight={700}>
          {t("lecturerDashboard.assignForm.title")}
        </Typography>

        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <TextField
              select
              fullWidth
              required
              label={t("lecturerDashboard.assignForm.disease")}
              value={diseaseName}
              onChange={(event) => setDiseaseName(event.target.value)}
            >
              {(diseases ?? []).map((disease) => (
                <MenuItem key={disease.id} value={disease.name}>
                  {disease.name}
                </MenuItem>
              ))}
            </TextField>
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              select
              fullWidth
              label={t("lecturerDashboard.assignForm.difficulty")}
              value={difficulty}
              onChange={(event) => setDifficulty(event.target.value as CaseDifficulty)}
            >
              {DIFFICULTIES.map((level) => (
                <MenuItem key={level} value={level}>
                  {t(`hematology.caseIntake.difficulty.${level}`)}
                </MenuItem>
              ))}
            </TextField>
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              required
              label={t("lecturerDashboard.assignForm.group")}
              placeholder={t("lecturerDashboard.assignForm.groupPlaceholder")}
              value={assignedToGroup}
              onChange={(event) => setAssignedToGroup(event.target.value)}
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              type="number"
              label={t("lecturerDashboard.assignForm.seed")}
              helperText={t("lecturerDashboard.assignForm.seedHelp")}
              value={seed}
              onChange={(event) => setSeed(event.target.value)}
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              type="datetime-local"
              label={t("lecturerDashboard.assignForm.dueAt")}
              InputLabelProps={{ shrink: true }}
              value={dueAt}
              onChange={(event) => setDueAt(event.target.value)}
            />
          </Grid>
        </Grid>

        {assignCase.isError && (
          <Alert severity="error">
            {assignCase.error instanceof ApiError && typeof assignCase.error.detail === "string"
              ? assignCase.error.detail
              : t("lecturerDashboard.assignForm.error")}
          </Alert>
        )}

        {assignCase.isSuccess && (
          <Alert severity="success">{t("lecturerDashboard.assignForm.success")}</Alert>
        )}

        <Button
          type="submit"
          variant="contained"
          disabled={!canSubmit || assignCase.isPending}
          sx={{ alignSelf: "flex-start" }}
        >
          {assignCase.isPending
            ? t("lecturerDashboard.assignForm.submitting")
            : t("lecturerDashboard.assignForm.submit")}
        </Button>
      </Stack>
    </Paper>
  );
}

function GroupList({
  selectedGroup,
  onSelectGroup,
}: {
  selectedGroup: string | null;
  onSelectGroup: (groupId: string) => void;
}): JSX.Element {
  const { t } = useTranslation();
  const { data: assignments, isLoading, isError } = useMyAssignments();

  const groups = useMemo(() => {
    const counts = new Map<string, number>();
    for (const assignment of assignments ?? []) {
      counts.set(assignment.assigned_to_group, (counts.get(assignment.assigned_to_group) ?? 0) + 1);
    }
    return [...counts.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  }, [assignments]);

  return (
    <Paper elevation={2} sx={{ p: 4 }}>
      <Stack spacing={2}>
        <Typography variant="h6" fontWeight={700}>
          {t("lecturerDashboard.groups.title")}
        </Typography>

        {isLoading && (
          <Box display="flex" justifyContent="center" py={4}>
            <CircularProgress aria-label={t("common.loading")} />
          </Box>
        )}

        {isError && <Alert severity="error">{t("lecturerDashboard.groups.loadError")}</Alert>}

        {groups.length === 0 && !isLoading && !isError && (
          <Typography variant="body2" color="text.secondary">
            {t("lecturerDashboard.groups.empty")}
          </Typography>
        )}

        <List dense disablePadding>
          {groups.map(([groupId, count]) => (
            <ListItem
              key={groupId}
              disableGutters
              divider
              secondaryAction={
                <Button
                  size="small"
                  variant={selectedGroup === groupId ? "contained" : "outlined"}
                  onClick={() => onSelectGroup(groupId)}
                >
                  {t("lecturerDashboard.groups.viewAnalytics")}
                </Button>
              }
            >
              <ListItemText
                primary={groupId}
                secondary={t("lecturerDashboard.groups.assignmentCount", { count })}
              />
            </ListItem>
          ))}
        </List>
      </Stack>
    </Paper>
  );
}

function CohortAnalyticsPanel({ groupId }: { groupId: string }): JSX.Element {
  const { t } = useTranslation();
  const { data, isLoading, isError } = useCohortAnalytics(groupId);

  return (
    <Paper elevation={2} sx={{ p: 4 }}>
      <Stack spacing={3}>
        <Typography variant="h6" fontWeight={700}>
          {t("lecturerDashboard.analytics.title", { group: groupId })}
        </Typography>

        {isLoading && (
          <Box display="flex" justifyContent="center" py={4}>
            <CircularProgress aria-label={t("common.loading")} />
          </Box>
        )}

        {isError && <Alert severity="error">{t("lecturerDashboard.analytics.loadError")}</Alert>}

        {data && (
          <>
            <Stack direction="row" spacing={4} flexWrap="wrap" useFlexGap>
              <Box>
                <Typography variant="overline" color="text.secondary">
                  {t("lecturerDashboard.analytics.distinctStudents")}
                </Typography>
                <Typography variant="h4" fontWeight={700}>
                  {data.distinct_students}
                </Typography>
              </Box>
              <Box>
                <Typography variant="overline" color="text.secondary">
                  {t("lecturerDashboard.analytics.totalAttempts")}
                </Typography>
                <Typography variant="h4" fontWeight={700}>
                  {data.total_attempts}
                </Typography>
              </Box>
              <Box>
                <Typography variant="overline" color="text.secondary">
                  {t("lecturerDashboard.analytics.overallAverage")}
                </Typography>
                <Typography variant="h4" fontWeight={700}>
                  {t("scoring.masteryValue", { score: Math.round(data.overall_average_score) })}
                </Typography>
              </Box>
            </Stack>

            <Divider />

            <Stack spacing={1}>
              <Typography variant="subtitle2">{t("lecturerDashboard.analytics.byCase")}</Typography>
              {data.cases.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  {t("lecturerDashboard.analytics.noAttemptsYet")}
                </Typography>
              ) : (
                <List dense disablePadding>
                  {data.cases.map((caseBreakdown) => (
                    <ListItem key={caseBreakdown.case_id} disableGutters divider>
                      <ListItemText
                        primary={caseBreakdown.disease_name}
                        secondary={t("lecturerDashboard.analytics.caseSummary", {
                          attempts: caseBreakdown.attempts_count,
                          students: caseBreakdown.distinct_students,
                          average: caseBreakdown.average_score,
                        })}
                      />
                      <Chip
                        size="small"
                        label={t("scoring.masteryValue", {
                          score: Math.round(caseBreakdown.average_score),
                        })}
                        color={masteryColor(caseBreakdown.average_score)}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </Stack>

            <Divider />

            <Stack spacing={1}>
              <Typography variant="subtitle2">
                {t("lecturerDashboard.analytics.byTopic")}
              </Typography>
              {data.topics.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  {t("lecturerDashboard.analytics.noAttemptsYet")}
                </Typography>
              ) : (
                <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                  {data.topics.map((topic) => (
                    <Chip
                      key={topic.topic}
                      label={`${t(`scoring.topics.${topic.topic}`, {
                        defaultValue: topic.topic,
                      })}: ${Math.round(topic.average_mastery)}%`}
                      color={masteryColor(topic.average_mastery)}
                      variant="outlined"
                    />
                  ))}
                </Stack>
              )}
            </Stack>

            <Divider />

            <Stack spacing={1}>
              <Typography variant="subtitle2">
                {t("lecturerDashboard.analytics.commonlyMissed")}
              </Typography>
              {data.commonly_missed_findings.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  {t("lecturerDashboard.analytics.noneMissed")}
                </Typography>
              ) : (
                <List dense disablePadding>
                  {data.commonly_missed_findings.map((finding) => (
                    <ListItem key={finding.finding} disableGutters divider>
                      <ListItemText
                        primary={finding.finding}
                        secondary={t("lecturerDashboard.analytics.missCount", {
                          count: finding.miss_count,
                        })}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </Stack>
          </>
        )}
      </Stack>
    </Paper>
  );
}

export function LecturerDashboardPage(): JSX.Element {
  const { t } = useTranslation();
  const [selectedGroup, setSelectedGroup] = useState<string | null>(null);

  return (
    <Box display="flex" justifyContent="center" px={2} py={6}>
      <Stack spacing={3} sx={{ width: "100%", maxWidth: 960 }}>
        <Stack
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          flexWrap="wrap"
          gap={2}
        >
          <Box>
            <Typography variant="h5" component="h1" fontWeight={700}>
              {t("lecturerDashboard.title")}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t("lecturerDashboard.subtitle")}
            </Typography>
          </Box>
          <Button component={RouterLink} to="/" variant="text">
            {t("hematology.caseIntake.backToDashboard")}
          </Button>
        </Stack>

        <AssignCaseForm onAssigned={setSelectedGroup} />
        <GroupList selectedGroup={selectedGroup} onSelectGroup={setSelectedGroup} />
        {selectedGroup && <CohortAnalyticsPanel groupId={selectedGroup} />}
      </Stack>
    </Box>
  );
}
