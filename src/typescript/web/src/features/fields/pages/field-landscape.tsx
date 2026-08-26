import React, { Fragment } from "react";
import { useParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { fieldsSelectors } from "../state/fields-slice";
import { AgriField, Point } from "@tornatura/coreapis";
import * as turf from "@turf/turf";
import {
  LandscapeParcelsResponse,
  LandscapeResponse,
  fetchLandscapeComposition,
  fetchLandscapeParcels,
} from "../../../services/model-api";
import { Container, Row, Col } from "react-bootstrap";
import TableCozy, { TableColumn, TableOptions } from "../../../components/TableCozy";
import MapLandscapeCrops, { LEGENDA_FAMIGLIE } from "../../../components/MapLandscapeCrops";

const RADIUS_OPTIONS_M = [3000, 5000, 10000];
const DEFAULT_RADIUS_M = 3000;

/**
 * Anello del poligono del campo, chiuso.
 *
 * In archivio esistono campi con primo e ultimo vertice diversi: turf.polygon
 * solleva un'eccezione su un anello aperto, e dentro un useMemo l'eccezione
 * farebbe cadere l'intera pagina.
 */
function getFieldRing(field?: AgriField): number[][] | null {
  if (!field?.map?.length || field.map.length < 3) {
    return null;
  }
  const points: Point[] = field.map;
  const ring = points.map((p) => [p.lng, p.lat]);
  const first = ring[0];
  const last = ring[ring.length - 1];
  if (first[0] !== last[0] || first[1] !== last[1]) {
    ring.push([first[0], first[1]]);
  }
  return ring;
}

function getFieldCentroid(field?: AgriField): { lat: number; lng: number } | null {
  if (!field?.map?.length) {
    return null;
  }
  const ring = getFieldRing(field);
  if (!ring) {
    return { lat: field.map[0].lat, lng: field.map[0].lng };
  }
  try {
    const centroid = turf.centroid(turf.polygon([ring]));
    return {
      lng: centroid.geometry.coordinates[0],
      lat: centroid.geometry.coordinates[1],
    };
  } catch {
    return { lat: field.map[0].lat, lng: field.map[0].lng };
  }
}

function formatHarvestName(crop?: string | null) {
  if (!crop) {
    return "-";
  }
  return crop
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function formatHa(ha?: number | null) {
  if (ha == null) {
    return "-";
  }
  return `${ha.toLocaleString("it-IT", { maximumFractionDigits: 0 })} ha`;
}

export function FieldLandscape() {
  const dispatch = useAppDispatch();
  const { fieldId } = useParams();
  const currentField = useAppSelector((state) =>
    fieldsSelectors.selectFieldbyId(state, fieldId ?? "default"),
  );

  const [data, setData] = React.useState<LandscapeResponse | null>(null);
  const [geo, setGeo] = React.useState<LandscapeParcelsResponse | null>(null);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);
  const [radiusM, setRadiusM] = React.useState<number>(DEFAULT_RADIUS_M);
  const [showCrop, setShowCrop] = React.useState<boolean>(true);
  const [showAgri, setShowAgri] = React.useState<boolean>(true);
  const [tabellaEspansa, setTabellaEspansa] = React.useState<boolean>(false);

  const centroid = React.useMemo(() => getFieldCentroid(currentField), [currentField]);
  const fieldRing = React.useMemo(() => getFieldRing(currentField), [currentField]);

  React.useEffect(() => {
    dispatch(
      headerbarActions.setTitle({
        title: "Il tuo paesaggio",
        subtitle: "Le colture intorno al tuo campo",
      }),
    );
  }, [dispatch]);

  React.useEffect(() => {
    if (!currentField) {
      return;
    }
    if (!centroid) {
      setError("Il campo non ha una mappa: non è possibile individuare la sua posizione.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    const lat = Number(centroid.lat.toFixed(6));
    const lng = Number(centroid.lng.toFixed(6));

    Promise.all([
      fetchLandscapeComposition(lat, lng, radiusM, currentField.harvest),
      fetchLandscapeParcels(lat, lng, radiusM, currentField.harvest),
    ])
      .then(([composition, parcels]) => {
        setData(composition);
        setGeo(parcels);
      })
      .catch((err) => {
        setData(null);
        setGeo(null);
        setError(
          err instanceof Error
            ? err.message
            : "Non è stato possibile caricare il paesaggio agricolo del campo.",
        );
      })
      .finally(() => {
        setLoading(false);
      });
  }, [currentField, centroid, radiusM]);

  if (!currentField) {
    return (
      <Container fluid className="mb-5">
        <Row>
          <Col>Caricamento campo...</Col>
        </Row>
      </Container>
    );
  }

  const crop = data?.crop;
  const km = radiusM / 1000;
  const datasetLabel = data?.dataset
    ? `${data.dataset.source} ${data.dataset.year}`
    : "ARPAE iColt";
  const aggregato = crop?.reason === "aggregated_class";
  const oss = data?.observability;
  const semi = data?.seminatural;
  const cross = data?.crosscheck;
  const daDichiarazioni = data?.source === "agrea";
  // Fuori dall'area cartografata i numeri non si mostrano: la mappa resta, con il
  // campo e il cerchio vuoto, che e' la cosa piu' onesta da far vedere.
  const numeriAttendibili = oss?.status !== "suppressed";

  // Etichetta del layer della coltura: per mais e barbabietola iColt non
  // distingue la specie, quindi si nomina la classe collettiva, non la coltura.
  const cropLayerLabel = crop?.icolt_class
    ? aggregato
      ? `${formatHarvestName(crop.icolt_class)} (comprende il tuo ${formatHarvestName(
          crop.harvest,
        ).toLowerCase()})`
      : formatHarvestName(crop.icolt_class)
    : null;

  const coloreFamiglia = (family?: string) =>
    LEGENDA_FAMIGLIE.find((f) => f.family === family)?.color ??
    LEGENDA_FAMIGLIE[LEGENDA_FAMIGLIE.length - 1].color;

  const tableColumns: TableColumn[] = [
    {
      id: "coltura",
      headerText: "Coltura",
      type: "text",
      sortable: true,
      sortValueId: "colturaSort",
    },
    { id: "ettari", headerText: "Ettari", type: "text", sortable: true, align: "right" },
    {
      id: "quota",
      headerText: "% sup. cartografata",
      type: "text",
      sortable: true,
      sortValueId: "pctValue",
      align: "right",
    },
    {
      id: "appezzamenti",
      headerText: "Appezzamenti",
      type: "text",
      sortable: true,
      align: "right",
    },
  ];

  const tableOptions: TableOptions = { defaultSortCol: "ettari", defaultSortDir: "desc" };

  const composizione = data?.composition ?? [];
  const tableDataAll = composizione.map((row) => ({
    coltura: (
      <span className="d-flex align-items-center">
        <span
          className="dot me-2 flex-shrink-0"
          data-size="10"
          style={{ background: coloreFamiglia((row as any).family) }}
        ></span>
        {row.icolt_class ?? "-"}
      </span>
    ),
    colturaSort: row.icolt_class ?? "-",
    ettari: row.ha ?? 0,
    quota: `${(row.pct ?? 0).toFixed(1)}%`,
    pctValue: row.pct ?? 0,
    // Le classi accorpate non pubblicano il conteggio: sotto i tre appezzamenti
    // una riga descrive singole aziende, non il paesaggio.
    appezzamenti: row.parcels ?? "—",
  }));
  const tableData = tabellaEspansa ? tableDataAll : tableDataAll.slice(0, 5);
  const righeNascoste = tableDataAll.length - tableData.length;

  return (
    <Container fluid className="mb-5">
      <Row>
        <Col>
          {error && <div className="alert alert-danger">{error}</div>}
          {loading && <div>Caricamento paesaggio agricolo...</div>}
          {!loading && !error && (
            <Fragment>
              {/* --- mappa e controlli ------------------------------------- */}
              <section className="soft bg-white">
                <Row className="mb-3">
                  <Col xl={12}>
                    <h1>Le colture intorno al tuo campo</h1>
                  </Col>
                </Row>

                <MapLandscapeCrops
                  fieldRing={fieldRing}
                  buffer={geo?.buffer ?? null}
                  parcels={(geo?.parcels as any) ?? null}
                  cropLabel={cropLayerLabel}
                  aggregatedClasses={geo?.aggregated_classes ?? {}}
                  datasetLabel={datasetLabel}
                  showAgri={showAgri}
                  showCrop={showCrop}
                />

                <Row className="mt-3">
                  <Col md={6} className="mb-2 mb-md-0">
                    <div className="iiinfo-label font-s-label mb-1">Layer</div>
                    <div className="d-flex flex-wrap">
                      {cropLayerLabel && (
                        <button
                          type="button"
                          className={`trnt_btn slim-y narrow-x type-rounded me-2 mb-2 ${
                            showCrop ? "primary" : "secondary"
                          }`}
                          onClick={() => setShowCrop(!showCrop)}
                        >
                          {cropLayerLabel}
                        </button>
                      )}
                      <button
                        type="button"
                        className={`trnt_btn slim-y narrow-x type-rounded me-2 mb-2 ${
                          showAgri ? "primary" : "secondary"
                        }`}
                        onClick={() => setShowAgri(!showAgri)}
                      >
                        Superfici agricole
                      </button>
                    </div>
                  </Col>
                  <Col md={6}>
                    <div className="iiinfo-label font-s-label mb-1">Raggio</div>
                    <div className="d-flex">
                      {RADIUS_OPTIONS_M.map((option) => (
                        <button
                          key={option}
                          type="button"
                          className={`trnt_btn slim-y narrow-x type-rounded me-2 mb-2 ${
                            radiusM === option ? "primary" : "secondary"
                          }`}
                          onClick={() => setRadiusM(option)}
                        >
                          {option / 1000} km
                        </button>
                      ))}
                    </div>
                  </Col>
                </Row>

                {geo?.truncated && (
                  <div className="alert alert-warning mt-3 mb-0 font-s">
                    L&apos;area contiene piu&apos; appezzamenti di quanti la mappa possa
                    disegnarne: alcuni non sono mostrati, mentre le percentuali qui sotto
                    restano calcolate su tutti. Riduci il raggio per vederli tutti.
                  </div>
                )}

                <p className="font-s opacity-05 mb-0">
                  Clicca un appezzamento per sapere quale coltura vi è dichiarata e quanti
                  ettari occupa entro il raggio. Il cerchio tratteggiato è l&apos;area su cui
                  tutti i numeri di questa pagina sono calcolati.
                  {geo?.map_min_ha != null && geo.map_pct_of_area != null && (
                    <>
                      {" "}
                      La mappa disegna gli appezzamenti sopra {geo.map_min_ha} ettari, cioè il{" "}
                      {geo.map_pct_of_area.toFixed(0)}% della superficie; le percentuali li
                      includono tutti.
                    </>
                  )}
                </p>
              </section>

              {/* --- la tua coltura nel paesaggio -------------------------- */}
              <section className="soft bg-white">
                {oss?.status === "suppressed" && (
                  <div className="alert alert-warning font-s">
                    Questo campo e&apos; fuori dall&apos;area cartografata da{" "}
                    {datasetLabel}, che copre la pianura emiliano-romagnola: entro{" "}
                    {(oss.radius_m ?? 3000) / 1000} km risulta cartografato il{" "}
                    {oss.mapped_pct}% del territorio. Le colture di collina come vite e
                    olivo sono fortemente sottostimate. Per questo campo non mostriamo la
                    composizione del paesaggio: sarebbe un numero calcolato su dati
                    mancanti.
                  </div>
                )}
                {oss?.status === "partial" && (
                  <div className="alert alert-warning font-s">
                    Entro {(oss.radius_m ?? 3000) / 1000} km risulta cartografato il{" "}
                    {oss.mapped_pct}% del territorio
                    {oss.worst_quadrant_pct != null &&
                    oss.worst_quadrant_pct < 10 &&
                    oss.quadrant_pct
                      ? ", e la parte cartografata e' concentrata da un lato del cerchio"
                      : ""}
                    . Le percentuali qui sotto sono calcolate sul solo territorio
                    cartografato, non sull&apos;intero raggio.
                  </div>
                )}
                {data?.coverage_note && (
                  <div className="alert alert-warning font-s">{data.coverage_note}</div>
                )}
                {numeriAttendibili &&
                crop?.mappable &&
                crop.pct_of_agri != null &&
                crop.ha != null ? (
                  crop.ha > 0 ? (
                    <Fragment>
                      <p className="font-m mb-2">
                        Entro {km} km <strong>{formatHarvestName(crop.harvest)}</strong> occupa{" "}
                        <strong>{formatHa(crop.ha)}</strong>, cioè il{" "}
                        <strong>{crop.pct_of_agri.toFixed(1)}%</strong> dei{" "}
                        {formatHa(data?.agri_ha)} di superficie agricola che iColt cartografa
                        intorno al tuo campo.
                      </p>
                      <p className="font-s mb-0">
                        Perché guardarlo: quanto una coltura è concentrata nel paesaggio dice
                        quanta risorsa continua è disponibile per gli organismi che vivono su
                        quella coltura. È un elemento di consapevolezza, non una previsione: il
                        dato non dice se e quanto quella concentrazione si traduca in pressione
                        sul tuo campo, che dipende dall&apos;organismo, da quanto si sposta e
                        dalla stagione.
                      </p>
                    </Fragment>
                  ) : (
                    <p className="font-m mb-0">
                      Entro {km} km non risultano altri appezzamenti di{" "}
                      <strong>{formatHarvestName(crop.harvest)}</strong> nei dati satellitari.
                    </p>
                  )
                ) : null}

                {aggregato && (
                  <p className="font-m mb-0">
                    Nei dati satellitari <strong>{formatHarvestName(crop?.harvest)}</strong> non
                    è distinguibile: ricade nella classe collettiva{" "}
                    <strong>{crop?.icolt_class}</strong>, insieme a{" "}
                    {geo?.aggregated_classes?.[crop?.icolt_class ?? ""] ??
                      "altre colture con lo stesso ciclo"}
                    . Il layer mostra quindi tutta la classe, non il solo{" "}
                    {formatHarvestName(crop?.harvest).toLowerCase()}.
                  </p>
                )}

                {crop?.reason === "not_in_dataset" && (
                  <p className="font-m mb-0">
                    <strong>{formatHarvestName(crop.harvest)}</strong> non è presente nei dati
                    satellitari di questa regione. Sulla mappa resta il contesto agricolo
                    complessivo.
                  </p>
                )}

                {crop?.reason === "unknown_harvest_code" && (
                  <p className="font-m mb-0">
                    La coltura registrata per questo campo non è riconosciuta nei dati
                    satellitari. Sulla mappa resta il contesto agricolo complessivo.
                  </p>
                )}
              </section>

              {/* --- ambienti semi-naturali e controllo incrociato --------- */}
              {numeriAttendibili && (semi || cross) && (
                <section className="soft bg-white">
                  {semi && semi.pct_of_buffer != null && (
                    <Fragment>
                      <h2 className="mb-3">Ambienti semi-naturali</h2>
                      <Row>
                        <Col md={4} className="iiinfo-col mb-2">
                          <div className="iiinfo-label font-s-label">
                            Quota entro {km} km
                          </div>
                          <div className="iiinfo-value font-l-600">
                            {semi.pct_of_buffer.toFixed(1)}%
                          </div>
                        </Col>
                        <Col md={4} className="iiinfo-col mb-2">
                          <div className="iiinfo-label font-s-label">Bosco</div>
                          <div className="iiinfo-value font-l-600">
                            {formatHa(semi.bosco_ha)}
                          </div>
                        </Col>
                        <Col md={4} className="iiinfo-col mb-2">
                          <div className="iiinfo-label font-s-label">
                            Siepi, margini, fossi
                          </div>
                          <div className="iiinfo-value font-l-600">
                            {formatHa(semi.elementi_ha)}
                            {semi.elementi_n ? (
                              <span className="font-s opacity-05">
                                {" "}
                                in {semi.elementi_n.toLocaleString("it-IT")} elementi
                              </span>
                            ) : null}
                          </div>
                        </Col>
                      </Row>
                      <p className="font-s opacity-05 mt-2 mb-0">
                        Bosco, siepi, filari, fossi e maceri dichiarati nelle domande PAC.
                        Sono l&apos;elemento di paesaggio che la letteratura collega piu&apos;
                        spesso alla presenza di insetti e dei loro antagonisti, e che la
                        classificazione satellitare non contiene affatto. La superficie
                        degli elementi minori e&apos; contata per appartenenza del loro
                        centro al raggio, con uno scarto misurato dello 0-2%.
                      </p>
                    </Fragment>
                  )}

                  {cross && cross.usable && cross.crop_pct_of_agri != null && (
                    <p className="font-s mt-4 mb-0">
                      <strong>Controllo indipendente.</strong> Sulla stessa domanda la
                      classificazione satellitare {cross.source === "icolt" ? "iColt" : ""}{" "}
                      {cross.year} dice {cross.crop_pct_of_agri.toFixed(1)}%
                      {cross.delta_pct_points != null && (
                        <> , cioe&apos; {cross.delta_pct_points.toFixed(1)} punti di scarto</>
                      )}
                      . Le due fonti sono indipendenti — una dichiarazione e
                      un&apos;osservazione da satellite — e il loro disaccordo e&apos; la
                      misura piu&apos; onesta dell&apos;incertezza di questo numero.
                    </p>
                  )}
                  {cross && cross.usable === false && (
                    <p className="font-s opacity-05 mt-4 mb-0">
                      Qui la classificazione satellitare non arriva, quindi non c&apos;e&apos;
                      una seconda misura con cui confrontare questi numeri.
                    </p>
                  )}
                </section>
              )}

              {/* --- composizione e limiti del dato ----------------------- */}
              {numeriAttendibili && (
              <section className="soft bg-white">
                <h2 className="mb-3">Composizione della superficie cartografata</h2>
                <TableCozy columns={tableColumns} data={tableData} options={tableOptions} />
                {(righeNascoste > 0 || tabellaEspansa) && (
                  <button
                    type="button"
                    className="trnt_btn slim-y narrow-x secondary type-rounded mt-3"
                    onClick={() => setTabellaEspansa(!tabellaEspansa)}
                  >
                    {tabellaEspansa
                      ? "Mostra solo le prime 5"
                      : `Mostra tutte le colture (${righeNascoste} in piu')`}
                  </button>
                )}

                <Row className="mt-4">
                  <Col md={6} className="iiinfo-col mb-2">
                    <div className="iiinfo-label font-s-label">Superficie agricola entro {km} km</div>
                    <div className="iiinfo-value font-l-600">{formatHa(data?.agri_ha)}</div>
                  </Col>
                  <Col md={6} className="iiinfo-col mb-2">
                    <div className="iiinfo-label font-s-label">Appezzamenti</div>
                    <div className="iiinfo-value font-l-600">{data?.parcels ?? "-"}</div>
                  </Col>
                </Row>

                <p className="font-s opacity-05 mt-3 mb-0">
                  Fonte: {datasetLabel}.{" "}
                  {daDichiarazioni
                    ? "Sono i piani colturali che le aziende dichiarano per la PAC: coprono anche la collina e nominano le colture, ma esistono solo per le aziende che presentano la dichiarazione, e non tutte ne hanno l'obbligo."
                    : "Classificazione colturale da immagini satellitari di ARPAE Emilia-Romagna, che cartografa gli appezzamenti oltre 0,5 ettari della pianura: dove la copertura è parziale, in particolare in collina, le superfici sono sottostimate."}{" "}
                  Il dato è annuale. Descrive il paesaggio,
                  non le singole aziende. Le classi sostenute da meno di tre
                  appezzamenti sono accorpate in "altre colture": una riga con uno o due
                  appezzamenti descriverebbe singole aziende, non il paesaggio.
                </p>
              </section>
              )}
            </Fragment>
          )}
        </Col>
      </Row>
    </Container>
  );
}
