import React from "react";
import {
  ObservationType,
  ObservationTypeCreatePayload,
  ObservationTypeUpdatePayload,
  HarvestType,
} from "@tornatura/coreapis";

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

  React.useEffect(() => {
    setValues(toInitialValues(observationType));
  }, [observationType]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
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
  };

  return (
    <form onSubmit={handleSubmit} className="form-section">
      <div className="row input-row">
        <div className="col-md-3">
          <label>
            Categoria
            <input
              value={values.category}
              onChange={(event) => setValues((prev) => ({ ...prev, category: event.target.value }))}
            />
          </label>
        </div>
        <div className="col-md-3">
          <label>
            Tipologia
            <input
              value={values.typology}
              onChange={(event) => setValues((prev) => ({ ...prev, typology: event.target.value }))}
            />
          </label>
        </div>
        <div className="col-md-3">
          <label>
            Metodo
            <input
              value={values.method}
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

      <div className="row input-row">
        <div className="col-md-6">
          <label>
            Istruzioni
            <input
              value={values.locationAndScoreInstructions}
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
            <input
              value={values.observationHint}
              onChange={(event) =>
                setValues((prev) => ({ ...prev, observationHint: event.target.value }))
              }
            />
          </label>
        </div>
      </div>

      <div className="row input-row">
        <div className="col-md-2">
          <label>
            Range min
            <input
              type="number"
              value={values.rangeMin}
              onChange={(event) => setValues((prev) => ({ ...prev, rangeMin: event.target.value }))}
            />
          </label>
        </div>
        <div className="col-md-2">
          <label>
            Range max
            <input
              type="number"
              value={values.rangeMax}
              onChange={(event) => setValues((prev) => ({ ...prev, rangeMax: event.target.value }))}
            />
          </label>
        </div>
        <div className="col-md-4">
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
        <div className="col-md-4">
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

      <div className="row input-row">
        <div className="col-md-10">
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
        <div className="col-md-2 d-flex align-items-end">
          <button className="trnt_btn primary" type="submit">
            Salva
          </button>
        </div>
      </div>
    </form>
  );
}
