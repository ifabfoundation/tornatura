import React from "react";
import mapboxgl from "mapbox-gl";
import type { ExpressionSpecification, FilterSpecification } from "mapbox-gl";
import * as turf from "@turf/turf";

/**
 * Mappa del paesaggio agricolo intorno a un campo.
 *
 * Struttura ripresa da MapNUTSData (init in un solo effect con map.on("load"),
 * aggiornamento dei dati via getSource().setData senza ricreare la mappa, popup
 * registrato sul layer) e da FieldMaplet per la geometria del campo e il fit.
 *
 * Due layer accendibili sulla stessa sorgente, come da specifica:
 *  - tutte le superfici agricole cartografate, colore neutro (contesto);
 *  - solo gli appezzamenti della coltura dell'utente, evidenziati (sopra).
 *
 * L'opacita' e' volutamente contenuta: un poligono pieno comunicherebbe una
 * certezza che una classificazione satellitare annuale non ha.
 */

/**
 * Colori delle famiglie colturali.
 *
 * Non un colore per ognuna delle 16 classi: su fondo satellitare, dove qualsiasi
 * classe puo' confinare con qualsiasi altra, oltre quattro colori le coppie
 * diventano indistinguibili anche a visione normale (validato: giallo/arancio
 * ΔE 13,7 contro una soglia di 15). Questo quartetto e' stato verificato col
 * validatore della palette documentata: separazione CVD 13,0 e visione normale
 * 19,6, entrambe sopra soglia. Il colore e' FISSO per famiglia, mai assegnato per
 * posizione in classifica: cambiare raggio non deve ridipingere le classi.
 * Il dettaglio per specie sta nella tabella e nel popup, dove il nome e' scritto
 * e il colore non porta l'informazione da solo.
 *
 * Il verde va al SEMI-NATURALE (bosco, siepi, margini, fossi) e non ai prati:
 * la letteratura indica l'habitat semi-naturale come driver per Halyomorpha
 * halys e Drosophila suzukii, mentre la distinzione fra prati e seminativi non
 * cambia nessuna decisione. La distinzione persa resta leggibile nella tabella,
 * dove ogni classe ha la sua riga.
 */
export const COLORE_CAMPO = "#EAFF00";
export const COLORE_COLTURA = "#e87ba4";
const COLORE_PERMANENTI = "#2a78d6";
const COLORE_ERBACEE = "#eda100";
const COLORE_SEMINATURALE = "#008300";
const COLORE_ALTRO = "#9a9a94";

/** Espressione Mapbox: colore dalla PROPRIETA' famiglia, non una coppia per feature. */
const COLORE_PER_FAMIGLIA: any = [
  "match",
  ["get", "family"],
  "permanenti",
  COLORE_PERMANENTI,
  "erbacee",
  COLORE_ERBACEE,
  "seminaturale",
  COLORE_SEMINATURALE,
  COLORE_ALTRO,
];

/**
 * Modalita' "ospiti di un organismo": la mappa ricolora gli appezzamenti per livello
 * ospite (`host_level`, che il servizio aggiunge alle feature quando /parcels riceve
 * `pest=`). E' ESCLUSIVA rispetto alle famiglie e alla coltura dell'utente, cosi' i
 * colori in uso restano tre piu' il campo: dentro il vincolo dei quattro misurato.
 * Niente quinto colore: il magenta della coltura passa alle colture con danno
 * documentato, il giallo delle erbacee alle altre piante ospiti, il grigio al resto.
 */
const COLORE_PER_LIVELLO_OSPITE: ExpressionSpecification = [
  "match",
  ["get", "host_level"],
  "principale",
  COLORE_COLTURA,
  "secondario",
  COLORE_ERBACEE,
  COLORE_ALTRO,
];

