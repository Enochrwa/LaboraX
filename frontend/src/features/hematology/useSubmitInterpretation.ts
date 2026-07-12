import { useMutation, useQueryClient } from "@tanstack/react-query";

import { interpretationsApi } from "@/api/interpretationsApi";
import { useAppSelector } from "@/hooks/useAppStore";

export function useSubmitInterpretation(caseId: string) {
  const accessToken = useAppSelector((state) => state.auth.accessToken);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (freeText: string) =>
      interpretationsApi.submit(accessToken as string, caseId, freeText),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["interpretations", caseId] });
    },
  });
}
