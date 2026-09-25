import { Fragment } from "react";
import { Col, Row } from "react-bootstrap";
import TableCozy, { TableColumn, TableOptions } from "./TableCozy";
import InfoPopover from "./InfoPopover";
import type { LandscapePestHabitat } from "../services/model-api";

/**
 * Sezione "quanto il paesaggio ospita un organismo" nella pagina del paesaggio.
 *
 * E' GENERICA: riceve la risposta di /v1/landscape/pest-habitat e disegna titolo,
 * testi, livelli, serbatoi, distanze e prime specie con le etichette che il servizio
 * manda. La cimice asiatica e' il primo organismo; il secondo non richiedera' un
 * componente nuovo, ma una cartella dati in piu' nel servizio.
 *
 * Stile: consapevolezza, non rischio. Niente punteggio, niente semaforo: numeri con
 * il loro perche', limiti dichiarati, fonti linkate.
 */

const DEF_LIVELLI =
  "I livelli non sono un giudizio: discendono da una regola applicata a fonti pubblicate. " +
  "Colture con danno documentato = almeno due fonti indipendenti riportano danni in Italia o in Europa. " +
  "Altre piante ospiti = almeno una prova che l'organismo vi si nutre o si riproduce (una sola fonte di danno, " +
  "liste ospiti internazionali, segnalazioni del servizio fitosanitario).";
const DEF_DISTANZA =
  "Distanza dal bordo del tuo campo al bordo dell'elemento piu' vicino, indicata per fasce e non in metri: " +
  "descrive il paesaggio, non il campo di un vicino. Il tuo campo e' escluso dal conteggio.";
const DEF_SERBATOI =
  "Bosco, siepi, boschetti, fasce e margini dichiarati nelle domande PAC: rifugi dove molti organismi svernano " +
  "e da cui entrano nelle colture. La quota e' calcolata sull'intero cerchio.";

function formatHa(ha?: number | null) {
  if (ha == null) {
    return "-";
  }
  return `${ha.toLocaleString("it-IT", { maximumFractionDigits: 0 })} ha`;
}

function pct(v?: number | null) {
  return v == null ? "-" : `${v.toFixed(1)}%`;
}

const ORIGINE: Record<string, string> = {
  ring: "misurata dal contorno del tuo campo",
  declared_parcel: "misurata dall'appezzamento dichiarato in cui ricade il campo",
  centroid: "misurata dal centro del campo",
};

type Props = {
  data: LandscapePestHabitat;
  /** Raggio in km, per i testi ("entro 3 km"). */
  km: number;
};

