import { Fragment } from "react";
import { Col, Row } from "react-bootstrap";
import TableCozy, { TableColumn, TableOptions } from "./TableCozy";
import InfoPopover from "./InfoPopover";
import { COLORE_COLTURA } from "./MapLandscapeCrops";
import type { LandscapePestSeason, LandscapeSeasonClass } from "../services/model-api";

/**
 * "In questo periodo": quanti ospiti intorno al campo sono oggi nella fase che l'organismo
 * attacca, quanti ci arrivano nelle prossime settimane, e da che parte stanno.
 *
 * Generico come PestHabitatSection: disegna la risposta di /v1/landscape/pest-season con le
 * etichette del servizio. Le fasi vengono dal bollettino di produzione integrata della zona
 * (o, se il servizio bollettini non risponde, dal calendario 2026, e lo si dice).
 * Consapevolezza, non rischio: nessun semaforo, i numeri con la loro fonte.
 */

const COLORE_IN_ARRIVO = "#eda100"; // lo stesso delle erbacee sulla mappa: nessun colore nuovo

const DEF_FINESTRA =
  "Per ogni coltura ospite si legge la fase scritta nel bollettino di produzione integrata della tua zona " +
  "(l'ultimo, valido 14 giorni) e la si traduce nella scala BBCH. La si confronta poi con la finestra in cui " +
  "l'organismo trova la risorsa che attacca, tratta dalla letteratura: per la cimice i frutti e i semi in " +
  "sviluppo. \"In arrivo\" è lo stadio subito prima.";
const DEF_DIREZIONE =
  "Gli ettari sono divisi in otto spicchi intorno al campo secondo il centro di ogni appezzamento. Uno " +
  "spicchio con meno di tre appezzamenti non mostra i numeri, come le righe della tabella.";

function formatHa(ha?: number | null) {
  if (ha == null) {
    return "-";
  }
  // sotto i 10 ettari un decimale: "0 ha" per 0,4 ha direbbe il falso
  return `${ha.toLocaleString("it-IT", { maximumFractionDigits: ha < 10 ? 1 : 0 })} ha`;
}

function pct(v?: number | null) {
  return v == null ? "-" : `${v.toFixed(0)}%`;
}

function dataIt(iso?: string | null) {
  if (!iso) {
    return "-";
  }
  const [a, m, g] = iso.split("-");
  return `${g}/${m}/${a}`;
}

const ETICHETTA: Record<LandscapeSeasonClass, string> = {
  active: "Nella fase che attacca",
  arriving: "In arrivo",
  not_yet: "Non ancora",
  over: "Fase conclusa",
  no_phase: "Fase non disponibile",
  no_window: "Senza finestra documentata",
};

