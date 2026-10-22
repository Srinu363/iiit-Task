/** React Query hooks for analysis operations. */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { analyzeImage, getAnalyses, getAnalysis, deleteAnalysis } from "../api/analysis";

export function useAnalyze() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: analyzeImage,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["analyses"] });
    },
  });
}

export function useHistory(page = 1, pageSize = 20, label?: string) {
  return useQuery({
    queryKey: ["analyses", page, pageSize, label],
    queryFn: () => getAnalyses(page, pageSize, label),
  });
}

export function useAnalysisDetail(id: string) {
  return useQuery({
    queryKey: ["analysis", id],
    queryFn: () => getAnalysis(id),
    enabled: !!id,
  });
}

export function useDeleteAnalysis() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteAnalysis,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["analyses"] });
    },
  });
}