export default function PestHabitatSection({ data, km }: Props) {
  if (!data.available) {
    return null;
  }
  const testi = data.texts ?? {};
  const livelli = data.levels ?? {};
  const principali = livelli.principale;
  const secondari = livelli.secondario;
  const nonClass = livelli.non_classificabile;
  const famiglie = data.hosts?.by_family ?? {};
  const serbatoi = data.reservoirs;
  const vicini = data.nearest ?? {};
  const titolo = testi.title ?? `${data.pest?.label ?? "Organismo"}: le piante ospiti intorno al tuo campo`;

  const colonne: TableColumn[] = [
    { id: "specie", headerText: "Pianta", type: "text", sortable: true, sortValueId: "specieSort" },
    { id: "livello", headerText: "Livello", type: "text", sortable: true },
    { id: "ettari", headerText: "Ettari", type: "text", sortable: true, align: "right" },
    {
      id: "quota",
      headerText: "% sup. dichiarata",
      type: "text",
      sortable: true,
      sortValueId: "quotaValue",
      align: "right",
    },
    { id: "appezzamenti", headerText: "Appezzamenti", type: "text", sortable: true, align: "right" },
  ];
  const opzioni: TableOptions = { defaultSortCol: "ettari", defaultSortDir: "desc" };
  const righe = (data.top_hosts ?? []).map((r) => ({
    specie: r.species,
    specieSort: r.species,
    livello: livelli[r.level]?.label ?? r.level,
    ettari: r.ha,
    quota: pct(r.pct_of_declared),
    quotaValue: r.pct_of_declared ?? 0,
    appezzamenti: r.parcels,
  }));

  return (
    <section className="soft bg-white">
      <h2 className="mb-2">{titolo}</h2>
      {data.pest?.scientific_name && (
        <p className="font-s opacity-05 mb-3">
          <em>{data.pest.scientific_name}</em>
          {data.pest.eppo_code ? ` · codice EPPO ${data.pest.eppo_code}` : ""}
        </p>
      )}

      {testi.why && (
        <Fragment>
          <p className="font-m-600 mb-1">Perché guardarlo?</p>
          <p className="font-m mb-3">{testi.why}</p>
        </Fragment>
      )}

      {/* --- i tre numeri ---------------------------------------------------- */}
      <Row>
        <Col md={4} className="iiinfo-col mb-2">
          <div className="iiinfo-label font-s-label d-flex align-items-center">
            {principali?.label ?? "Colture con danno documentato"}
            <InfoPopover title="Livelli ospite" text={DEF_LIVELLI} />
          </div>
          <div className="iiinfo-value font-l-600">{pct(principali?.pct_of_declared)}</div>
          <div className="font-s opacity-05">
            {formatHa(principali?.ha)} entro {km} km
            {famiglie.permanente && famiglie.erbacea
              ? ` · frutteti ${pct(famiglie.permanente.pct_of_declared)}, erbacee ${pct(
                  famiglie.erbacea.pct_of_declared,
                )} (tutti i livelli)`
              : ""}
          </div>
        </Col>
        <Col md={4} className="iiinfo-col mb-2">
          <div className="iiinfo-label font-s-label">{secondari?.label ?? "Altre piante ospiti"}</div>
          <div className="iiinfo-value font-l-600">{pct(secondari?.pct_of_declared)}</div>
          <div className="font-s opacity-05">{formatHa(secondari?.ha)} entro {km} km</div>
        </Col>
        <Col md={4} className="iiinfo-col mb-2">
          <div className="iiinfo-label font-s-label d-flex align-items-center">
            {serbatoi?.label ?? "Serbatoi semi-naturali"}
            <InfoPopover title="Serbatoi semi-naturali" text={DEF_SERBATOI} />
          </div>
          <div className="iiinfo-value font-l-600">{pct(serbatoi?.pct_of_buffer)}</div>
          <div className="font-s opacity-05">
            bosco {formatHa(serbatoi?.bosco_ha)}, siepi e margini {formatHa(serbatoi?.elementi_ha)}
          </div>
        </Col>
      </Row>

      {/* --- le distanze, in fasce ------------------------------------------ */}
      {Object.keys(vicini).length > 0 && (
        <div className="mt-2">
          <div className="iiinfo-label font-s-label mb-1 d-flex align-items-center">
            Quanto sono vicini?
            <InfoPopover title="Distanza" text={DEF_DISTANZA} />
          </div>
          <div className="d-flex flex-wrap align-items-center">
            {Object.entries(vicini).map(([chiave, v]) => (
              <span key={chiave} className="legend-chip is-static me-3 mb-2 font-s">
                {v.label_target ?? chiave} più vicino: <strong className="ms-1">{v.label ?? "-"}</strong>
              </span>
            ))}
            {data.nearest_origin && ORIGINE[data.nearest_origin] && (
              <span className="font-s opacity-05 mb-2">{ORIGINE[data.nearest_origin]}</span>
            )}
          </div>
        </div>
      )}

      {/* --- le prime specie ospiti ----------------------------------------- */}
      {righe.length > 0 ? (
        <div className="table-scroll mt-2">
          <TableCozy columns={colonne} data={righe} options={opzioni} />
        </div>
      ) : (
        <p className="font-s mt-2 mb-0">
          <em>
            Nessuna specie ospite raggiunge i {data.min_parcels_per_row ?? 3} appezzamenti in questo
            raggio: le percentuali qui sopra contano comunque tutto.
          </em>
        </p>
      )}

      {/* --- come leggerlo ---------------------------------------------------- */}
      {(testi.how || testi.scales || testi.families_note) && (
        <Fragment>
          <p className="font-m-600 mt-3 mb-1">Come leggere questi numeri</p>
          {testi.how && <p className="font-m mb-2">{testi.how}</p>}
          {testi.scales && <p className="font-m mb-2">{testi.scales}</p>}
          {testi.families_note && <p className="font-m mb-2">{testi.families_note}</p>}
        </Fragment>
      )}
      {testi.not_risk && (
        <p className="font-m mb-2">
          <strong>{testi.not_risk}</strong>
        </p>
      )}
      {nonClass && nonClass.pct_of_declared != null && nonClass.pct_of_declared > 0 && (
        <p className="font-s mb-2">
          <em>
            Il {pct(nonClass.pct_of_declared)} della superficie dichiarata non è classificabile (
            {nonClass.label?.toLowerCase() ?? "bosco senza specie, voci generiche"}): può essere habitat, ma il
            dato non permette di attribuirlo.
          </em>
        </p>
      )}

      {/* --- limiti e fonti --------------------------------------------------- */}
      {(data.limits?.length ?? 0) > 0 && (
        <ul className="font-s mb-2 ps-3">
          {data.limits!.map((l, i) => (
            <li key={i}>{l}</li>
          ))}
        </ul>
      )}
      <p className="font-s mb-0">
        Lista delle piante ospiti versione {data.hosts_version ?? data.pest?.hosts_version ?? "-"}, dedotta
        dalle fonti
        {(data.sources?.length ?? 0) > 0 ? ": " : "."}
        {(data.sources ?? []).map((s, i) => (
          <Fragment key={s.id}>
            {i > 0 ? "; " : ""}
            {s.url ? (
              <a href={s.url} target="_blank" rel="noopener noreferrer">
                {s.citation}
              </a>
            ) : (
              s.citation
            )}
          </Fragment>
        ))}
        {(data.sources?.length ?? 0) > 0 ? "." : ""}
      </p>
    </section>
  );
}
