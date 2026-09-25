import type { FeatureCollection, Geometry, Polygon } from "geojson";

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
  culture?: string;
  region?: string;
  province?: string;
  report_slug?: string;
  filename?: string;
  report_date?: string;
  last_modified?: string;
  content?: string;
  location?: {
    lat: number;
    lng: number;
  };
};

type LandscapeCropInfo = {
  harvest?: string | null;
  icolt_class?: string | null;
  mappable?: boolean;
  reason?: "aggregated_class" | "not_in_dataset" | "unknown_harvest_code" | null;
  ha?: number | null;
  pct_of_agri?: number | null;
  presence?: {
    level?: string;
    icon?: string;
  } | null;
};

type LandscapeClassShare = {
  icolt_class?: string;
  /** Famiglia colturale, usata per il colore fisso su mappa e tabella. */
  family?: string;
  ha?: number;
  pct?: number;
  /** null per le classi accorpate: sotto tre appezzamenti il conteggio non si pubblica. */
  parcels?: number | null;
  merged_classes?: number;
};

/** La sorgente che ha prodotto i numeri principali. */
type LandscapeSource = "agrea" | "icolt";

/** Elementi semi-naturali nel buffer: bosco piu' siepi, margini e fossi. */
type LandscapeSeminatural = {
  bosco_ha?: number;
  elementi_ha?: number;
  elementi_n?: number;
  ha?: number;
  pct_of_buffer?: number;
  elementi_method?: string;
};

/** La seconda misura, indipendente: serve a dichiarare l'incertezza. */
type LandscapeCrosscheck = {
  source?: LandscapeSource;
  year?: number;
  mapped_ha?: number;
  mapped_pct_of_buffer?: number;
  crop_pct_of_agri?: number | null;
  crop_ha?: number | null;
  delta_pct_points?: number | null;
  usable?: boolean;
  coverage_note?: string | null;
};

/** Quanta parte dell'intorno il dato riesce a vedere, misurata a raggio fisso. */
type LandscapeObservability = {
  status?: "full" | "partial" | "suppressed";
  radius_m?: number;
  mapped_pct?: number;
  quadrant_pct?: number[];
  worst_quadrant_pct?: number;
};

type LandscapeResponse = {
  location?: {
    lat: number;
    lng: number;
  };
  radius_m?: number;
  dataset?: {
    source?: string;
    year?: number;
    region?: string;
  };
  buffer_ha?: number;
  /** Deprecato: il nome dice "agricola" ma e' la superficie CARTOGRAFATA. */
  agri_ha?: number;
  mapped_ha?: number;
  mapped_pct_of_buffer?: number;
  agri_pct_of_buffer?: number;
  parcels?: number;
  crop?: LandscapeCropInfo;
  coverage_note?: string | null;
  observability?: LandscapeObservability;
  source?: LandscapeSource;
  crosscheck?: LandscapeCrosscheck | null;
  seminatural?: LandscapeSeminatural | null;
  aggregated_classes?: Record<string, string>;
  composition?: LandscapeClassShare[];
};

type LandscapeParcelsResponse = {
  /** Presente quando la richiesta aveva `pest=`. */
  pest?: LandscapePestSummary;
  location?: { lat: number; lng: number };
  radius_m?: number;
  dataset?: { source?: string; year?: number; region?: string };
  buffer_ha?: number;
  /** Poligono del buffer calcolato dal servizio: e' l'area su cui i numeri sono veri. */
  buffer?: Polygon;
  crop?: LandscapeCropInfo;
  coverage_note?: string | null;
  observability?: LandscapeObservability;
  /** Classe iColt collettiva -> colture che contiene. */
  aggregated_classes?: Record<string, string>;
  count?: number;
  truncated?: boolean;
  source?: LandscapeSource;
  /** Soglia di DISEGNO: i poligoni sotto questa superficie non sono disegnati. */
  map_min_ha?: number;
  /** Quota della superficie effettivamente disegnata, sul totale. */
  map_pct_of_area?: number;
  parcels?: {
    type: "FeatureCollection";
    features: Array<{
      type: "Feature";
      properties: {
        icolt_class?: string;
        /** La specie come sta nel dato dichiarativo: chiave del join con le tabelle ospiti. */
        declared?: string;
        ha?: number;
        is_crop?: boolean;
        family?: string;
        /** Presente solo con `pest=`: livello ospite della specie per quell'organismo. */
        host_level?: string;
      };
      geometry: Geometry;
    }>;
  };
};

