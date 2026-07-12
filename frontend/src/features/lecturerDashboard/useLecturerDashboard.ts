import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { AssignCasePayload } from "@/api/lecturerApi";
import { lecturerApi } from "@/api/lecturerApi";
import { useAppSelector } from "@/hooks/useAppStore";

export function useMyAssignments() {
  const accessToken = useAppSelector((state) => state.auth.accessToken);

  return useQuery({
    queryKey: ["lecturer", "assignments"],
    queryFn: () => lecturerApi.myAssignments(accessToken as string),
    enabled: Boolean(accessToken),
    staleTime: 0,
  });
}

export function useAssignCase() {
  const accessToken = useAppSelector((state) => state.auth.accessToken);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: AssignCasePayload) =>
      lecturerApi.assignCase(accessToken as string, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["lecturer", "assignments"] });
    },
  });
}

export function useCohortAnalytics(groupId: string | null) {
  const accessToken = useAppSelector((state) => state.auth.accessToken);

  return useQuery({
    queryKey: ["lecturer", "analytics", groupId],
    queryFn: () => lecturerApi.cohortAnalytics(accessToken as string, groupId as string),
    enabled: Boolean(accessToken) && Boolean(groupId),
    staleTime: 0,
  });
}
