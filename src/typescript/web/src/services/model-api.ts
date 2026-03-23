type PeronosporaResponse = {
  forecast_date?: string;
  target_week?: {
    start?: string;
    end?: string;
  };
  detail?: Record<string, any>;
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

type ModelApiErrorPayload = {
  detail?: string;
  message?: string;
  error?: string;
};

const MODEL_API_ERROR_MAP: Record<string, string> = {
  "Location not in Emilia-Romagna province":
    "Il punto selezionato non si trova in una provincia dell'Emilia-Romagna.",
  "Report not available for province": "Bollettino non disponibile per la provincia selezionata.",
  "Report not found": "Bollettino non trovato.",
  "start must be before end": "La data di inizio deve essere precedente alla data di fine.",
};

function mapModelApiError(detail: string | undefined, status: number) {
  if (detail) {
    if (MODEL_API_ERROR_MAP[detail]) {
      return MODEL_API_ERROR_MAP[detail];
    }
    if (detail.startsWith("Prediction not found for province:")) {
      return "Previsione non disponibile per la provincia selezionata.";
    }
    if (detail.startsWith("Forecast not found:")) {
      return "Previsione non disponibile per la provincia selezionata.";
    }
    if (detail.startsWith("History directory not found:")) {
      return "Archivio storico non disponibile.";
    }
    if (detail.startsWith("Map not found:")) {
      return "Mappa non disponibile.";
    }
  }

  if (status === 400) {
    return "Richiesta non valida.";
  }
  if (status === 404) {
    return "Risorsa non trovata.";
  }
  if (status >= 500) {
    return "Errore del server dei modelli.";
  }
  return `Errore del servizio modelli (${status}).`;
}

function buildUrl(path: string, params?: Record<string, string | number>) {
  if (!MODEL_API_BASE) {
    throw new Error("URL base dei Model API non configurato.");
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
    let detail: string | undefined;
    try {
      const data = (await response.clone().json()) as ModelApiErrorPayload;
      detail = typeof data.detail === "string" ? data.detail : undefined;
      if (!detail && typeof data.message === "string") {
        detail = data.message;
      }
      if (!detail && typeof data.error === "string") {
        detail = data.error;
      }
    } catch {
      // Ignore parsing errors and fall back to status-based messages.
    }
    throw new Error(mapModelApiError(detail, response.status));
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

export async function fetchPeronosporaAllCurrent() {
  const response = await fetchJson<any>("/v1/peronospora/risk/current");
  return response.provinces as any[];
}

export async function fetchPeronosporaAllForecast() {
  const response = await fetchJson<any>("/v1/peronospora/risk/forecast");
  return response.provinces as any[];
}

export type { PeronosporaResponse, BollettinoResponse };
