import { useQuery } from "@tanstack/react-query";

import { scoringApi } from "@/api/scoringApi";
import { useAppSelector } from "@/hooks/useAppStore";

export function useScoringSummary() {
  const accessToken = useAppSelector((state) => state.auth.accessToken);

  return useQuery({
    queryKey: ["scoring", "me"],
    queryFn: () => scoringApi.me(accessToken as string),
    enabled: Boolean(accessToken),
    staleTime: 0,
  });
}