export const LEGENDA_OSPITI: Array<{ level: string; label: string; color: string }> = [
  { level: "principale", label: "Colture con danno documentato", color: COLORE_COLTURA },
  { level: "secondario", label: "Altre piante ospiti", color: COLORE_ERBACEE },
  { level: "altro", label: "Non ospiti e non classificabili", color: COLORE_ALTRO },
];

const ETICHETTA_LIVELLO: Record<string, string> = {
  principale: "coltura con danno documentato",
  secondario: "altra pianta ospite",
  non_ospite: "non ospite",
  non_classificabile: "non classificabile",
};

export const LEGENDA_FAMIGLIE: Array<{ family: string; label: string; color: string }> = [
  { family: "permanenti", label: "Frutteti e vigneti", color: COLORE_PERMANENTI },
  { family: "erbacee", label: "Seminativi e prati", color: COLORE_ERBACEE },
  {
    family: "seminaturale",
    label: "Bosco, siepi e margini",
    color: COLORE_SEMINATURALE,
  },
  { family: "altro", label: "Altro", color: COLORE_ALTRO },
];

const SRC_PARCELLE = "landscape-parcels";
const SRC_CAMPO = "landscape-field";
const SRC_BUFFER = "landscape-buffer";
const LYR_AGRI = "landscape-agri-fill";
const LYR_AGRI_LINE = "landscape-agri-line";
const LYR_COLTURA = "landscape-crop-fill";
const LYR_COLTURA_LINE = "landscape-crop-line";

type ParcelsFC = {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    properties: { icolt_class?: string; ha?: number; is_crop?: boolean; host_level?: string };
    geometry: any;
  }>;
};

export type MapLandscapeCropsProps = {
  /** Anello del poligono del campo, [lng, lat][], gia' chiuso. */
  fieldRing: number[][] | null;
  /** Geometria del buffer restituita dal servizio (Polygon GeoJSON). */
  buffer: any | null;
  parcels: ParcelsFC | null;
  /** Classi iColt che raggruppano piu' colture: classe -> cosa contiene. */
  aggregatedClasses: Record<string, string>;
  /** Es. "ARPAE iColt 2026", mostrato in legenda. */
  datasetLabel: string;
  /** Famiglie di uso del suolo accese: una famiglia spenta non si disegna. */
  enabledFamilies: string[];
  showCrop: boolean;
  /** Acceso: colora per livello ospite dell'organismo (richiede feature con `host_level`). */
  hostMode?: boolean;
  /** Nome dell'organismo, per il popup ("ospite della cimice asiatica"). */
  hostModeLabel?: string;
};

const vuoto: ParcelsFC = { type: "FeatureCollection", features: [] };

/** Evita di interpolare stringhe del backend dentro setHTML senza filtro. */
function esc(value: unknown) {
  return String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c] ?? c,
  );
}

