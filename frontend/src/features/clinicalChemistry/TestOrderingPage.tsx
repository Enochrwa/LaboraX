import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  CircularProgress,
  Divider,
  FormControlLabel,
  List,
  ListItem,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import type { JSX } from "react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link as RouterLink, useParams } from "react-router-dom";

import type { Result } from "@/api/testsApi";
import { useCaseResults } from "./useCaseResults";
import { useOrderTests } from "./useOrderTests";
import { useTestCatalog } from "./useTestCatalog";

const FLAG_COLOR: Record<string, "default" | "warning" | "error"> = {
  normal: "default",
  low: "warning",
  high: "error",
  abnormal: "error",
};

function ResultCard({ result }: { result: Result }): JSX.Element {
  const { t } = useTranslation();
  const { values, flags, findings, flag } = result.result_payload;

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
        <Typography variant="subtitle2" fontWeight={600}>
          {result.test.name}
        </Typography>
        {flag && (
          <Chip
            size="small"
            label={t(`clinicalChemistry.testOrdering.flags.${flag}`, { defaultValue: flag })}
            color={FLAG_COLOR[flag] ?? "default"}
          />
        )}
      </Stack>

      {values && flags && (
        <Stack spacing={0.5}>
          {Object.entries(values).map(([parameter, value]) => (
            <Stack key={parameter} direction="row" justifyContent="space-between">
              <Typography variant="body2" color="text.secondary">
                {t(`clinicalChemistry.testOrdering.parameterLabels.${parameter}`, {
                  defaultValue: parameter,
                })}
              </Typography>
              <Stack direction="row" spacing={1} alignItems="center">
                <Typography variant="body2" fontWeight={600}>
                  {value}
                </Typography>
                <Chip
                  size="small"
                  variant="outlined"
                  label={t(`clinicalChemistry.testOrdering.flags.${flags[parameter]}`, {
                    defaultValue: flags[parameter],
                  })}
                  color={FLAG_COLOR[flags[parameter]] ?? "default"}
                />
              </Stack>
            </Stack>
          ))}
        </Stack>
      )}

      {findings && (
        <List dense disablePadding>
          {findings.map((finding) => (
            <ListItem key={finding} disableGutters sx={{ display: "list-item", pl: 2 }}>
              <Typography variant="body2">{finding}</Typography>
            </ListItem>
          ))}
        </List>
      )}
    </Paper>
  );
}

export function TestOrderingPage(): JSX.Element {
  const { t } = useTranslation();
  const { caseId } = useParams<{ caseId: string }>();
  const [selectedCodes, setSelectedCodes] = useState<string[]>([]);

  const { data: catalog, isLoading: catalogLoading, isError: catalogError } = useTestCatalog();
  const {
    data: caseResults,
    isLoading: resultsLoading,
    isError: resultsError,
  } = useCaseResults(caseId ?? "");
  const orderTests = useOrderTests(caseId ?? "");

  const orderedCodes = useMemo(
    () => new Set(caseResults?.results.map((result) => result.test.code) ?? []),
    [caseResults],
  );

  const toggleCode = (code: string): void => {
    setSelectedCodes((current) =>
      current.includes(code) ? current.filter((c) => c !== code) : [...current, code],
    );
  };

  const handleSubmit = (): void => {
    if (!caseId || selectedCodes.length === 0) return;
    orderTests.mutate(selectedCodes, {
      onSuccess: () => setSelectedCodes([]),
    });
  };

  const totalPenalty = orderTests.data?.total_penalty ?? caseResults?.total_penalty ?? 0;

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
                {t("clinicalChemistry.testOrdering.title")}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t("clinicalChemistry.testOrdering.subtitle")}
              </Typography>
            </Box>
            <Button component={RouterLink} to="/" variant="text">
              {t("clinicalChemistry.caseIntake.backToDashboard")}
            </Button>
          </Stack>

          {(catalogLoading || resultsLoading) && (
            <Box display="flex" justifyContent="center" py={6}>
              <CircularProgress aria-label={t("common.loading")} />
            </Box>
          )}

          {(catalogError || resultsError) && (
            <Alert severity="error">{t("clinicalChemistry.testOrdering.loadError")}</Alert>
          )}

          {orderTests.isError && (
            <Alert severity="error">
              {orderTests.error instanceof Error
                ? orderTests.error.message
                : t("clinicalChemistry.testOrdering.orderError")}
            </Alert>
          )}

          {catalog && (
            <Stack spacing={1}>
              <Typography variant="subtitle2">
                {t("clinicalChemistry.testOrdering.selectTests")}
              </Typography>
              <Stack>
                {catalog.map((test) => {
                  const alreadyOrdered = orderedCodes.has(test.code);
                  return (
                    <FormControlLabel
                      key={test.id}
                      control={
                        <Checkbox
                          checked={selectedCodes.includes(test.code) || alreadyOrdered}
                          disabled={alreadyOrdered || orderTests.isPending}
                          onChange={() => toggleCode(test.code)}
                        />
                      }
                      label={
                        <Stack direction="row" spacing={1} alignItems="center">
                          <Typography variant="body2">{test.name}</Typography>
                          {alreadyOrdered && (
                            <Chip
                              size="small"
                              variant="outlined"
                              label={t("clinicalChemistry.testOrdering.alreadyOrdered")}
                            />
                          )}
                        </Stack>
                      }
                    />
                  );
                })}
              </Stack>
              <Button
                variant="contained"
                onClick={handleSubmit}
                disabled={selectedCodes.length === 0 || orderTests.isPending}
                sx={{ alignSelf: "flex-start" }}
              >
                {orderTests.isPending
                  ? t("clinicalChemistry.testOrdering.ordering")
                  : t("clinicalChemistry.testOrdering.orderSelected")}
              </Button>
            </Stack>
          )}

          <Divider />

          <Stack spacing={2}>
            <Stack direction="row" justifyContent="space-between" alignItems="center">
              <Typography variant="subtitle2">
                {t("clinicalChemistry.testOrdering.results")}
              </Typography>
              <Chip
                size="small"
                label={t("clinicalChemistry.testOrdering.totalPenalty", { penalty: totalPenalty })}
                color={totalPenalty > 0 ? "warning" : "default"}
              />
            </Stack>

            {caseResults && caseResults.results.length === 0 && (
              <Typography variant="body2" color="text.secondary">
                {t("clinicalChemistry.testOrdering.noResultsYet")}
              </Typography>
            )}

            {caseResults?.results.map((result) => (
              <ResultCard key={result.id} result={result} />
            ))}

            {caseResults && caseResults.results.length > 0 && (
              <Button
                component={RouterLink}
                to={`/chemistry/case/${caseId}/interpretation`}
                variant="contained"
                sx={{ alignSelf: "flex-start" }}
              >
                {t("clinicalChemistry.testOrdering.submitInterpretation")}
              </Button>
            )}
          </Stack>
        </Stack>
      </Paper>
    </Box>
  );
}
