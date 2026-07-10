import { useQuery } from "@tanstack/react-query";

import { casesApi, type CaseDifficulty } from "@/api/casesApi";
import { useAppSelector } from "@/hooks/useAppStore";

interface UseNextCaseOptions {
  difficulty?: CaseDifficulty;
  /** Bump this to force a brand-new case with the same filters. */
  requestId?: number;
}

export function useNextCase({ difficulty = "novice", requestId = 0 }: UseNextCaseOptions = {}) {
  const accessToken = useAppSelector((state) => state.auth.accessToken);

  return useQuery({
    queryKey: ["cases", "next", difficulty, requestId],
    queryFn: () => casesApi.next(accessToken as string, { difficulty }),
    enabled: Boolean(accessToken),
    staleTime: 0,
    retry: false,
  });
}
