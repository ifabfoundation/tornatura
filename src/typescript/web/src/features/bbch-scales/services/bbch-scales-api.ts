import axios from "axios";
import { getCoreApiConfiguration } from "../../../services/utils";

export type BbchStage = {
  code: string;
  name: string;
  thumbnail?: string | null;
  icon?: string | null;
  sortOrder: number;
};

export type BbchGroup = {
  code: string;
  name: string;
  icon?: string | null;
  sortOrder: number;
  stages: BbchStage[];
};

export type BbchScale = {
  id: string;
  harvestCode: string;
  sourceHarvestCode?: string | null;
  groups: BbchGroup[];
  creationTime: number;
  lastUpdateTime: number;
};

async function requestConfig() {
  const configuration = await getCoreApiConfiguration();
  return {
    baseURL: configuration.basePath,
    headers: configuration.baseOptions?.headers,
  };
}

export async function listBbchScales() {
  const response = await axios.get<BbchScale[]>("/v1/bbch-scales", await requestConfig());
  return response.data;
}

export async function getBbchScale(harvestCode: string) {
  const response = await axios.get<BbchScale>(
    `/v1/bbch-scales/${encodeURIComponent(harvestCode)}`,
    await requestConfig(),
  );
  return response.data;
}

export async function createBbchScale(payload: {
  harvestCode: string;
  sourceHarvestCode?: string | null;
  groups?: BbchGroup[];
}) {
  const response = await axios.post<BbchScale>("/v1/bbch-scales", payload, await requestConfig());
  return response.data;
}

export async function updateBbchScale(harvestCode: string, groups: BbchGroup[]) {
  const response = await axios.put<BbchScale>(
    `/v1/bbch-scales/${encodeURIComponent(harvestCode)}`,
    { groups },
    await requestConfig(),
  );
  return response.data;
}

export async function duplicateBbchScale(sourceHarvestCode: string, targetHarvestCode: string) {
  const response = await axios.post<BbchScale>(
    `/v1/bbch-scales/${encodeURIComponent(sourceHarvestCode)}/duplicate`,
    { targetHarvestCode },
    await requestConfig(),
  );
  return response.data;
}

export async function deleteBbchScale(harvestCode: string) {
  await axios.delete(
    `/v1/bbch-scales/${encodeURIComponent(harvestCode)}`,
    await requestConfig(),
  );
}

export async function uploadBbchThumbnail(file: File) {
  const body = new FormData();
  body.append("file", file);
  const response = await axios.post<{ category: string; name: string }>(
    "/v1/bbch-scales/thumbnails/upload",
    body,
    await requestConfig(),
  );
  return response.data;
}
