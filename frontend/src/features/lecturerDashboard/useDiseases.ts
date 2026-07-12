import { useQuery } from "@tanstack/react-query";

import { diseasesApi } from "@/api/diseasesApi";
import { useAppSelector } from "@/hooks/useAppStore";

export function useDiseases() {
  const accessToken = useAppSelector((state) => state.auth.accessToken);

  return useQuery({
    queryKey: ["diseases"],
    queryFn: () => diseasesApi.list(accessToken as string),
    enabled: Boolean(accessToken),
    staleTime: 5 * 60 * 1000,
  });
}
