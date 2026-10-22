/** API functions for image analysis operations. */

import client from "./client";
import type { AnalysisResult, AnalysisListResponse } from "../types/analysis";

export async function analyzeImage(file: File): Promise<AnalysisResult> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await client.post<AnalysisResult>(
    "/api/v1/analyze",
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return data;
}

export async function getAnalyses(
  page = 1,
  pageSize = 20,
  label?: string
): Promise<AnalysisListResponse> {
  const params: Record<string, string | number> = { page, page_size: pageSize };
  if (label) params.label = label;
  const { data } = await client.get<AnalysisListResponse>(
    "/api/v1/analyses",
    { params }
  );
  return data;
}

export async function getAnalysis(id: string): Promise<AnalysisResult> {
  const { data } = await client.get<AnalysisResult>(`/api/v1/analyses/${id}`);
  return data;
}

export async function deleteAnalysis(id: string): Promise<void> {
  await client.delete(`/api/v1/analyses/${id}`);
}