/**
 * Un PEZZO scegliibile: il frammento come sta nel dato dichiarativo, cioe'
 * l'appezzamento intersecato la particella catastale. E' la granularita' minima
 * esistente, e serve al disegno del campo perche' permette di prendere una
 * porzione invece di tutto il campo dichiarato.
 */
type LandscapePiece = {
  type: "Feature";
  properties: {
    /** Identificativo del pezzo, stabile fra una richiesta e l'altra. */
    pid: number;
    /** Quali pezzi formano lo stesso campo dichiarato. Non dice di chi e'. */
    app_id: number;
    /** Quanti pezzi ha quel campo in tutto, anche fuori dalla vista. */
    app_n: number;
    crop?: string;
    /** Codice del registro colture di tornatura, se la specie vi corrisponde. */
    harvest_code?: string | null;
    family?: string;
    /** Superficie calcolata dal servizio in UTM 32N: NON ricalcolarla. */
    ha?: number;
    is_crop_class?: boolean;
  };
  geometry: Geometry;
};

/**
 * I pezzi nella vista. `count: 0` NON e' un errore: significa che non c'e' nulla
 * da proporre (azienda che non presenta il piano colturale, pezzi sotto la soglia
 * minima, punto fuori dalla copertura) e si disegna a mano.
 */
type LandscapePiecesResponse = {
  source?: string;
  year?: number;
  count?: number;
  /**
   * Vero quando a questa larghezza di vista i pezzi piu' piccoli non sono
   * serviti: la risposta ha un tetto sui vertici, che e' cio' che ne determina il
   * peso. Va detto all'utente, altrimenti sembra che quei campi non esistano.
   */
  truncated?: boolean;
  /** Superficie minima dei pezzi effettivamente serviti, in ettari. */
  piece_min_ha?: number;
  /** Decimali delle coordinate: 7 = 1,1 cm. Non ricalcolare le superfici. */
  coord_decimals?: number;
  pieces?: FeatureCollection<Geometry, LandscapePiece["properties"]>;
};

/**
 * L'appezzamento dichiarato che contiene un punto, per suggerire il confine di un
 * campo nuovo. `found: false` NON e' un errore: significa che non c'e' nulla da
 * suggerire (azienda che non presenta il piano colturale, appezzamento sotto la
 * soglia minima, oppure punto fuori dalla copertura).
 */
type LandscapeParcelSuggestion = {
  found: boolean;
  reason?: string;
  source?: string;
  year?: number;
  geometry?: Geometry;
  /** Superficie calcolata dal servizio in UTM 32N: NON ricalcolarla dal poligono. */
  ha?: number;
  crop?: {
    declared?: string;
    display?: string;
    /** Codice del registro colture di tornatura, se la specie vi corrisponde. */
    harvest_code?: string | null;
  };
  is_crop_class?: boolean;
  precision?: {
    simplified_m?: number;
    datum_accuracy_m?: number;
    note?: string;
  };
};

/** Un organismo di cui il servizio sa descrivere l'habitat (una cartella in data/pests). */
type LandscapePestSummary = {
  code: string;
  label?: string;
  scientific_name?: string;
  eppo_code?: string;
  hosts_version?: string;
  /** null = tutte le colture. */
  applies_to_harvests?: string[] | null;
};

type LandscapePestShare = {
  label?: string;
  ha?: number;
  pct_of_buffer?: number;
  pct_of_declared?: number;
  parcels?: number;
};

/** Distanza al piu' vicino: SOLO come classe, mai in metri (anonimato). */
type LandscapeDistanceClass = {
  class?: string;
  label?: string;
  label_target?: string;
};

/**
 * Quanto il paesaggio dichiarato intorno al campo ospita un organismo.
 * `available: false` NON e' un errore: la sezione non si mostra.
 */
