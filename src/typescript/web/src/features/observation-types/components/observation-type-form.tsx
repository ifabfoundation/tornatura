import React from "react";
import {
  ObservationType,
  ObservationTypeCreatePayload,
  ObservationTypeUpdatePayload,
  HarvestType,
} from "@tornatura/coreapis";
import "../../catalog-admin.css";

type ObservationTypeFormValues = {
  typology: string;
  method: string;
  category: string;
  locationAndScoreInstructions: string;
  observationHint: string;
  observationType: string;
  rangeMin: string;
  rangeMax: string;
  rangeLabels: string;
  counters: string;
  supportedHarvestCodes: string[];
};

type ObservationTypeFormProps = {
  observationType?: ObservationType;
  harvestTypes: HarvestType[];
  onSubmit: (payload: ObservationTypeCreatePayload | ObservationTypeUpdatePayload) => Promise<void>;
};

function splitCsv(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function toInitialValues(observationType?: ObservationType): ObservationTypeFormValues {
  return {
    typology: observationType?.typology ?? "",
    method: observationType?.method ?? "",
    category: observationType?.category ?? "",
    locationAndScoreInstructions: observationType?.locationAndScoreInstructions ?? "",
    observationHint: observationType?.observationHint ?? "",
    observationType: observationType?.observationType ?? "range",
    rangeMin: observationType?.rangeMin == null ? "" : String(observationType.rangeMin),
    rangeMax: observationType?.rangeMax == null ? "" : String(observationType.rangeMax),
    rangeLabels: (observationType?.rangeLabels ?? []).join(", "),
    counters: (observationType?.counters ?? []).join(", "),
    supportedHarvestCodes: observationType?.supportedHarvestCodes ?? [],
  };
}

export function ObservationTypeForm({
  observationType,
  harvestTypes,
  onSubmit,
}: ObservationTypeFormProps) {
  const [values, setValues] = React.useState<ObservationTypeFormValues>(
    toInitialValues(observationType),
  );
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState("");

  React.useEffect(() => {
    setValues(toInitialValues(observationType));
  }, [observationType]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await onSubmit({
        typology: values.typology.trim(),
        method: values.method.trim(),
        category: values.category.trim(),
        locationAndScoreInstructions: values.locationAndScoreInstructions.trim(),
        observationHint: values.observationHint.trim(),
        observationType: values.observationType,
        rangeMin: values.rangeMin === "" ? null : Number(values.rangeMin),
        rangeMax: values.rangeMax === "" ? null : Number(values.rangeMax),
        rangeLabels: splitCsv(values.rangeLabels),
        counters: splitCsv(values.counters),
        supportedHarvestCodes: values.supportedHarvestCodes,
      });
    } catch {
      setError("Salvataggio non riuscito. Controlla i dati e riprova.");
    } finally {
      setSubmitting(false);
    }
  };

  const isRange = values.observationType === "range";

  return (
    <form onSubmit={handleSubmit} className="catalog-form">
      <header className="catalog-form__header">
        <p className="catalog-form__eyebrow">Catalogo rilevamenti</p>
        <h2>{observationType ? "Modifica tipo di rilevamento" : "Nuovo tipo di rilevamento"}</h2>
        <p className="catalog-form__lead">
          Definisci cosa viene osservato, come viene valutato e per quali colture sarà disponibile.
        </p>
      </header>
      <div className="catalog-form__panel">
      <section className="catalog-form__section">
        <div className="catalog-form__section-heading">
          <h3>Identità del rilevamento</h3>
          <p>Questi dati orientano la selezione di tipologia e metodo durante il rilievo.</p>
        </div>
      <div className="row input-row">
        <div className="col-md-3">
          <label>
            Categoria
            <input
              value={values.category}
              required
              placeholder="es. Fungo"
              onChange={(event) => setValues((prev) => ({ ...prev, category: event.target.value }))}
            />
          </label>
        </div>
        <div className="col-md-3">
          <label>
            Tipologia
            <input
              value={values.typology}
              required
              placeholder="es. Peronospora"
              onChange={(event) => setValues((prev) => ({ ...prev, typology: event.target.value }))}
            />
          </label>
        </div>
        <div className="col-md-3">
          <label>
            Metodo
            <input
              value={values.method}
              required
              placeholder="es. Foglia"
              onChange={(event) => setValues((prev) => ({ ...prev, method: event.target.value }))}
            />
          </label>
        </div>
        <div className="col-md-3">
          <label>
            Formato
            <select
              value={values.observationType}
              onChange={(event) =>
                setValues((prev) => ({ ...prev, observationType: event.target.value }))
              }
            >
              <option value="range">Range</option>
              <option value="counters">Counters</option>
            </select>
          </label>
        </div>
      </div>
      </section>
      <section className="catalog-form__section">
        <div className="catalog-form__section-heading">
          <h3>Guida per l’operatore</h3>
          <p>Testi mostrati durante il flusso di rilevamento.</p>
        </div>
      <div className="row input-row">
        <div className="col-md-6">
          <label>
            Istruzioni
            <textarea
              value={values.locationAndScoreInstructions}
              required
              onChange={(event) =>
                setValues((prev) => ({
                  ...prev,
                  locationAndScoreInstructions: event.target.value,
                }))
              }
            />
          </label>
        </div>
        <div className="col-md-6">
          <label>
            Hint osservazione
            <textarea
              value={values.observationHint}
              onChange={(event) =>
                setValues((prev) => ({ ...prev, observationHint: event.target.value }))
              }
            />
          </label>
        </div>
      </div>
      </section>
      <section className="catalog-form__section">
        <div className="catalog-form__section-heading">
          <h3>Scala di valutazione</h3>
          <p>{isRange ? "Imposta l’intervallo e le etichette che aiutano a interpretarlo." : "Indica i contatori che l’operatore dovrà compilare."}</p>
        </div>
      <div className="row input-row">
        <div className="col-md-2" hidden={!isRange}>
          <label>
            Range min
            <input
              type="number"
              value={values.rangeMin}
              onChange={(event) => setValues((prev) => ({ ...prev, rangeMin: event.target.value }))}
            />
          </label>
        </div>
        <div className="col-md-2" hidden={!isRange}>
          <label>
            Range max
            <input
              type="number"
              value={values.rangeMax}
              onChange={(event) => setValues((prev) => ({ ...prev, rangeMax: event.target.value }))}
            />
          </label>
        </div>
        <div className={isRange ? "col-md-8" : "d-none"}>
          <label>
            Etichette range
            <input
              value={values.rangeLabels}
              onChange={(event) =>
                setValues((prev) => ({ ...prev, rangeLabels: event.target.value }))
              }
            />
          </label>
        </div>
        <div className={isRange ? "d-none" : "col-md-12"}>
          <label>
            Counters
            <input
              value={values.counters}
              onChange={(event) =>
                setValues((prev) => ({ ...prev, counters: event.target.value }))
              }
            />
          </label>
        </div>
      </div>
      </section>
      <section className="catalog-form__section">
        <div className="catalog-form__section-heading">
          <h3>Colture abilitate</h3>
          <p>Seleziona tutte le colture a cui applicare questo rilevamento.</p>
        </div>
      <div className="row input-row">
        <div className="col-md-12">
          <label>
            Colture supportate
            <select
              multiple
              value={values.supportedHarvestCodes}
              onChange={(event) =>
                setValues((prev) => ({
                  ...prev,
                  supportedHarvestCodes: Array.from(event.target.selectedOptions).map(
                    (option) => option.value,
                  ),
                }))
              }
            >
              {harvestTypes.map((item) => (
                <option key={item.id} value={item.code}>
                  {item.label} {item.active === false ? "(inattiva)" : ""}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>
      </section>
      {error && <div className="bbch-admin__message bbch-admin__message--error">{error}</div>}
      <footer className="catalog-form__footer">
        <button className="trnt_btn primary" type="submit" disabled={submitting}>{submitting ? "Salvataggio…" : "Salva rilevamento"}</button>
      </footer>
      </div>
    </form>
  );
}
