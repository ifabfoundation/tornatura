import React from "react";
import mapboxgl from "mapbox-gl";
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
const COLORE_CAMPO = "#EAFF00";
const COLORE_COLTURA = "#e87ba4";
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
    properties: { icolt_class?: string; ha?: number; is_crop?: boolean };
    geometry: any;
  }>;
};

export type MapLandscapeCropsProps = {
  /** Anello del poligono del campo, [lng, lat][], gia' chiuso. */
  fieldRing: number[][] | null;
  /** Geometria del buffer restituita dal servizio (Polygon GeoJSON). */
  buffer: any | null;
  parcels: ParcelsFC | null;
  /** Etichetta della classe iColt della coltura dell'utente, se mappabile. */
  cropLabel: string | null;
  /** Classi iColt che raggruppano piu' colture: classe -> cosa contiene. */
  aggregatedClasses: Record<string, string>;
  /** Es. "ARPAE iColt 2026", mostrato in legenda. */
  datasetLabel: string;
  showAgri: boolean;
  showCrop: boolean;
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
  cropLabel,
  aggregatedClasses,
  datasetLabel,
  showAgri,
  showCrop,
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
        popupRef.current
          .setLngLat(e.lngLat)
          .setHTML(
            `<div class="llist-group">
               <div class="font-m-600">${esc(classe)}</div>
               <div class="font-s">${ha.toLocaleString("it-IT", {
                 maximumFractionDigits: 2,
               })} ha nel raggio</div>
               ${nota}
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
    set(LYR_AGRI, showAgri);
    set(LYR_AGRI_LINE, showAgri);
    set(LYR_COLTURA, showCrop);
    set(LYR_COLTURA_LINE, showCrop);
  }, [mapLoaded, showAgri, showCrop]);

  return (
    <div className="map-observations-wrapper">
      <div ref={mapContainerRef} className="map-observations"></div>
      <div className="map-legend">
        <div className="llist-group">
          <div className="llist-group-item p-0 h-s d-flex align-items-center">
            <div className="dot me-2" data-size="12" style={{ background: COLORE_CAMPO }}></div>
            <span className="font-s">Il tuo campo</span>
          </div>
          {cropLabel && (
            <div className="llist-group-item p-0 h-s d-flex align-items-center">
              <div
                className="dot me-2"
                data-size="12"
                style={{ background: COLORE_COLTURA }}
              ></div>
              <span className="font-s">{cropLabel}</span>
            </div>
          )}
          {LEGENDA_FAMIGLIE.map((f) => (
            <div
              key={f.family}
              className="llist-group-item p-0 h-s d-flex align-items-center"
            >
              <div className="dot me-2" data-size="12" style={{ background: f.color }}></div>
              <span className="font-s">{f.label}</span>
            </div>
          ))}
          <div className="llist-group-item p-0 h-s">
            <span className="font-s opacity-05">{datasetLabel}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