type LandscapePestHabitat = {
  available: boolean;
  reason?: string;
  pest?: LandscapePestSummary;
  location?: { lat: number; lng: number };
  radius_m?: number;
  source?: string;
  year?: number;
  hosts_version?: string;
  buffer_ha?: number;
  declared_ha?: number;
  declared_pct_of_buffer?: number;
  agri_ha?: number;
  levels?: Record<string, LandscapePestShare>;
  hosts?: LandscapePestShare & { by_family?: Record<string, LandscapePestShare> };
  top_hosts?: Array<{
    species: string;
    declared?: string;
    level: string;
    family?: string;
    ha: number;
    pct_of_declared?: number;
    parcels: number;
  }>;
  min_parcels_per_row?: number;
  reservoirs?: LandscapeSeminatural & { label?: string };
  nearest?: Record<string, LandscapeDistanceClass>;
  nearest_origin?: "ring" | "declared_parcel" | "centroid";
  field?: { species?: string; level?: string } | null;
  texts?: Record<string, string>;
  limits?: string[];
  sources?: Array<{ id: string; citation: string; url?: string }>;
};

/** Classi della finestra stagionale, nell'ordine in cui si mostrano. */
type LandscapeSeasonClass = "active" | "arriving" | "not_yet" | "over" | "no_phase" | "no_window";

/**
 * Quali ospiti intorno al campo sono oggi nella fase che l'organismo attacca, e dove.
 * `source` dice da dove arrivano le fasi: dal bollettino della zona o, se il servizio
 * bollettini non risponde, dal calendario 2026. `available: false` non e' un errore.
 */