/** Rosa degli ettari attivi e in arrivo per spicchio: SVG semplice, niente librerie. */
function Rosa({ sectors }: { sectors: NonNullable<LandscapePestSeason["sectors"]> }) {
  const lato = 180;
  const c = lato / 2;
  const raggioMax = c - 22;
  const massimo = Math.max(1, ...sectors.map((s) => (s.active_ha ?? 0) + (s.arriving_ha ?? 0)));
  const spicchio = (i: number, r0: number, r1: number) => {
    const a0 = ((i * 45 - 20) * Math.PI) / 180;
    const a1 = ((i * 45 + 20) * Math.PI) / 180;
    const p = (a: number, r: number) => `${c + r * Math.sin(a)},${c - r * Math.cos(a)}`;
    return `M ${p(a0, r0)} L ${p(a0, r1)} A ${r1} ${r1} 0 0 1 ${p(a1, r1)} L ${p(a1, r0)} A ${r0} ${r0} 0 0 0 ${p(a0, r0)} Z`;
  };
  return (
    <svg width={lato} height={lato} viewBox={`0 0 ${lato} ${lato}`} role="img" aria-label="Rosa della direzione">
      {[0.5, 1].map((f) => (
        <circle key={f} cx={c} cy={c} r={raggioMax * f} fill="none" stroke="#ddd" />
      ))}
      {sectors.map((s, i) => {
        const att = s.active_ha ?? 0;
        const arr = s.arriving_ha ?? 0;
        const r1 = (Math.sqrt(att / massimo) || 0) * raggioMax;
        const r2 = (Math.sqrt((att + arr) / massimo) || 0) * raggioMax;
        const a = (i * 45 * Math.PI) / 180;
        return (
          <g key={s.sector}>
            {s.shown && r1 > 0.5 && <path d={spicchio(i, 0, r1)} fill={COLORE_COLTURA} />}
            {s.shown && r2 - r1 > 0.5 && <path d={spicchio(i, r1, r2)} fill={COLORE_IN_ARRIVO} />}
            <text
              x={c + (raggioMax + 12) * Math.sin(a)}
              y={c - (raggioMax + 12) * Math.cos(a) + 4}
              textAnchor="middle"
              fontSize="10"
              fill={s.shown ? "#333" : "#aaa"}
            >
              {s.sector}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

type Props = { data: LandscapePestSeason; km: number };

export default function PestSeasonBlock({ data, km }: Props) {
  if (!data.available || !data.classes) {
    return null;
  }
  const cl = data.classes;
  const settori = data.sectors ?? [];
  // ettari attivi negli spicchi che mostrano i numeri (almeno tre appezzamenti)
  const mostrati = settori.reduce((a, s) => a + (s.shown ? (s.active_ha ?? 0) : 0), 0);
  const direzioni = (data.main_directions ?? [])
    .map((d) => settori.find((s) => s.sector === d)?.label)
    .filter(Boolean) as string[];
  const fonte =
    data.source === "bulletins"
      ? `Fasi dal bollettino di produzione integrata di ${data.area ?? "zona"}${
          data.last_bulletin ? ` (ultimo del ${dataIt(data.last_bulletin.date)})` : ""
        }.`
      : `${
          data.fallback_reason === "bulletins_no_data"
            ? "Il servizio dei bollettini non ha dati per questo punto"
            : "Il servizio dei bollettini non ha risposto"
        }: fasi dal calendario 2026 alla stessa data, da prendere come indicazione.`;

  // Fuori stagione (i bollettini non escono o hanno piu' di 14 giorni) i numeri sarebbero tutti
  // zero: si dice solo questo, con la data dell'ultimo bollettino.
  // Si guarda solo agli ospiti che HANNO una finestra: se dominano quelli senza (bietola, patata...)
  // non e' fuori stagione.
  const conFinestra = 100 - cl.no_window.pct_of_hosts;
  if (conFinestra > 0 && cl.no_phase.pct_of_hosts >= 0.9 * conFinestra) {
    return (
      <div className="mt-3">
        <p className="font-m-600 mb-1 d-flex align-items-center">
          In questo periodo
          <InfoPopover title="Finestra stagionale" text={DEF_FINESTRA} />
        </p>
        <p className="font-m mb-0">
          {data.last_bulletin
            ? `L'ultimo bollettino di produzione integrata di ${data.area ?? "questa zona"} è del ${dataIt(
                data.last_bulletin.date,
              )}: `
            : "Non ci sono bollettini recenti per questa zona: "}
          per il {pct(cl.no_phase.pct_of_hosts)} delle piante ospiti non c'è una fase degli ultimi{" "}
          {data.validity_days ?? 14} giorni, e non si può dire se sono nella fase che l'organismo attacca. La
          finestra stagionale torna appena riprendono i bollettini.
        </p>
      </div>
    );
  }

  const colonne: TableColumn[] = [
    { id: "specie", headerText: "Coltura", type: "text", sortable: true },
    { id: "stato", headerText: "Adesso", type: "text", sortable: true, sortValueId: "statoOrdine" },
    { id: "fase", headerText: "Fase nel bollettino", type: "text" },
    { id: "ettari", headerText: "Ettari", type: "text", sortable: true, align: "right" },
  ];
  const ordine: LandscapeSeasonClass[] = ["active", "arriving", "not_yet", "over", "no_phase", "no_window"];
  const opzioni: TableOptions = { defaultSortCol: "stato", defaultSortDir: "asc" };
  const righe = (data.crops ?? []).map((r) => ({
    specie: r.species,
    stato: `${ETICHETTA[r.class]}${r.partial ? " (in parte)" : ""}`,
    statoOrdine: ordine.indexOf(r.class) * 1e6 - r.ha,
    fase: r.phases?.length ? `${r.phases.join(" · ")} (${dataIt(r.bulletin_date)})` : "-",
    ettari: r.ha,
  }));

  return (
    <div className="mt-3">
      <p className="font-m-600 mb-1 d-flex align-items-center">
        In questo periodo
        <InfoPopover title="Finestra stagionale" text={DEF_FINESTRA} />
      </p>
      <Row className="align-items-center">
        <Col md={4} className="iiinfo-col mb-2">
          <div className="iiinfo-label font-s-label">{cl.active.label ?? ETICHETTA.active}</div>
          <div className="iiinfo-value font-l-600">{pct(cl.active.pct_of_hosts)}</div>
          <div className="font-s opacity-05">
            {formatHa(cl.active.ha)} degli ospiti entro {km} km
            {data.partial_active_ha ? `, di cui ${formatHa(data.partial_active_ha)} solo in parte` : ""}
          </div>
        </Col>
        <Col md={4} className="iiinfo-col mb-2">
          <div className="iiinfo-label font-s-label">{cl.arriving.label ?? ETICHETTA.arriving}</div>
          <div className="iiinfo-value font-l-600">{pct(cl.arriving.pct_of_hosts)}</div>
          <div className="font-s opacity-05">
            {formatHa(cl.arriving.ha)} · non ancora {pct(cl.not_yet.pct_of_hosts)} · conclusa{" "}
            {pct(cl.over.pct_of_hosts)}
          </div>
        </Col>
        <Col md={4} className="mb-2 d-flex align-items-center">
          <Rosa sectors={settori} />
          <div className="font-s ms-2">
            <div className="d-flex align-items-center mb-1">
              Da che parte
              <InfoPopover title="Direzione" text={DEF_DIREZIONE} />
            </div>
            <div>
              <span className="legend-chip is-static font-s mb-1">
                <span className="dot me-2" data-size="10" style={{ background: COLORE_COLTURA }} /> nella fase
              </span>
            </div>
            <div>
              <span className="legend-chip is-static font-s">
                <span className="dot me-2" data-size="10" style={{ background: COLORE_IN_ARRIVO }} /> in arrivo
              </span>
            </div>
          </div>
        </Col>
      </Row>
      <p className="font-m mb-2">
        {cl.active.ha > 0 ? (
          <Fragment>
            Oggi {formatHa(cl.active.ha)} di piante ospiti intorno al campo sono nella fase che l'organismo
            attacca
            {direzioni.length
              ? `, soprattutto a ${direzioni.join(" e a ")}`
              : mostrati >= 0.75 * (data.active_ha_directional ?? cl.active.ha)
                ? ", distribuite tutto intorno senza un lato prevalente"
                : ""}
            .
          </Fragment>
        ) : (
          <Fragment>Oggi nessuna pianta ospite intorno al campo è nella fase che l'organismo attacca.</Fragment>
        )}
        {cl.no_phase.pct_of_hosts > 0
          ? ` Per il ${pct(cl.no_phase.pct_of_hosts)} degli ospiti il bollettino non riporta una fase recente ` +
            "(o non tratta quella coltura)."
          : ""}
      </p>
      {righe.length > 0 && (
        <div className="table-scroll">
          <TableCozy columns={colonne} data={righe} options={opzioni} />
        </div>
      )}
      <p className="font-s mt-2 mb-0">
        <em>
          {fonte} Colture con meno di {data.min_parcels_per_row ?? 3} appezzamenti non sono elencate, ma sono
          contate nelle percentuali.
        </em>
      </p>
    </div>
  );
}
