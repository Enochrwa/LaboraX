import { useQuery } from "@tanstack/react-query";

import { testsApi } from "@/api/testsApi";
import { useAppSelector } from "@/hooks/useAppStore";

export function useCaseResults(caseId: string) {
  const accessToken = useAppSelector((state) => state.auth.accessToken);

  return useQuery({
    queryKey: ["results", caseId],
    queryFn: () => testsApi.results(accessToken as string, caseId),
    enabled: Boolean(accessToken) && Boolean(caseId),
    staleTime: 0,
  });
}