type LandscapePestSeason = {
  available: boolean;
  reason?: string;
  pest?: LandscapePestSummary;
  date?: string;
  radius_m?: number;
  source?: "bulletins" | "calendar_2026";
  area?: string | null;
  last_bulletin?: { file: string; date: string } | null;
  /** Perche' si usa il calendario: servizio non raggiungibile, non configurato o senza dati. */
  fallback_reason?: "bulletins_unreachable" | "bulletins_not_configured" | "bulletins_no_data" | null;
  /** Ettari attivi che hanno una direzione (escluso l'appezzamento sotto il punto). */
  active_ha_directional?: number;
  validity_days?: number;
  hosts_ha?: number;
  classes?: Record<LandscapeSeasonClass, { ha: number; pct_of_hosts: number; parcels: number; label?: string }>;
  partial_active_ha?: number;
  crops?: Array<{
    species: string;
    declared?: string;
    class: LandscapeSeasonClass;
    partial?: boolean;
    ha: number;
    parcels: number;
    phases?: string[];
    bbch_min?: number | null;
    bbch_max?: number | null;
    bulletin_date?: string | null;
  }>;
  /** Ettari per settore di 45 gradi; null quando il settore ha meno di tre appezzamenti. */
  sectors?: Array<{
    sector: string;
    label: string;
    parcels: number;
    shown: boolean;
    active_ha: number | null;
    arriving_ha: number | null;
  }>;
  main_directions?: string[];
  min_parcels_per_row?: number;
  windows?: Record<string, { active: number[]; arriving: number[]; note?: string; sources?: string[] }>;
  method?: string;
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
  "Location not in supported province":
    "Il campo selezionato non rientra in un'area coperta dai bollettini fitosanitari.",
  "Report not available for province": "Bollettino non disponibile per la provincia selezionata.",
  "Report not found": "Bollettino non trovato.",
  "Culture report not available for province":
    "Il bollettino per la coltura del campo non è disponibile per questa provincia.",
  "Culture reports not found":
    "Non ci sono ancora bollettini disponibili per la coltura del campo.",
  "Region not supported for culture reports":
    "La regione del campo non è ancora supportata dai bollettini fitosanitari.",
  "Invalid culture": "La coltura del campo non è supportata dai bollettini fitosanitari.",
  "start must be before end": "La data di inizio deve essere precedente alla data di fine.",
  "Location outside data coverage":
    "Il campo selezionato è fuori dall'area coperta dai dati sul paesaggio agricolo (attualmente la sola Emilia-Romagna).",
  "Landscape dataset not available":
    "I dati sul paesaggio agricolo non sono al momento disponibili.",
  "Unknown pest": "Organismo non riconosciuto dal servizio del paesaggio.",
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
    return "Bollettino non disponibile per il campo selezionato.";
  }
  if (status >= 500) {
    return "Il servizio bollettini non è al momento disponibile.";
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

export async function fetchCultureReport(culture: string, lat: number, lng: number) {
  return fetchJson<BollettinoResponse>(`/v1/bollettini/culture/${encodeURIComponent(culture)}/location`, {
    lat,
    lng,
  });
}

export async function fetchPeronosporaAllCurrent() {
  const response = await fetchJson<any>("/v1/peronospora/risk/current");
  return response.provinces as any[];
}

export async function fetchPeronosporaAllForecast() {
  const response = await fetchJson<any>("/v1/peronospora/risk/forecast");
  return response.provinces as any[];
}

export async function fetchLandscapeComposition(
  lat: number,
  lng: number,
  radiusM: number,
  crop?: string,
) {
  return fetchJson<LandscapeResponse>("/v1/landscape/composition", {
    lat,
    lng,
    radius_m: radiusM,
    ...(crop ? { crop } : {}),
  });
}

export async function fetchLandscapeParcels(
  lat: number,
  lng: number,
  radiusM: number,
  crop?: string,
  pest?: string,
) {
  return fetchJson<LandscapeParcelsResponse>("/v1/landscape/parcels", {
    lat,
    lng,
    radius_m: radiusM,
    ...(crop ? { crop } : {}),
    ...(pest ? { pest } : {}),
  });
}

/** Gli organismi pertinenti a una coltura: decide quali sezioni disegnare. */
export async function fetchLandscapePests(crop?: string) {
  return fetchJson<{ pests: LandscapePestSummary[] }>("/v1/landscape/pests", {
    ...(crop ? { crop } : {}),
  });
}

/**
 * Contorno del campo nel formato compatto del servizio: "lng,lat;lng,lat;...".
 * Sei decimali sono 11 cm: sufficienti per una distanza pubblicata in classi.
 */
export function ringParam(ring: number[][] | null | undefined): string | undefined {
  if (!ring || ring.length < 4) {
    return undefined;
  }
  return ring.map(([lng, lat]) => `${lng.toFixed(6)},${lat.toFixed(6)}`).join(";");
}

export async function fetchLandscapePestHabitat(
  lat: number,
  lng: number,
  radiusM: number,
  pest: string,
  crop?: string,
  ring?: string,
) {
  return fetchJson<LandscapePestHabitat>("/v1/landscape/pest-habitat", {
    lat,
    lng,
    radius_m: radiusM,
    pest,
    ...(crop ? { crop } : {}),
    ...(ring ? { ring } : {}),
  });
}

export async function fetchLandscapePestSeason(lat: number, lng: number, radiusM: number, pest: string) {
  return fetchJson<LandscapePestSeason>("/v1/landscape/pest-season", {
    lat,
    lng,
    radius_m: radiusM,
    pest,
  });
}

export async function fetchLandscapePieces(lat: number, lng: number, radiusM: number) {
  return fetchJson<LandscapePiecesResponse>("/v1/landscape/pieces", {
    lat,
    lng,
    radius_m: radiusM,
  });
}

export async function fetchLandscapeParcelAt(lat: number, lng: number) {
  return fetchJson<LandscapeParcelSuggestion>("/v1/landscape/parcel-at", { lat, lng });
}

export type {
  PeronosporaResponse,
  BollettinoResponse,
  LandscapeResponse,
  LandscapeCropInfo,
  LandscapeClassShare,
  LandscapeParcelsResponse,
  LandscapeObservability,
  LandscapeSource,
  LandscapeSeminatural,
  LandscapeCrosscheck,
  LandscapeParcelSuggestion,
  LandscapePiece,
  LandscapePiecesResponse,
  LandscapePestSummary,
  LandscapePestShare,
  LandscapePestHabitat,
  LandscapeDistanceClass,
  LandscapePestSeason,
  LandscapeSeasonClass,
};