export default function MapLandscapeCrops({
  fieldRing,
  buffer,
  parcels,
  aggregatedClasses,
  datasetLabel,
  enabledFamilies,
  showCrop,
  hostMode = false,
  hostModeLabel,
}: MapLandscapeCropsProps) {
  const mapContainerRef = React.useRef<HTMLDivElement>(null);
  const mapRef = React.useRef<any>(null);
  const popupRef = React.useRef<any>(null);
  const [mapLoaded, setMapLoaded] = React.useState(false);

  // I dati piu' recenti, letti dal gestore del click senza ricreare la mappa.
  const aggregatedRef = React.useRef(aggregatedClasses);
  aggregatedRef.current = aggregatedClasses;
  const datasetRef = React.useRef(datasetLabel);
  datasetRef.current = datasetLabel;
  const hostModeRef = React.useRef({ on: hostMode, label: hostModeLabel });
  hostModeRef.current = { on: hostMode, label: hostModeLabel };

  // --- inizializzazione: una volta sola, non dipende dai dati -----------------
  React.useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) {
      return;
    }
    mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_API_TOKEN as string;

    const map = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: "mapbox://styles/mapbox/satellite-streets-v12",
      center: [11.34, 44.49],
      zoom: 11,
    });
    mapRef.current = map;

    map.on("load", () => {
      // --- sorgenti (vuote: i dati arrivano dal secondo effect) ---
      map.addSource(SRC_PARCELLE, { type: "geojson", data: vuoto });
      map.addSource(SRC_BUFFER, { type: "geojson", data: vuoto as any });
      map.addSource(SRC_CAMPO, { type: "geojson", data: vuoto as any });

      // --- tutte le superfici agricole cartografate (contesto) ---
      map.addLayer({
        id: LYR_AGRI,
        type: "fill",
        source: SRC_PARCELLE,
        paint: { "fill-color": COLORE_PER_FAMIGLIA, "fill-opacity": 0.45 },
      });
      map.addLayer({
        id: LYR_AGRI_LINE,
        type: "line",
        source: SRC_PARCELLE,
        paint: {
          "line-color": COLORE_PER_FAMIGLIA,
          "line-width": 0.6,
          "line-opacity": 0.9,
        },
      });

      // --- solo la coltura dell'utente, sopra il contesto ---
      map.addLayer({
        id: LYR_COLTURA,
        type: "fill",
        source: SRC_PARCELLE,
        filter: ["==", ["get", "is_crop"], true],
        paint: { "fill-color": COLORE_COLTURA, "fill-opacity": 0.6 },
      });
      map.addLayer({
        id: LYR_COLTURA_LINE,
        type: "line",
        source: SRC_PARCELLE,
        filter: ["==", ["get", "is_crop"], true],
        paint: { "line-color": COLORE_COLTURA, "line-width": 1.4 },
      });

      // --- bordo del buffer: l'area su cui i numeri sono calcolati ---
      map.addLayer({
        id: "landscape-buffer-line",
        type: "line",
        source: SRC_BUFFER,
        paint: {
          "line-color": "#FFFFFF",
          "line-width": 1.5,
          "line-dasharray": [3, 2],
          "line-opacity": 0.9,
        },
      });

      // --- il campo dell'utente, sempre in cima ---
      map.addLayer({
        id: "landscape-field-fill",
        type: "fill",
        source: SRC_CAMPO,
        paint: { "fill-color": COLORE_CAMPO, "fill-opacity": 0.25 },
      });
      map.addLayer({
        id: "landscape-field-line",
        type: "line",
        source: SRC_CAMPO,
        paint: { "line-color": COLORE_CAMPO, "line-width": 2.5 },
      });

      // --- interrogazione al click, registrata sui layer ---
      popupRef.current = new mapboxgl.Popup({ closeButton: true, closeOnClick: true });
      const onClick = (e: any) => {
        const f = e.features?.[0];
        if (!f) {
          return;
        }
        const classe = String(f.properties?.icolt_class ?? "-");
        const ha = Number(f.properties?.ha ?? 0);
        const contenuto = aggregatedRef.current?.[classe];
        const nota = contenuto
          ? `<div class="font-s opacity-05 mt-1">Classe collettiva: comprende ${esc(
              contenuto,
            )}. Il dato non distingue la singola coltura.</div>`
          : "";
        const livello = f.properties?.host_level
          ? String(f.properties.host_level)
          : null;
        const rigaOspite =
          livello && hostModeRef.current.on
            ? `<div class="font-s mt-1">${esc(
                hostModeRef.current.label ?? "Organismo",
              )}: ${esc(ETICHETTA_LIVELLO[livello] ?? livello)}</div>`
            : "";
        popupRef.current
          .setLngLat(e.lngLat)
          .setHTML(
            `<div class="llist-group">
               <div class="font-m-600">${esc(classe)}</div>
               <div class="font-s">${ha.toLocaleString("it-IT", {
                 maximumFractionDigits: 2,
               })} ha nel raggio</div>
               ${nota}
               ${rigaOspite}
               <div class="font-s opacity-05 mt-1">${esc(datasetRef.current)}</div>
             </div>`,
          )
          .addTo(map);
      };
      [LYR_COLTURA, LYR_AGRI].forEach((id) => {
        map.on("click", id, onClick);
        map.on("mouseenter", id, () => {
          map.getCanvas().style.cursor = "pointer";
        });
        map.on("mouseleave", id, () => {
          map.getCanvas().style.cursor = "";
        });
      });

      setMapLoaded(true);
    });

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
      setMapLoaded(false);
    };
  }, []);

  // --- aggiornamento dei dati: non ricrea la mappa ----------------------------
  React.useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) {
      return;
    }

    map.getSource(SRC_PARCELLE)?.setData(parcels ?? vuoto);

    if (buffer) {
      map.getSource(SRC_BUFFER)?.setData({
        type: "Feature",
        properties: {},
        geometry: buffer,
      });
    }

    if (fieldRing && fieldRing.length >= 4) {
      map.getSource(SRC_CAMPO)?.setData({
        type: "Feature",
        properties: {},
        geometry: { type: "Polygon", coordinates: [fieldRing] },
      });
    }

    // Il fit e' sul BUFFER, non sul campo: l'area di interesse e' l'intorno.
    try {
      const target = buffer
        ? turf.bbox(turf.feature(buffer) as any)
        : fieldRing && fieldRing.length >= 4
          ? turf.bbox(turf.polygon([fieldRing]))
          : null;
      if (target) {
        map.fitBounds(target as any, { padding: 24, duration: 0 });
      }
    } catch {
      // Geometria inattesa: si resta sulla vista corrente invece di rompere la pagina.
    }
  }, [mapLoaded, parcels, buffer, fieldRing]);

  // --- accensione e spegnimento dei layer ------------------------------------
  React.useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) {
      return;
    }
    const set = (id: string, on: boolean) =>
      map.setLayoutProperty(id, "visibility", on ? "visible" : "none");
    // Le famiglie spente escono dal filtro: un solo layer serve tutte le voci
    // della legenda, senza duplicare la sorgente per ogni famiglia.
    if (hostMode) {
      // Modalita' ospiti: tutti gli appezzamenti, colorati per livello; la coltura
      // dell'utente si spegne perche' il suo colore ora dice "danno documentato".
      map.setFilter(LYR_AGRI, null);
      map.setFilter(LYR_AGRI_LINE, null);
      map.setPaintProperty(LYR_AGRI, "fill-color", COLORE_PER_LIVELLO_OSPITE);
      map.setPaintProperty(LYR_AGRI_LINE, "line-color", COLORE_PER_LIVELLO_OSPITE);
      set(LYR_AGRI, true);
      set(LYR_AGRI_LINE, true);
      set(LYR_COLTURA, false);
      set(LYR_COLTURA_LINE, false);
      return;
    }
    map.setPaintProperty(LYR_AGRI, "fill-color", COLORE_PER_FAMIGLIA);
    map.setPaintProperty(LYR_AGRI_LINE, "line-color", COLORE_PER_FAMIGLIA);
    const filtroFamiglie: FilterSpecification = [
      "in",
      ["get", "family"],
      ["literal", enabledFamilies],
    ];
    map.setFilter(LYR_AGRI, filtroFamiglie);
    map.setFilter(LYR_AGRI_LINE, filtroFamiglie);
    set(LYR_AGRI, enabledFamilies.length > 0);
    set(LYR_AGRI_LINE, enabledFamilies.length > 0);
    set(LYR_COLTURA, showCrop);
    set(LYR_COLTURA_LINE, showCrop);
  }, [mapLoaded, enabledFamilies, showCrop, hostMode]);

  return (
    <div className="map-observations-wrapper">
      <div ref={mapContainerRef} className="map-observations"></div>
    </div>
  );
}
