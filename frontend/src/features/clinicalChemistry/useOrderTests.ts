import { useMutation, useQueryClient } from "@tanstack/react-query";

import { testsApi } from "@/api/testsApi";
import { useAppSelector } from "@/hooks/useAppStore";

export function useOrderTests(caseId: string) {
  const accessToken = useAppSelector((state) => state.auth.accessToken);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (testCodes: string[]) => testsApi.order(accessToken as string, caseId, testCodes),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["results", caseId] });
    },
  });
}
