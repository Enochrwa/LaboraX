import { useQuery } from "@tanstack/react-query";

import { testsApi } from "@/api/testsApi";
import { useAppSelector } from "@/hooks/useAppStore";

export function useTestCatalog() {
  const accessToken = useAppSelector((state) => state.auth.accessToken);

  return useQuery({
    queryKey: ["tests", "catalog"],
    queryFn: () => testsApi.catalog(accessToken as string),
    enabled: Boolean(accessToken),
    staleTime: Infinity,
  });
}
