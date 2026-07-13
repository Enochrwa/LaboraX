import { useQuery } from "@tanstack/react-query";

import { casesApi, type CaseDifficulty } from "@/api/casesApi";
import { useAppSelector } from "@/hooks/useAppStore";

interface UseNextCaseOptions {
  difficulty?: CaseDifficulty;
  /** Bump this to force a brand-new case with the same filters. */
  requestId?: number;
}

/**
 * Sprint 7 (Clinical Chemistry): identical to `hematology/useNextCase`, but
 * pinned to `category: "chemistry"` so this module only ever surfaces
 * chemistry disease templates (LFT/RFT/electrolyte patterns), never a
 * hematology one, even though both flow through the same `/cases/next`
 * endpoint (see `app/api/v1/routes/cases.py`'s `category` query param).
 */
export function useNextCase({ difficulty = "novice", requestId = 0 }: UseNextCaseOptions = {}) {
  const accessToken = useAppSelector((state) => state.auth.accessToken);

  return useQuery({
    queryKey: ["cases", "next", "chemistry", difficulty, requestId],
    queryFn: () => casesApi.next(accessToken as string, { difficulty, category: "chemistry" }),
    enabled: Boolean(accessToken),
    staleTime: 0,
    retry: false,
  });
}
