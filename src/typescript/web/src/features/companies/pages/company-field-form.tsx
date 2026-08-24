import React, { Fragment } from "react";
import { useFormik } from "formik";
import * as Yup from "yup";
import mapboxgl from "mapbox-gl";
import { LandscapePiece, fetchLandscapePieces } from "../../../services/model-api";
import type {
  Feature,
  FeatureCollection,
  Geometry,
  MultiPolygon,
  Polygon,
} from "geojson";
import MapboxLanguage from "@mapbox/mapbox-gl-language";
import { SearchBox } from "@mapbox/search-js-react";
import MapboxDraw from "@mapbox/mapbox-gl-draw";
import { AgriFieldMutationPayload, Point } from "@tornatura/coreapis";
import { useNavigate, useParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { companiesSelectors } from "../state/companies-slice";
import { harvestTypesSelectors } from "../../harvest-types/state/harvest-types-slice";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { fieldsActions } from "../../fields/state/fields-slice";
import * as turf from "@turf/turf";
import { gpsStore } from "../../../providers/gps-providers";
import { Col, Container, Row } from "react-bootstrap";
import Icon from "../../../components/Icon";

/**
 * Quel che il passo del disegno consegna al passo dei dettagli. Prima era il solo
 * elenco di punti; ora porta anche la coltura, quando il confine viene da un pezzo
 * dichiarato e la sua specie corrisponde a una coltura del registro.
 */
type DisegnoCompletato = {
  map: Point[];
  harvest: string | null;
};

interface FieldProps {
  formData: AgriFieldMutationPayload;
  action: string;
  onBackClick?: () => Promise<void>;
  onNextClick: (data: any) => Promise<void>;
}

const calcArea = (points: Point[]) => {
  const coords: number[][] = [];
  points.forEach((p) => coords.push([p.lng, p.lat]));
  var polygon = turf.polygon([coords]);
  var areaSqm = turf.area(polygon);
  var areaHe = areaSqm / 10000; // Convert to hectares
  return parseFloat(areaHe.toFixed(2));
};

/** Un pezzo dichiarato scelto dall'utente per comporre il campo. */
type PezzoScelto = {
  pid: number;
  appId: number;
  /** Quanti pezzi ha in tutto il campo dichiarato a cui questo appartiene. */
  appN: number;
  ha: number;
  crop: string;
  harvestCode: string | null;
  geometry: Polygon | MultiPolygon;
};

/** Il contorno che si puo' davvero salvare, piu' cio' che si e' perso per farlo. */
type Contorno = {
  /** Anello chiuso, nella forma che `AgriFieldModel.map` puo' contenere. */
  ring: number[][];
  /** Superficie dell'anello: e' quella che finira' nel database. */
  ha: number;
  /** Somma delle superfici dichiarate dei pezzi scelti. */
  haPezzi: number;
  /** Parti staccate scartate perche' il campo ha un contorno solo. */
  partiScartate: number;
  /** Vuoti reali inglobati nell'anello, in metri quadri. */
  vuotiM2: number;
};

/**
 * Un buco nell'unione dei pezzi puo' essere due cose diverse, e vanno distinte
 * perche' solo la seconda va detta all'utente:
 *
 *   FESSURA   una scheggia fra due bordi che non combaciano perfettamente. Sono
 *             artefatti del dato AGREA, non del nostro calcolo: verificato con un
 *             A/B a precisione piena, 9 e 7 decimali, dove la quota di coppie con
 *             fessura resta identica (pianura 7,7% / 7,8% / 7,5%; collina 32,1% /
 *             31,7% / 33,6%).
 *   VUOTO     un'area davvero non dichiarata dentro il campo: un'aia, un
 *             fabbricato, un laghetto.
 *
 * Si separano con due criteri, perche' la superficie da sola non basta: la misura
 * e la compattezza 4*pi*area/perimetro^2, che vale 1 per un cerchio e tende a 0
 * per una scheggia. Misurato su 765 buchi in tre zone: l'88% sta sotto 100 m2, e
 * dei 93 sopra soglia solo 6 sono schegge (compattezza sotto 0,10). Con i due
 * criteri insieme il messaggio all'utente e' esatto in tutti i casi misurati.
 *
 * Nota: qualunque sia la classificazione, il contorno salvato e' sempre il solo
 * anello esterno, perche' il database non puo' contenere buchi. Questi due numeri
 * servono a DIRLO, non a cambiare la geometria.
 */
const VUOTO_MIN_M2 = 100;
const VUOTO_MIN_COMPATTEZZA = 0.1;

/**
 * Vero se la coltura dichiarata su un pezzo e' fra quelle che tornatura gestisce.
 *
 * L'autorita' e' il registro colture del database (`harvest_type`), lo stesso che
 * riempie il menu della coltura al passo successivo: aggiungerne una li' la rende
 * selezionabile qui senza toccare questo file. Perche' un pezzo arrivi con un
 * codice serve anche la riga corrispondente in `HARVEST_TO_AGREA_SPECIES`
 * (`landscape/modules/config.py`), che dice quale specie AGREA e' quella coltura:
 * quel raccordo nessuno puo' derivarlo, va scritto.
 *
 * Si apre invece di chiudere quando il registro non e' ancora arrivato dal
 * server: una corsa in caricamento non deve rendere la mappa inutilizzabile.
 */
const colturaRegistrabile = (
  harvestCode: string | null,
  permesse: Set<string>,
): boolean => (permesse.size === 0 ? true : !!harvestCode && permesse.has(harvestCode));

/** Vero se il buco e' un vuoto reale e non una scheggia fra due bordi. */
const vuotoReale = (anello: number[][]): boolean => {
  const poligono = turf.polygon([anello]);
  const area = turf.area(poligono);
  if (area < VUOTO_MIN_M2) {
    return false;
  }
  const perimetro = turf.length(turf.polygonToLine(poligono), { units: "meters" });
  if (perimetro <= 0) {
    return false;
  }
  return (4 * Math.PI * area) / (perimetro * perimetro) >= VUOTO_MIN_COMPATTEZZA;
};

/**
 * Da una feature della mappa al pezzo scelto. Il tipo del parametro e' volutamente
 * larghi: la stessa funzione riceve le feature degli eventi mapbox e quelle
 * arrivate dal servizio, che mapbox e geojson tipizzano in modo diverso.
 */
const pezzoDaFeature = (f: {
  properties: Record<string, unknown> | null;
  geometry: Geometry;
}): PezzoScelto => ({
  pid: Number(f.properties?.pid),
  appId: Number(f.properties?.app_id),
  appN: Number(f.properties?.app_n ?? 1),
  ha: Number(f.properties?.ha ?? 0),
  crop: String(f.properties?.crop ?? ""),
  harvestCode: (f.properties?.harvest_code as string) || null,
  geometry: f.geometry as Polygon | MultiPolygon,
});

/**
 * Unisce i pezzi scelti e riduce il risultato a cio' che il database accetta.
 *
 * `AgriFieldModel.map` e' una lista piatta di punti, cioe' UN anello: niente
 * parti staccate, niente buchi. La riduzione e' quindi obbligata, ma cio' che si
 * perde deve essere detto e non sparire in silenzio — prima veniva scartato senza
 * avvisi e su un campo dichiarato su cinque si perdeva fino al 70% della
 * superficie.
 *
 * Misurato sul dato vero: unendo i pezzi adiacenti di uno stesso campo, il 94,2%
 * delle unioni e' un solo poligono e il 90,6% non ha vuoti reali.
 */
const contornoDaPezzi = (pezzi: PezzoScelto[]): Contorno | null => {
  if (pezzi.length === 0) {
    return null;
  }
  let unito: Feature<Polygon | MultiPolygon> | null = null;
  if (pezzi.length === 1) {
    // `turf.union` pretende ALMENO DUE geometrie e con una sola solleva
    // "Must have at least 2 geometries". Con un pezzo solo l'unione e' il pezzo
    // stesso e non c'e' niente da unire.
    unito = turf.feature(pezzi[0].geometry);
  } else {
    try {
      unito = turf.union(
        turf.featureCollection(pezzi.map((x) => turf.feature(x.geometry))),
      );
    } catch {
      // Un'unione che non riesce non deve impedire di disegnare a mano.
      return null;
    }
  }
  if (!unito?.geometry) {
    return null;
  }
  const parti: number[][][][] =
    unito.geometry.type === "MultiPolygon"
      ? unito.geometry.coordinates
      : [unito.geometry.coordinates];

  // La parte piu' grande diventa il campo: le altre si perdono, e si contano.
  let scelta = parti[0];
  let areaScelta = -1;
  parti.forEach((parte) => {
    const a = turf.area(turf.polygon(parte));
    if (a > areaScelta) {
      areaScelta = a;
      scelta = parte;
    }
  });

  const vuotiM2 = scelta
    .slice(1)
    .filter(vuotoReale)
    .map((anello) => turf.area(turf.polygon([anello])))
    .reduce((somma, a) => somma + a, 0);

  return {
    ring: scelta[0],
    ha: Number((turf.area(turf.polygon([scelta[0]])) / 10000).toFixed(2)),
    haPezzi: Number(pezzi.reduce((somma, x) => somma + x.ha, 0).toFixed(2)),
    partiScartate: parti.length - 1,
    vuotiM2: Math.round(vuotiM2),
  };
};

export function FieldFormInfo({ formData, action, onNextClick, onBackClick }: FieldProps) {
  const harvestTypes = useAppSelector(harvestTypesSelectors.selectActiveHarvestTypes);
  const formik = useFormik({
    initialValues: {
      name: "",
      description: "",
      // Precompilata dal pezzo scelto al passo precedente, quando la coltura
      // dichiarata corrisponde a una del registro. Resta modificabile: il dato
      // AGREA descrive la campagna in corso, non necessariamente cio' che
      // l'utente sta registrando.
      harvest: formData.harvest ?? "",
      area: 0.0,
      areafrom: "map",
      plants: 0,
      variety: "",
      irrigation: "",
      weaving: "",
      rotation: "",
      grassing: "",
      year: "",
    },
    validationSchema: Yup.object({
      name: Yup.string().required("Campo necessario"),
      harvest: Yup.string().required("Campo necessario"),
      area: Yup.number()
        .typeError("Il valore inserito non è positivo")
        .min(0, "Il valore deve essere positivo")
        .required("Campo necessario"),
      variety: Yup.string().required("Campo necessario"),
      irrigation: Yup.string().required("Campo necessario"),
      weaving: Yup.string().required("Campo necessario"),
      rotation: Yup.string().required("Campo necessario"),
      grassing: Yup.string().required("Campo necessario"),
    }),
    onSubmit: async (values, { setSubmitting, setErrors }) => {
      setSubmitting(true);
      if (values.areafrom === "map") {
        values.area = calcArea(formData.map);
      }
      if (values.rotation === "no" && !values.year) {
        setErrors({ year: "Specificare l'anno di impianto" });
        setSubmitting(false);
        return;
      } else if (values.rotation === "si") {
        values.year = "";
      }
      await onNextClick(values);
      setSubmitting(false);
    },
  });

  React.useEffect(() => {
    formik.setValues({
      name: formData.name,
      description: formData.description,
      harvest: formData.harvest,
      area: formData.area,
      areafrom: "map",
      plants: formData.plants || 0,
      variety: formData.variety,
      irrigation: formData.irrigation,
      weaving: formData.weaving,
      rotation: formData.rotation,
      grassing: formData.grassing,
      year: "",
    });
  }, [formData]);

  const form_options_rotazione = {
    si: "Sì",
    no: "No",
  };
  const form_options_dimensione = {
    map: "Calcolo automatico dalla mappa",
    manual: "Manuale",
  };
  const form_options_irrigazione = {
    scorrimento: "A scorrimento",
    pioggia: "A pioggia",
    goccia: "A goccia",
    "n/a": "Non applicabile"
  };
  const form_options_inerbimento = {
    misto_spoglio: "Misto / Spoglio",
    brassicaceae: "Brassicaceae",
    graminaceae: "Graminaceae",
    fabaceae: "Fabaceae",
    "n/a": "Non applicabile"
  };
  const form_options_tessitura = {
    misto: "Misto",
    argilla: "Argilla",
    sabbia: "Sabbia",
    limo: "Limo",
  };

  return (
    <form onSubmit={formik.handleSubmit} autoComplete="off">
      <div className="form-section">
        <div className="container px-0">
          <div className="row">
            <div className="col mb-4">
              <h4>
                <strong>Dettagli del Campo</strong>
              </h4>
            </div>
          </div>
          <div className="row input-row">
            <div className="col">
              <label>
                Nome
                <input
                  id="FIELD_1"
                  name="name"
                  type="text"
                  placeholder="Nome del campo"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.name}
                />
              </label>
              {formik.touched.name && formik.errors.name ? (
                <div className="error">{formik.errors.name}</div>
              ) : null}
            </div>
          </div>
          <div className="row input-row">
            <div className="col-md-6 input-row-margin-fix">
              <label>
                Coltura
                <select
                  id="FIELD_2"
                  name="harvest"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.harvest}
                >
                  <option value="" disabled>
                    Scegli la coltura
                  </option>
                  {harvestTypes.map((item) => (
                    <option key={item.id} value={item.code}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </label>
              {formik.touched.harvest && formik.errors.harvest ? (
                <div className="error">{formik.errors.harvest}</div>
              ) : null}
            </div>
            <div className="col-md-6 input-row-margin-fix">
              <label>
                Varietà/Cultivar
                <input
                  id="FIELD_3"
                  name="variety"
                  type="text"
                  placeholder="Indica la varietà o cultivar"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.variety}
                />
              </label>
              {formik.touched.variety && formik.errors.variety ? (
                <div className="error">{formik.errors.variety}</div>
              ) : null}
            </div>
          </div>
          <div className="row input-row">
            <div className="col-md-6 input-row-margin-fix">
              <label>
                Rotazione
                <select
                  id="FIELD_4"
                  name="rotation"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.rotation}
                >
                  <option value="" disabled>
                    Scegli...
                  </option>
                  {Object.entries(form_options_rotazione).map(([key, label]) => (
                    <option key={key} value={key}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              {formik.touched.rotation && formik.errors.rotation ? (
                <div className="error">{formik.errors.rotation}</div>
              ) : null}
            </div>
            <div className="col-md-6 input-row-margin-fix">
              <label>
                Anno di impianto
                <input
                  id="FIELD_5"
                  name="year"
                  type="text"
                  // placeholder="[SOLO SE ROTAZIONE = NO]"
                  placeholder="Anno"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  disabled={formik.values.rotation === "si"}
                  value={formik.values.rotation === "no" ? formik.values.year : ""}
                />
              </label>
              {formik.touched.rotation && formik.errors.year ? (
                <div className="error">{formik.errors.year}</div>
              ) : null}
            </div>
          </div>
          <div className="row input-row">
            <div className="col-md-6 input-row-margin-fix">
              <label>
                Dimensione del campo
                <select
                  id="FIELD_6"
                  name="areafrom"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.areafrom}
                >
                  <option value="" disabled>
                    Scegli il metodo di inserimento
                  </option>
                  {Object.entries(form_options_dimensione).map(([key, label]) => (
                    <option key={key} value={key}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              {formik.touched.areafrom && formik.errors.areafrom ? (
                <div className="error">{formik.errors.areafrom}</div>
              ) : null}
            </div>
            <div className="col-md-6 input-row-margin-fix">
              <label>
                Dimensione in ettari
                <input
                  id="FIELD_7"
                  name="area"
                  type="text"
                  min={0}
                  // placeholder="[NON MODIFICABILE SE CALCOLO AUTOMATICO]"
                  placeholder="He"
                  disabled={formik.values.areafrom === "map"}
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={
                    formik.values.areafrom === "manual"
                      ? formik.values.area
                      : calcArea(formData.map)
                  }
                />
              </label>
              {formik.touched.area && formik.errors.area ? (
                <div className="error">{formik.errors.area}</div>
              ) : null}
            </div>
          </div>
          <div className="row input-row">
            <div className="col-md-6 input-row-margin-fix">
              <label>
                Numero di piante
                <input
                  id="FIELD_8"
                  name="plants"
                  type="text"
                  placeholder="Numero di piante"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.plants}
                />
              </label>
              {formik.touched.plants && formik.errors.plants ? (
                <div className="error">{formik.errors.plants}</div>
              ) : null}
            </div>
            <div className="col-md-6 input-row-margin-fix">
              <label>
                Irrigazione
                <select
                  id="FIELD_9"
                  name="irrigation"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.irrigation}
                >
                  <option value="" disabled>
                    Scegli il tipo di irrigazione
                  </option>
                  {Object.entries(form_options_irrigazione).map(([key, label]) => (
                    <option key={key} value={key}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              {formik.touched.irrigation && formik.errors.irrigation ? (
                <div className="error">{formik.errors.irrigation}</div>
              ) : null}
            </div>
          </div>
          <div className="row input-row">
            <div className="col-md-6 input-row-margin-fix">
              <label>
                Inerbimento
                <select
                  id="FIELD_10"
                  name="grassing"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.grassing}
                >
                  <option value="" disabled>
                    Scegli il tipo di inerbimento
                  </option>
                  {Object.entries(form_options_inerbimento).map(([key, label]) => (
                    <option key={key} value={key}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              {formik.touched.grassing && formik.errors.grassing ? (
                <div className="error">{formik.errors.grassing}</div>
              ) : null}
            </div>
            <div className="col-md-6 input-row-margin-fix">
              <label>
                Tessitura
                <select
                  id="FIELD_11"
                  name="weaving"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.weaving}
                >
                  <option value="" disabled>
                    Scegli la tessitura del suolo
                  </option>
                  {Object.entries(form_options_tessitura).map(([key, label]) => (
                    <option key={key} value={key}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              {formik.touched.weaving && formik.errors.weaving ? (
                <div className="error">{formik.errors.weaving}</div>
              ) : null}
            </div>
          </div>
          <div className="row input-row">
            <div className="col">
              <label>
                Descrizione
                <textarea
                  id="FIELD_12"
                  name="description"
                  rows={15}
                  cols={50}
                  placeholder="Descrizione del campo"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.description}
                />
              </label>
              {formik.touched.description && formik.errors.description ? (
                <div className="error">{formik.errors.description}</div>
              ) : null}
            </div>
          </div>
        </div>
      </div>
      <div className="buttons-wrapper mt-4 text-center">
        <button className="trnt_btn secondary" onClick={onBackClick}>
          Indietro
        </button>
        <button type="submit" className="trnt_btn primary" disabled={formik.isSubmitting}>
          {formik.isSubmitting ? "Caricamento..." : action}
        </button>
      </div>

      <div className="spacer my-5"></div>
    </form>
  );
}

/**
 * Zoom da cui si caricano i pezzi scegliibili della vista.
 *
 * Scelto su quando il contorno diventa VISIBILE, non a sentimento: a latitudine
 * 44,5 e su uno schermo da 390 px, a zoom 13 la vista copre 5,3 km e un pezzo di
 * 1,4 ha misura 9 pixel di lato — riconoscibile; a zoom 12 ne misurerebbe 4.
 *
 * Il raggio si calcola dai confini REALI della vista invece di indovinarlo per
 * dispositivo: il campo si disegna quasi sempre da PC, dove la vista e' molto piu'
 * larga che su telefono. Il tetto e' quello dell'endpoint: il layer fine e' 1,54x
 * i poligoni e 2,40x i vertici di quello del paesaggio.
 */
const PEZZI_ZOOM_MIN = 13;
const PEZZI_RAGGIO_MAX_M = 3000;
/**
 * Il raggio non scende sotto questo valore: a zoom alto la mezza diagonale della
 * vista diventa piccolissima, e sotto il minimo accettato dall'endpoint la
 * richiesta tornerebbe 422 lasciando la mappa senza pezzi proprio quando si sta
 * mirando a un pezzo piccolo. Deve restare >= AGREA_PIECES_MIN_RADIUS_M.
 */
const PEZZI_RAGGIO_MIN_M = 250;

/**
 * Quanti pezzi scelti si elencano uno per uno, con il loro cestino. "Tutto il
 * campo" puo' aggiungerne molti — il massimo misurato in regione e' 46 — e senza
 * un tetto l'elenco sfonderebbe lo schermo. Oltre il tetto si togliono cliccando
 * il pezzo sulla mappa.
 */
const PEZZI_IN_ELENCO = 6;

/**
 * I pannelli galleggianti stanno a 5rem, cioe' esattamente nello spazio in cui si
 * apre la tendina degli indirizzi della casella di ricerca.
 *
 * Non si risolve con lo z-index: `@mapbox/search-js-web` attacca la tendina a
 * `document.body` (`document.body.appendChild(this.listbox)`), quindi non e' nel
 * sottoalbero del wrapper e alzare lo z-index del wrapper non la solleverebbe. La
 * via affidabile e' non disegnare i pannelli mentre la ricerca e' in uso: chi sta
 * scrivendo un indirizzo non ha bisogno di leggere come si scelgono i pezzi.
 */
const STILE_PANNELLO: React.CSSProperties = { top: "5rem" };

export const FieldFormMap = ({ action, onNextClick }: FieldProps) => {
  const currentPosition = React.useContext(gpsStore);
  const mapContainerRef = React.useRef<HTMLDivElement>(null);
  const mapRef = React.useRef<any>(null);
  const [mapLoaded, setMapLoaded] = React.useState(false);
  const [inputValue, setInputValue] = React.useState("");
  /** Vero mentre si scrive nella casella di ricerca: i pannelli si ritirano. */
  const [ricercaAttiva, setRicercaAttiva] = React.useState(false);
  const [map, setMap] = React.useState<Point[]>([]);

  // --- scelta del confine dai pezzi dichiarati AGREA -------------------------
  // Il disegno a mano resta esattamente come prima: questo si aggiunge sopra e
  // non lo sostituisce mai. I pezzi mancano spesso (l'azienda puo' non presentare
  // il piano colturale, i pezzi possono stare sotto la soglia minima, il punto
  // puo' cadere fuori dalla copertura) e la loro assenza non deve mai impedire di
  // procedere.
  const drawRef = React.useRef<any>(null);
  /** Il pezzo sotto il cursore: e' solo un'anteprima e non tocca la scelta. */
  const [anteprima, setAnteprima] = React.useState<PezzoScelto | null>(null);
  /**
   * Il pezzo con una coltura che tornatura non gestisce, su cui si e' cliccato
   * comunque. Non entra nella scelta: apre una richiesta di conferma. Serve al
   * caso legittimo dell'impianto nuovo, perche' AGREA dichiara la campagna in
   * corso e un pereto appena piantato risulta ancora seminativo.
   */
  const [daForzare, setDaForzare] = React.useState<PezzoScelto | null>(null);
  /** I pezzi scelti col click. Il cursore che si muove non li cambia. */
  const [selezione, setSelezione] = React.useState<PezzoScelto[]>([]);
  const [contornoUsato, setContornoUsato] = React.useState(false);
  /** I pezzi caricati per la vista corrente. */
  const [pezzi, setPezzi] = React.useState<LandscapePiece[]>([]);
  /**
   * Se la vista e' larga il servizio serve solo i pezzi piu' grandi, perche' la
   * risposta ha un tetto sui vertici. Qui si tiene la misura minima servita, per
   * poterla dire: senza, sembrerebbe che i campi piccoli non esistano.
   */
  const [sogliaServita, setSogliaServita] = React.useState<number | null>(null);
  /**
   * Vero finche' la vista e' troppo larga per caricare i pezzi. Serve a non
   * confondere due situazioni molto diverse nel messaggio: "non abbiamo ancora
   * guardato" e "qui non c'e' nessun confine dichiarato".
   */
  const [vistaLarga, setVistaLarga] = React.useState(true);
  // Centro e raggio dei pezzi caricati: serve a non ricaricarli a ogni piccolo
  // spostamento della mappa.
  const vicinatoRef = React.useRef<{ lat: number; lng: number; r: number } | null>(null);

  /**
   * Le colture registrabili, dal registro del database. E' la stessa lista del
   * menu al passo 2: una sola verita', nessun elenco duplicato nel codice.
   */
  const harvestTypes = useAppSelector(harvestTypesSelectors.selectActiveHarvestTypes);
  const colturePermesse = React.useMemo(
    () => new Set(harvestTypes.map((h) => h.code)),
    [harvestTypes],
  );

  /** Il contorno salvabile, ricalcolato solo quando la scelta cambia. */
  const contorno = React.useMemo(() => contornoDaPezzi(selezione), [selezione]);

  /**
   * Quanti campi dichiarati diversi tocca la scelta. Se sono piu' di uno, il
   * varco fra loro e' normale e va spiegato: fra due campi dichiarati c'e' quasi
   * sempre una striscia non coltivata. Misurato in pianura: due pezzi dello STESSO
   * campo si toccano esatti nel 93-96% dei casi, mentre fra campi diversi solo il
   * 24% si tocca e gli altri distano 5,2-5,6 m in mediana.
   */
  const campiDistinti = React.useMemo(
    () => new Set(selezione.map((x) => x.appId)).size,
    [selezione],
  );

  /**
   * La coltura del confine effettivamente usato, da consegnare al passo 2. Va
   * tenuta a parte perche' `usaContorno` svuota la scelta, e con essa andrebbe
   * perso anche `colturaScelta`.
   */
  const [colturaDalDato, setColturaDalDato] = React.useState<string | null>(null);

  /** Riporta la scelta allo stato iniziale, senza toccare il disegno a mano. */
  const azzeraScelta = React.useCallback(() => {
    setSelezione([]);
    setDaForzare(null);
    setAnteprima(null);
  }, []);

  /** La coltura da preselezionare: solo se tutti i pezzi scelti concordano. */
  const colturaScelta = React.useMemo(() => {
    const codici = new Set(selezione.map((x) => x.harvestCode || ""));
    return codici.size === 1 ? selezione[0]?.harvestCode || null : null;
  }, [selezione]);

  /**
   * Quanti altri pezzi degli stessi campi dichiarati sono nella vista e non
   * ancora scelti. Serve al pulsante "Tutto il campo", e a dire quanti sono.
   */
  const fratelliNellaVista = React.useMemo(() => {
    if (selezione.length === 0) {
      return 0;
    }
    const campi = new Set(selezione.map((x) => x.appId));
    const scelti = new Set(selezione.map((x) => x.pid));
    return pezzi.filter(
      (f) =>
        campi.has(Number(f.properties?.app_id)) &&
        !scelti.has(Number(f.properties?.pid)),
    ).length;
  }, [selezione, pezzi]);

  React.useEffect(() => {
    if (mapLoaded && currentPosition) {
      const source = mapRef.current!.getSource("current-location") as mapboxgl.GeoJSONSource;

      if (source) {
        source.setData({
          type: "Feature",
          geometry: {
            type: "Point",
            coordinates: [currentPosition.lng, currentPosition.lat],
          },
          properties: {},
        });
      }
    }
  }, [mapLoaded, currentPosition]);

  React.useEffect(() => {
    if (mapContainerRef.current) {
      mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_API_TOKEN;

      mapRef.current = new mapboxgl.Map({
        container: mapContainerRef.current,
        style: "mapbox://styles/mapbox/satellite-streets-v12",
        center:
          currentPosition && currentPosition.lng && currentPosition.lat
            ? [currentPosition.lng, currentPosition.lat]
            : [12.5736108, 41.29246],
        zoom: 9,
      });
      mapRef.current.addControl(new MapboxLanguage({ defaultLanguage: "it" }));

      const draw = new MapboxDraw({
        displayControlsDefault: false,
        controls: {
          polygon: true,
          trash: true,
        },
        // Si parte in SELEZIONE, non in disegno: il click serve a scegliere il
        // confine dichiarato, che e' la strada piu' breve e piu' precisa. Chi
        // vuole tracciarlo a mano preme il pulsante del poligono, e da quel
        // momento il click sui pezzi viene ignorato: non si toglie all'utente lo
        // strumento che ha scelto.
        defaultMode: "simple_select",
      });

      mapRef.current.on("load", () => {
        mapRef.current!.addSource("current-location", {
          type: "geojson",
          data: {
            type: "Feature",
            geometry: { type: "Point", coordinates: [0, 0] },
          },
        });

        mapRef.current!.addLayer({
          id: "current-location-dot",
          type: "circle",
          source: "current-location",
          paint: {
            "circle-radius": 5,
            "circle-color": "#007AFF",
            "circle-opacity": 1,
          },
        });

        mapRef.current!.addLayer({
          id: "current-location-pulse",
          type: "circle",
          source: "current-location",
          paint: {
            "circle-radius": 5,
            "circle-color": "#007AFF",
            "circle-opacity": 0,
            "circle-radius-transition": { duration: 0, delay: 0 },
            "circle-opacity-transition": { duration: 0, delay: 0 },
          },
        });

        function animatePulse(startTime: number) {
          const t = (performance.now() - startTime) / 1000;
          const cycle = 2; // seconds per pulse
          const minRadius = 5;
          const maxRadius = 40;
          const maxOpacity = 0.8;

          // Instead of one pulse, compute multiple overlapping pulses
          const pulses = 3; // number of simultaneous ripples
          const radii: number[] = [];
          const opacities: number[] = [];

          for (let i = 0; i < pulses; i++) {
            const offset = i * (cycle / pulses);
            const progress = ((t - offset) % cycle) / cycle;

            const radius = minRadius + progress * (maxRadius - minRadius);
            const opacity = maxOpacity * (1 - progress);

            radii.push(radius);
            opacities.push(opacity);
          }

          // Use the largest radius and highest opacity for the layer
          // (or dynamically create multiple layers if you want all visible)
          const radius = radii[0];
          const opacity = opacities[0];

          if (mapRef.current) {
            mapRef.current.setPaintProperty("current-location-pulse", "circle-radius", radius);
            mapRef.current.setPaintProperty("current-location-pulse", "circle-opacity", opacity);
          }

          requestAnimationFrame(() => animatePulse(startTime));
        }

        // --- i pezzi scegliibili, e i quattro stati in cui si mostrano --------
        // Sorgenti distinte invece di feature-state: un pezzo scelto resta
        // disegnato anche quando esce dalla vista e la sorgente dei pezzi viene
        // ricaricata, cosa che con lo stato per feature si perderebbe.
        const VUOTO: FeatureCollection = { type: "FeatureCollection", features: [] };
        const BLU = "#00E5FF";
        if (!mapRef.current.getSource("vicinato")) {
          mapRef.current.addSource("vicinato", { type: "geojson", data: VUOTO });
          // Il riempimento serve anche a rendere il layer interrogabile: mapbox
          // non restituisce feature da un layer non disegnato.
          mapRef.current.addLayer({
            id: "vicinato-fill",
            type: "fill",
            source: "vicinato",
            paint: { "fill-color": "#FFFFFF", "fill-opacity": 0.04 },
          });
          // Il bordo dei pezzi utilizzabili e' marcato, quello degli esclusi
          // tenue e tratteggiato: la differenza fra "si puo' scegliere" e "sta
          // qui solo per orientarsi" si legge dal tratto, prima che dal colore.
          mapRef.current.addLayer({
            id: "vicinato-line",
            type: "line",
            source: "vicinato",
            paint: {
              "line-color": "#FFFFFF",
              "line-width": 1.7,
              "line-opacity": 0.92,
            },
          });
        }
        // I pezzi con una coltura che tornatura non gestisce: si DISEGNANO,
        // perche' servono a riconoscere il proprio campo, ma stanno su un layer
        // separato e il gestore del click non e' su questo. Il blocco e' quindi
        // strutturale e non una condizione che si puo' dimenticare.
        if (!mapRef.current.getSource("esclusi")) {
          mapRef.current.addSource("esclusi", { type: "geojson", data: VUOTO });
          mapRef.current.addLayer({
            id: "esclusi-fill",
            type: "fill",
            source: "esclusi",
            paint: { "fill-color": "#FFFFFF", "fill-opacity": 0.02 },
          });
          mapRef.current.addLayer({
            id: "esclusi-line",
            type: "line",
            source: "esclusi",
            paint: {
              "line-color": "#FFFFFF",
              "line-width": 0.8,
              "line-opacity": 0.22,
              "line-dasharray": [1, 2],
            },
          });
        }
        // I fratelli: gli altri pezzi dello stesso campo dichiarato, da
        // aggiungere se si vuole il campo intero invece della porzione.
        if (!mapRef.current.getSource("fratelli")) {
          mapRef.current.addSource("fratelli", { type: "geojson", data: VUOTO });
          mapRef.current.addLayer({
            id: "fratelli-line",
            type: "line",
            source: "fratelli",
            paint: {
              "line-color": BLU,
              "line-width": 1.4,
              "line-opacity": 0.8,
              "line-dasharray": [2, 1.5],
            },
          });
        }
        // L'anteprima sotto il cursore.
        if (!mapRef.current.getSource("anteprima")) {
          mapRef.current.addSource("anteprima", { type: "geojson", data: VUOTO });
          mapRef.current.addLayer({
            id: "anteprima-fill",
            type: "fill",
            source: "anteprima",
            paint: { "fill-color": BLU, "fill-opacity": 0.25 },
          });
        }
        // Il pezzo su cui si e' cliccato ma che aspetta una conferma: velo
        // BIANCO, cosi' si vede quale si sta per usare mentre si legge il
        // pannello e si va a premere il pulsante. Senza, il pannello parla di un
        // pezzo che sulla mappa non e' segnato in alcun modo.
        if (!mapRef.current.getSource("attesa")) {
          mapRef.current.addSource("attesa", { type: "geojson", data: VUOTO });
          mapRef.current.addLayer({
            id: "attesa-fill",
            type: "fill",
            source: "attesa",
            paint: { "fill-color": "#FFFFFF", "fill-opacity": 0.4 },
          });
          // Il bordo da' il taglio netto: su un campo di terra chiara il solo
          // velo sfuma e non si capisce dove finisce il pezzo.
          mapRef.current.addLayer({
            id: "attesa-line",
            type: "line",
            source: "attesa",
            paint: {
              "line-color": "#FFFFFF",
              "line-width": 1.2,
              "line-opacity": 0.9,
            },
          });
        }
        // I pezzi scelti, pieni.
        if (!mapRef.current.getSource("selezione")) {
          mapRef.current.addSource("selezione", { type: "geojson", data: VUOTO });
          mapRef.current.addLayer({
            id: "selezione-fill",
            type: "fill",
            source: "selezione",
            paint: { "fill-color": BLU, "fill-opacity": 0.45 },
          });
        }
        // Il contorno che verra' davvero salvato: disegnarlo rende visibile la
        // riduzione a un anello unico, invece di lasciarla scritta soltanto.
        if (!mapRef.current.getSource("contorno")) {
          mapRef.current.addSource("contorno", { type: "geojson", data: VUOTO });
          mapRef.current.addLayer({
            id: "contorno-line",
            type: "line",
            source: "contorno",
            paint: { "line-color": BLU, "line-width": 3 },
          });
        }

        animatePulse(performance.now());
        setMapLoaded(true);
      });

      // Evidenziazione sotto il cursore: tutta locale, nessuna chiamata al
      // server, quindi immediata. E' SOLO un'anteprima: non entra nella scelta,
      // altrimenti muovendo il cursore verso il pulsante cambierebbe il campo.
      mapRef.current.on("mousemove", "vicinato-fill", (e: mapboxgl.MapMouseEvent) => {
        const f = e.features?.[0];
        if (!f) {
          return;
        }
        mapRef.current.getCanvas().style.cursor = "pointer";
        setAnteprima(pezzoDaFeature(f));
      });
      mapRef.current.on("mouseleave", "vicinato-fill", () => {
        if (mapRef.current) {
          mapRef.current.getCanvas().style.cursor = "";
        }
        setAnteprima(null);
      });

      // Il canvas della mappa non prende il fuoco della tastiera: dopo una
      // ricerca l'input lo mantiene, `onBlurCapture` non scatta e i pannelli
      // resterebbero nascosti. Qualunque interazione con la mappa chiude la
      // ricerca, che e' anche cio' che l'utente si aspetta.
      mapRef.current.on("click", () => setRicercaAttiva(false));
      mapRef.current.on("movestart", () => setRicercaAttiva(false));

      // Sui pezzi esclusi il cursore mostra comunque cos'e', cosi' si capisce
      // perche' non si possono scegliere; il click chiede conferma invece di
      // selezionare, e non fa nulla di silenzioso.
      mapRef.current.on("mousemove", "esclusi-fill", (e: mapboxgl.MapMouseEvent) => {
        const f = e.features?.[0];
        if (!f) {
          return;
        }
        mapRef.current.getCanvas().style.cursor = "help";
        setAnteprima(pezzoDaFeature(f));
      });
      mapRef.current.on("mouseleave", "esclusi-fill", () => {
        if (mapRef.current) {
          mapRef.current.getCanvas().style.cursor = "";
        }
        setAnteprima(null);
      });
      mapRef.current.on("click", "esclusi-fill", (e: mapboxgl.MapMouseEvent) => {
        const draw = drawRef.current;
        if (draw && draw.getMode() === "draw_polygon") {
          return;
        }
        const f = e.features?.[0];
        if (!f) {
          return;
        }
        const pezzo = pezzoDaFeature(f);
        if (Number.isFinite(pezzo.pid)) {
          setDaForzare(pezzo);
        }
      });

      // Il click SCEGLIE il pezzo, e ri-cliccandolo lo toglie. E' cio' che
      // permette di prendere una porzione del campo dichiarato invece di tutto.
      mapRef.current.on("click", "vicinato-fill", (e: mapboxgl.MapMouseEvent) => {
        const draw = drawRef.current;
        // Mentre si disegna a mano il click serve a mettere un vertice: non si
        // ruba all'utente lo strumento che ha scelto.
        if (draw && draw.getMode() === "draw_polygon") {
          return;
        }
        const f = e.features?.[0];
        if (!f) {
          return;
        }
        const pezzo = pezzoDaFeature(f);
        if (!Number.isFinite(pezzo.pid)) {
          // Senza `pid` il confronto "l'ho gia' scelto?" sarebbe sempre falso
          // (NaN non e' uguale a se stesso) e il click accumulerebbe doppioni
          // invece di togliere. Meglio non fare nulla che sbagliare in silenzio.
          return;
        }
        setSelezione((prima) =>
          prima.some((x) => x.pid === pezzo.pid)
            ? prima.filter((x) => x.pid !== pezzo.pid)
            : [...prima, pezzo],
        );
      });

      // Caricamento dei pezzi della vista dopo ogni spostamento, con un ritardo
      // per non chiamare a ogni frame. Non c'e' nessuna interrogazione per
      // movimento del cursore: i pezzi stanno gia' sul client.
      let attesa: ReturnType<typeof setTimeout> | null = null;
      const svuotaPezzi = () => {
        setPezzi([]);
        setSogliaServita(null);
        vicinatoRef.current = null;
        setAnteprima(null);
        setDaForzare(null);
      };
      mapRef.current.on("moveend", () => {
        if (attesa) {
          clearTimeout(attesa);
        }
        attesa = setTimeout(() => {
          const m = mapRef.current;
          if (!m) {
            return;
          }
          if (m.getZoom() < PEZZI_ZOOM_MIN) {
            setVistaLarga(true);
            svuotaPezzi();
            return;
          }
          setVistaLarga(false);
          const c = m.getCenter();
          const b = m.getBounds();
          // Raggio che copre la vista, dai confini veri: mezza diagonale.
          const dLat = (b.getNorth() - b.getSouth()) * 111_320;
          const dLng =
            (b.getEast() - b.getWest()) * 111_320 * Math.cos((c.lat * Math.PI) / 180);
          const raggio = Math.min(
            Math.max(Math.round(Math.hypot(dLat, dLng) / 2), PEZZI_RAGGIO_MIN_M),
            PEZZI_RAGGIO_MAX_M,
          );
          const v = vicinatoRef.current;
          // Si ricarica solo se il centro e' uscito da meta' del raggio caricato,
          // o se il raggio richiesto e' cambiato molto.
          const spostato =
            !v ||
            Math.hypot(
              (c.lat - v.lat) * 111_320,
              (c.lng - v.lng) * 111_320 * Math.cos((c.lat * Math.PI) / 180),
            ) >
              v.r * 0.5 ||
            Math.abs(raggio - v.r) > v.r * 0.4;
          if (!spostato) {
            return;
          }
          vicinatoRef.current = { lat: c.lat, lng: c.lng, r: raggio };
          fetchLandscapePieces(
            Number(c.lat.toFixed(6)),
            Number(c.lng.toFixed(6)),
            raggio,
          )
            .then((res) => {
              // Le sorgenti le riempie l'effetto piu' sotto, che sa dividere gli
              // ammessi dagli esclusi: qui si aggiorna solo lo stato.
              setPezzi(res.pieces?.features ?? []);
              setSogliaServita(res.truncated ? (res.piece_min_ha ?? null) : null);
            })
            .catch(() => {
              // I pezzi sono un aiuto: se non arrivano si disegna a mano.
              vicinatoRef.current = null;
            });
        }, 400);
      });

      drawRef.current = draw;
      mapRef.current.addControl(draw);
      mapRef.current.on("draw.create", updateArea);
      mapRef.current.on("draw.delete", updateArea);
      mapRef.current.on("draw.update", updateArea);
      // Il cestino dello strumento di disegno riporta tutto alla partenza, non
      // solo il poligono: restavano la scelta e l'avviso "confine caricato", e
      // dopo aver svuotato sembrava di essere ancora a meta' di qualcosa.
      mapRef.current.on("draw.delete", () => {
        setSelezione([]);
        setDaForzare(null);
        setAnteprima(null);
        setContornoUsato(false);
        setColturaDalDato(null);
      });
      // Un poligono tracciato a mano non viene da nessun pezzo dichiarato: la
      // coltura ricordata non gli appartiene e va dimenticata.
      mapRef.current.on("draw.create", () => {
        setContornoUsato(false);
        setColturaDalDato(null);
      });

      function updateArea() {
        const data = draw.getAll();
        const points: Point[] = [];
        if (data.features.length > 0) {
          // @ts-ignore
          data.features[0].geometry.coordinates[0].forEach((point: number[]) => {
            points.push({
              lng: point[0],
              lat: point[1],
            });
          });
          setMap(points);
        } else {
          setMap(points);
        }
      }

      return () => {
        if (mapRef.current) {
          mapRef.current.remove();
        }
      };
    }
  }, [mapContainerRef]);

  // I due layer INTERROGABILI: quelli su cui stanno i gestori del cursore e del
  // click. Devono conservare le PROPRIETA' delle feature, perche' e' da quelle
  // che il gestore ricava `pid`, `app_id` e la coltura. Effetto separato dal
  // prossimo perche' dipende dai pezzi caricati e non dal movimento del cursore:
  // rimetterli a ogni mousemove significherebbe riscrivere centinaia di
  // geometrie per nulla.
  React.useEffect(() => {
    const m = mapRef.current;
    if (!m || !mapLoaded) {
      return;
    }
    // La divisione avviene qui e non nei gestori: quelli si registrano una volta
    // sola e vedrebbero per sempre il registro colture del primo render, che al
    // primo render puo' essere ancora vuoto.
    const ammesso = (f: LandscapePiece) =>
      colturaRegistrabile((f.properties?.harvest_code as string) || null, colturePermesse);
    const metti = (nome: string, features: LandscapePiece[]) => {
      const src = m.getSource(nome);
      if (src) {
        src.setData({ type: "FeatureCollection", features });
      }
    };
    metti("vicinato", pezzi.filter(ammesso));
    metti(
      "esclusi",
      pezzi.filter((f) => !ammesso(f)),
    );
  }, [mapLoaded, pezzi, colturePermesse]);

  // Anteprima, pezzi scelti, fratelli e contorno: sorgenti di sola geometria,
  // seguono lo stato e non hanno gestori sopra.
  React.useEffect(() => {
    const m = mapRef.current;
    if (!m || !mapLoaded) {
      return;
    }
    const disegna = (nome: string, geometrie: Geometry[]) => {
      const src = m.getSource(nome);
      if (src) {
        src.setData({
          type: "FeatureCollection",
          features: geometrie.map((g) => ({
            type: "Feature",
            properties: {},
            geometry: g,
          })),
        });
      }
    };
    // Il pezzo in attesa di conferma resta segnato fino alla risposta: e' l'unico
    // evidenziato, percio' mentre c'e' l'anteprima sotto il cursore si spegne.
    disegna("attesa", daForzare ? [daForzare.geometry] : []);
    // L'anteprima si nasconde quando il pezzo e' gia' scelto: sarebbe un
    // evidenziatore su qualcosa di gia' evidenziato.
    const gia = selezione.some((x) => x.pid === anteprima?.pid);
    disegna(
      "anteprima",
      anteprima && !gia && !daForzare ? [anteprima.geometry] : [],
    );
    // Grigio quando la coltura non e' registrabile: il blu significa
    // "scegliibile" e non deve dirlo di qualcosa che non lo e'.
    if (m.getLayer("anteprima-fill")) {
      m.setPaintProperty(
        "anteprima-fill",
        "fill-color",
        anteprima && !colturaRegistrabile(anteprima.harvestCode, colturePermesse)
          ? "#C9C9C4"
          : "#00E5FF",
      );
    }
    disegna("selezione", selezione.map((x) => x.geometry));
    const anelloContorno: Polygon | null = contorno
      ? { type: "Polygon", coordinates: [contorno.ring] }
      : null;
    disegna("contorno", anelloContorno ? [anelloContorno] : []);
    // I fratelli: gli altri pezzi degli stessi campi dichiarati, non ancora
    // scelti. Si pescano da quelli caricati, quindi solo dentro la vista.
    const campi = new Set(selezione.map((x) => x.appId));
    const scelti = new Set(selezione.map((x) => x.pid));
    disegna(
      "fratelli",
      campi.size === 0
        ? []
        : pezzi
            .filter(
              (f) =>
                campi.has(Number(f.properties?.app_id)) &&
                !scelti.has(Number(f.properties?.pid)),
            )
            .map((f) => f.geometry),
    );
  }, [mapLoaded, anteprima, daForzare, selezione, contorno, pezzi, colturePermesse]);

  /** Aggiunge alla scelta gli altri pezzi degli stessi campi dichiarati. */
  const aggiungiFratelli = () => {
    const campi = new Set(selezione.map((x) => x.appId));
    const scelti = new Set(selezione.map((x) => x.pid));
    const nuovi = pezzi
      .filter(
        (f) =>
          campi.has(Number(f.properties?.app_id)) &&
          !scelti.has(Number(f.properties?.pid)),
      )
      .map((f) => pezzoDaFeature(f));
    if (nuovi.length > 0) {
      setSelezione((prima) => [...prima, ...nuovi]);
    }
  };

  /** Carica il contorno scelto dentro lo strumento di disegno. */
  const usaContorno = () => {
    const draw = drawRef.current;
    if (!draw || !contorno) {
      return;
    }
    const anello = contorno.ring;
    draw.deleteAll();
    draw.add({
      type: "Feature",
      properties: {},
      geometry: { type: "Polygon", coordinates: [anello] },
    });
    // La stessa lettura che fa updateArea, anello chiuso compreso.
    setMap(anello.map((c) => ({ lng: c[0], lat: c[1] })));
    setContornoUsato(true);
    // Solo se e' una coltura del registro: un pezzo forzato puo' portare una
    // specie che il menu del passo 2 non contiene, e precompilarla darebbe un
    // valore che non si puo' nemmeno rileggere.
    setColturaDalDato(
      colturaRegistrabile(colturaScelta, colturePermesse) ? colturaScelta : null,
    );
    setSelezione([]);
    setAnteprima(null);
    setDaForzare(null);

    // Porta la vista sul campo: a zoom 13 il poligono puo' essere piccolo, e chi
    // lo accetta vuole vederlo per controllarlo sulla foto.
    try {
      const xs = anello.map((c) => c[0]);
      const ys = anello.map((c) => c[1]);
      mapRef.current?.fitBounds(
        [
          [Math.min(...xs), Math.min(...ys)],
          [Math.max(...xs), Math.max(...ys)],
        ],
        { padding: 60, duration: 600 },
      );
    } catch {
      // se il fit non riesce si resta dove si e'
    }
    // Resta in modalita' selezione: il poligono c'e' gia' e va eventualmente
    // corretto trascinando i vertici, non ridisegnato da zero.
    try {
      draw.changeMode("simple_select");
    } catch {
      // se la modalita' non e' disponibile si resta dove si e'
    }
  };

  const buttonDisabled = map.length === 0;

  return (
    <>
      {/* <h4>Disegna la mappa del campo</h4>
      <hr /> */}
      {mapLoaded && (
        <div
          className="mapbox-searchbox-wrapper-floating"
          // La tendina degli indirizzi vive fuori da questo nodo, ma il fuoco
          // dell'input no: e' da qui che si capisce quando la ricerca e' in uso.
          onFocusCapture={() => setRicercaAttiva(true)}
          onBlurCapture={() => setRicercaAttiva(false)}
        >
          {/*@ts-ignore*/}
          <SearchBox
            options={{
              language: "it",
              country: "IT",
            }}
            accessToken={process.env.REACT_APP_MAPBOX_API_TOKEN ?? ""}
            map={mapRef.current}
            mapboxgl={mapboxgl}
            value={inputValue}
            onChange={(d) => {
              setInputValue(d);
            }}
            marker
          />
        </div>
      )}
      <div ref={mapContainerRef} id="map" data-map-type="area-drawing"></div>

      {/* Un pezzo con una coltura che non gestiamo non entra nella scelta col
          click: apre questa conferma, che ha la precedenza su tutto il resto
          perche' e' una domanda in attesa di risposta. */}
      {!ricercaAttiva && daForzare && (
        <div className="mapbox-searchbox-wrapper-floating" style={STILE_PANNELLO}>
          <div className="contents bg-white soft p-3">
            <div className="font-m-600 mb-1">
              {daForzare.crop || "Coltura non indicata"}: coltura non seguita da
              tornatura
            </div>
            <div className="font-s mb-2">
              {daForzare.ha.toLocaleString("it-IT", { maximumFractionDigits: 2 })} ha.
              Per il campo dovrai comunque scegliere una delle colture in elenco. Il
              dato dichiarato si riferisce alla campagna in corso: se hai appena
              impiantato, il confine e&apos; valido anche se la coltura non lo e&apos;.
            </div>
            <div className="d-flex flex-wrap">
              <button
                type="button"
                className="trnt_btn slim-y narrow-x secondary type-rounded me-2"
                onClick={() => {
                  setSelezione((prima) =>
                    prima.some((x) => x.pid === daForzare.pid)
                      ? prima
                      : [...prima, daForzare],
                  );
                  setDaForzare(null);
                }}
              >
                Usa comunque il confine
              </button>
              <button
                type="button"
                className="trnt_btn slim-y narrow-x secondary type-rounded"
                onClick={() => setDaForzare(null)}
              >
                Annulla
              </button>
            </div>
          </div>
        </div>
      )}

      {/* La scelta ha la precedenza sull'anteprima: una volta cliccato un pezzo,
          muovere il cursore verso il pulsante non deve cambiare cio' che si sta
          per usare. */}
      {!ricercaAttiva && !daForzare && selezione.length > 0 && contorno && (
        <div className="mapbox-searchbox-wrapper-floating" style={STILE_PANNELLO}>
          <div className="contents bg-white soft p-3">
            <div className="font-m-600 mb-1">
              {selezione.length === 1
                ? "1 pezzo scelto"
                : `${selezione.length} pezzi scelti`}
              &nbsp;·&nbsp;
              {contorno.ha.toLocaleString("it-IT", { maximumFractionDigits: 2 })} ha
            </div>
            <div className="font-s mb-2">
              {colturaScelta
                ? `Coltura dichiarata: ${selezione[0].crop}`
                : "Pezzi con colture dichiarate diverse"}
              {selezione.some(
                (x) => !colturaRegistrabile(x.harvestCode, colturePermesse),
              ) && " — non fra quelle seguite da tornatura"}
            </div>
            <div className="mb-2">
              {selezione.slice(0, PEZZI_IN_ELENCO).map((x) => (
                <div
                  key={x.pid}
                  className="d-flex align-items-center justify-content-between font-s"
                >
                  <span>
                    {x.crop || "Superficie dichiarata"} &nbsp;·&nbsp;
                    {x.ha.toLocaleString("it-IT", { maximumFractionDigits: 2 })} ha
                  </span>
                  <button
                    type="button"
                    className="trnt_btn slim-y narrow-x secondary type-rounded"
                    title="Togli questo pezzo"
                    aria-label={`Togli ${x.crop || "il pezzo"} di ${x.ha} ettari`}
                    onClick={() =>
                      setSelezione((prima) => prima.filter((y) => y.pid !== x.pid))
                    }
                  >
                    <Icon iconName={"bin"} color={"black"} />
                  </button>
                </div>
              ))}
              {selezione.length > PEZZI_IN_ELENCO && (
                <div className="font-s opacity-05">
                  e altri {selezione.length - PEZZI_IN_ELENCO}: per togliere quelli,
                  clicca il pezzo sulla mappa.
                </div>
              )}
            </div>
            {campiDistinti > 1 && (
              <div className="font-s mb-2">
                I pezzi appartengono a {campiDistinti} campi dichiarati diversi. Fra
                due campi dichiarati c&apos;e&apos; quasi sempre una striscia non
                coltivata — capezzagna o fosso, di solito circa 5 m — che non e&apos;
                dichiarata e resta fuori dal confine.
              </div>
            )}
            {fratelliNellaVista > 0 && (
              <div className="font-s mb-2">
                Questo campo dichiarato ha altri {fratelliNellaVista}{" "}
                {fratelliNellaVista === 1 ? "pezzo" : "pezzi"} nella vista, col
                contorno tratteggiato.
              </div>
            )}
            {contorno.partiScartate > 0 && (
              <div className="font-s mb-2">
                I pezzi scelti non si toccano. Un campo ha un contorno solo, quindi
                verra&apos; usata la parte piu&apos; grande e{" "}
                {contorno.partiScartate === 1
                  ? "l'altra resta"
                  : `le altre ${contorno.partiScartate} restano`}{" "}
                fuori.
              </div>
            )}
            {contorno.vuotiM2 > 0 && (
              <div className="font-s mb-2">
                Dentro i pezzi scelti c'e' un'area non dichiarata di circa{" "}
                {contorno.vuotiM2.toLocaleString("it-IT")} m²: il contorno la
                ingloba, e l'estensione risulta{" "}
                {contorno.ha.toLocaleString("it-IT", { maximumFractionDigits: 2 })} ha
                invece di{" "}
                {contorno.haPezzi.toLocaleString("it-IT", {
                  maximumFractionDigits: 2,
                })}{" "}
                ha.
              </div>
            )}
            {map.length > 0 && (
              <div className="font-s mb-2">
                Usando questo confine sostituisci il poligono che hai disegnato.
              </div>
            )}
            <div className="d-flex flex-wrap">
              <button
                type="button"
                className="trnt_btn slim-y narrow-x primary type-rounded me-2"
                onClick={usaContorno}
              >
                Usa questo confine
              </button>
              {fratelliNellaVista > 0 && (
                <button
                  type="button"
                  className="trnt_btn slim-y narrow-x secondary type-rounded me-2"
                  onClick={aggiungiFratelli}
                >
                  Tutto il campo
                </button>
              )}
              <button
                type="button"
                className="trnt_btn slim-y narrow-x secondary type-rounded"
                title="Svuota la scelta"
                aria-label="Svuota la scelta"
                onClick={azzeraScelta}
              >
                <Icon iconName={"bin"} color={"black"} />
              </button>
            </div>
          </div>
        </div>
      )}

      {!ricercaAttiva && !daForzare && selezione.length === 0 && anteprima && (
        <div className="mapbox-searchbox-wrapper-floating" style={STILE_PANNELLO}>
          <div className="contents bg-white soft p-3">
            <div className="font-m-600 mb-1">
              {anteprima.crop || "Superficie dichiarata"} &nbsp;·&nbsp;
              {anteprima.ha.toLocaleString("it-IT", { maximumFractionDigits: 2 })} ha
            </div>
            <div className="font-s">
              {colturaRegistrabile(anteprima.harvestCode, colturePermesse) ? (
                <>
                  Clicca per scegliere questo pezzo
                  {anteprima.appN > 1
                    ? `; il campo dichiarato ne ha ${anteprima.appN} in tutto.`
                    : "."}
                </>
              ) : (
                <>
                  <span className="font-m-600">Coltura non seguita da tornatura.</span>{" "}
                  Clicca se vuoi usarne comunque il confine.
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Le tre situazioni in cui non c'e' ancora niente di scelto ne' di
          disegnato. Vanno distinte, perche' da quando la selezione e' la
          modalita' di partenza il click sulla mappa non disegna piu' e senza una
          riga di spiegazione sembrerebbe che non funzioni nulla. */}
      {!ricercaAttiva &&
        !daForzare &&
        selezione.length === 0 &&
        !anteprima &&
        !contornoUsato &&
        map.length === 0 && (
        <div className="mapbox-searchbox-wrapper-floating" style={STILE_PANNELLO}>
          <div className="contents bg-white soft p-3 font-s">
            {pezzi.length > 0 ? (
              <>
                Passa il cursore sulle superfici dichiarate e clicca per comporre il
                campo, anche prendendone solo una porzione. Si scelgono le colture
                seguite da tornatura; le altre restano disegnate a tratteggio, per
                orientarsi. Per disegnare a mano usa il pulsante del poligono.
                {sogliaServita !== null && (
                  <>
                    {" "}
                    A questo livello di zoom si vedono i pezzi da{" "}
                    {sogliaServita.toLocaleString("it-IT", {
                      maximumFractionDigits: 2,
                    })}{" "}
                    ha in su: avvicinati per i piu' piccoli.
                  </>
                )}
              </>
            ) : vistaLarga ? (
              <>
                Cerca la zona e avvicinati: i confini gia' dichiarati si
                scelgono col click, senza tracciarli. Per disegnare a mano, usa il
                pulsante del poligono.
              </>
            ) : (
              <>
                Qui non risultano confini dichiarati da scegliere: disegna il campo
                col pulsante del poligono.
              </>
            )}
          </div>
        </div>
      )}

      {!ricercaAttiva && contornoUsato && selezione.length === 0 && (
        <div className="mapbox-searchbox-wrapper-floating" style={STILE_PANNELLO}>
          <div className="contents bg-white soft p-3 font-s">
            Confine caricato dal dato dichiarativo. Controllalo sulla foto e correggilo
            trascinando i vertici, oppure cancellalo e disegnalo a mano.
          </div>
        </div>
      )}

      <div className="fixed-bottom mt-4 text-center" data-style="floating">
        <div className="contents bg-glass">
          <button
            className="trnt_btn accent-stronger"
            onClick={() => {
              if (buttonDisabled) {
                alert("Disegna l'area del campo sulla mappa prima di procedere");
              } else {
                onNextClick({ map, harvest: colturaDalDato });
              }
            }}
            // disabled={buttonDisabled}
            data-disabled-like={buttonDisabled ? "true" : "false"}
            title={buttonDisabled ? "Disegna l'area del campo sulla mappa" : ""}
          >
            {action}
          </button>
        </div>
      </div>
    </>
  );
};

export function CompanyFieldForm() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { companyId } = useParams();
  const currentCompany = useAppSelector((state) =>
    companiesSelectors.selectCompanybyId(state, companyId ?? "default"),
  );
  const [step, setStep] = React.useState(1);
  const [action, setAction] = React.useState("Avanti");
  const [formData, setFormData] = React.useState<AgriFieldMutationPayload>({
    name: "",
    variety: "",
    description: "",
    area: 0,
    harvest: "",
    plants: 0,
    map: [],
    irrigation: "",
    weaving: "",
    rotation: "",
    grassing: "",
    year: "",
  });

  React.useEffect(() => {
    if (step === 1) {
      dispatch(headerbarActions.setTitle({ title: "Disegna l'area del campo", subtitle: "–" }));
    } else if (step === 2) {
      dispatch(headerbarActions.setTitle({ title: "Dettagli del campo", subtitle: "–" }));
    }
  }, [step]);

  const createFieldAction = async (payload: AgriFieldMutationPayload) => {
    if (currentCompany) {
      try {
        await dispatch(
          fieldsActions.addNewFieldAction({ orgId: currentCompany.orgId, body: payload }),
        );
        navigate(`/m/companies/${companyId}/fields`, { replace: true });
      } catch (reason) {
        console.error("Error creating field with reason: ", reason);
      }
    }
  };

  const handleNextClick = async (data: any) => {
    if (step === 2) {
      const payload = {
        ...formData,
        name: data.name,
        description: data.description,
        area: data.area,
        harvest: data.harvest,
        plants: data.plants,
        variety: data.variety,
        irrigation: data.irrigation,
        weaving: data.weaving,
        rotation: data.rotation,
        grassing: data.rotation,
        year: data.year,
      };
      setFormData(payload);
      await createFieldAction(payload);
    } else if (step === 1) {
      const disegno = data as DisegnoCompletato;
      const payload = {
        ...formData,
        map: disegno.map,
        // La coltura arriva dal pezzo dichiarato scelto sulla mappa, quando c'e'.
        // Se manca si conserva quella eventualmente gia' in `formData`, cosi'
        // tornare indietro e riavanzare non cancella una scelta gia' fatta.
        harvest: disegno.harvest ?? formData.harvest,
      };
      setFormData(payload);
      setAction("Aggiungi campo");
      setStep(step + 1);
    }
  };

  const handleBackClick = async () => {
    if (step > 1) {
      setStep(step - 1);
      setAction("Avanti");
    }
  };

  return (
    <Fragment>
      {step === 1 && (
        <div className="remove-content-padding-x remove-content-padding-y">
          <FieldFormMap formData={formData} action={action} onNextClick={handleNextClick} />
        </div>
      )}
      {step === 2 && (
        <Container>
          <Row className="mt-2">
            <Col xl={12} className="py-3">
              <FieldFormInfo
                formData={formData}
                action={action}
                onBackClick={handleBackClick}
                onNextClick={handleNextClick}
              />
            </Col>
          </Row>
        </Container>
      )}
    </Fragment>
  );
}
