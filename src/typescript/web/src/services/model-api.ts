type PeronosporaResponse = {
  forecast_date?: string;
  target_week?: {
    start?: string;
    end?: string;
  };
  detail?: Record<string, unknown>;
  location?: {
    lat: number;
    lng: number;
  };
  province?: string;
};

type BollettinoResponse = {
  type?: string;
  province?: string;
  filename?: string;
  report_date?: string;
  last_modified?: string;
  content?: string;
  location?: {
    lat: number;
    lng: number;
  };
};

const MODEL_API_BASE = (process.env.REACT_APP_MODELAPIS_SERVER_URL ?? "").replace(/\/$/, "");

function buildUrl(path: string, params?: Record<string, string | number>) {
  if (!MODEL_API_BASE) {
    throw new Error("Model API base URL not configured.");
  }
  const url = new URL(`${MODEL_API_BASE}${path}`);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      url.searchParams.set(key, String(value));
    });
  }
  return url.toString();
}

async function fetchJson<T>(path: string, params?: Record<string, string | number>): Promise<T> {
  const response = await fetch(buildUrl(path, params));
  if (!response.ok) {
    throw new Error(`Model API error: ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function fetchPeronosporaCurrent(lat: number, lng: number) {
  return fetchJson<PeronosporaResponse>("/v1/peronospora/risk/location/current", { lat, lng });
}

export async function fetchPeronosporaForecast(lat: number, lng: number) {
  return fetchJson<PeronosporaResponse>("/v1/peronospora/risk/location/forecast", { lat, lng });
}

export async function fetchCimiceReport(lat: number, lng: number) {
  return fetchJson<BollettinoResponse>("/v1/bollettini/cimice/location", { lat, lng });
}

export async function fetchFlavescenzaReport(lat: number, lng: number) {
  return fetchJson<BollettinoResponse>("/v1/bollettini/flavescenza/location", { lat, lng });
}

export type { PeronosporaResponse, BollettinoResponse };
