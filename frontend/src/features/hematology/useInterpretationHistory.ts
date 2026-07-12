import { useQuery } from "@tanstack/react-query";

import { interpretationsApi } from "@/api/interpretationsApi";
import { useAppSelector } from "@/hooks/useAppStore";

export function useInterpretationHistory(caseId: string) {
  const accessToken = useAppSelector((state) => state.auth.accessToken);

  return useQuery({
    queryKey: ["interpretations", caseId],
    queryFn: () => interpretationsApi.history(accessToken as string, caseId),
    enabled: Boolean(accessToken) && Boolean(caseId),
    staleTime: 0,
  });
}
