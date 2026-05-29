import React from "react";
import { HarvestType, HarvestTypeCreatePayload, HarvestTypeUpdatePayload } from "@tornatura/coreapis";

type HarvestTypeFormValues = {
  code: string;
  label: string;
  active: boolean;
  sortOrder: string;
};

type HarvestTypeFormProps = {
  harvestType?: HarvestType;
  onSubmit: (payload: HarvestTypeCreatePayload | HarvestTypeUpdatePayload) => Promise<void>;
};

function toInitialValues(harvestType?: HarvestType): HarvestTypeFormValues {
  return {
    code: harvestType?.code ?? "",
    label: harvestType?.label ?? "",
    active: harvestType?.active !== false,
    sortOrder: String(harvestType?.sortOrder ?? 0),
  };
}

export function HarvestTypeForm({ harvestType, onSubmit }: HarvestTypeFormProps) {
  const [values, setValues] = React.useState<HarvestTypeFormValues>(toInitialValues(harvestType));

  React.useEffect(() => {
    setValues(toInitialValues(harvestType));
  }, [harvestType]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const payload = {
      code: values.code.trim(),
      label: values.label.trim(),
      active: values.active,
      sortOrder: Number(values.sortOrder || 0),
    };
    await onSubmit(payload);
  };

  return (
    <form onSubmit={handleSubmit} className="form-section">
      <div className="row input-row">
        <div className="col-md-3">
          <label>
            Codice
            <input
              value={values.code}
              disabled={Boolean(harvestType)}
              onChange={(event) => setValues((prev) => ({ ...prev, code: event.target.value }))}
            />
          </label>
        </div>
        <div className="col-md-4">
          <label>
            Etichetta
            <input
              value={values.label}
              onChange={(event) => setValues((prev) => ({ ...prev, label: event.target.value }))}
            />
          </label>
        </div>
        <div className="col-md-2">
          <label>
            Ordine
            <input
              type="number"
              value={values.sortOrder}
              onChange={(event) =>
                setValues((prev) => ({ ...prev, sortOrder: event.target.value }))
              }
            />
          </label>
        </div>
        <div className="col-md-2">
          <label>
            Stato
            <select
              value={values.active ? "active" : "inactive"}
              onChange={(event) =>
                setValues((prev) => ({ ...prev, active: event.target.value === "active" }))
              }
            >
              <option value="active">Attiva</option>
              <option value="inactive">Inattiva</option>
            </select>
          </label>
        </div>
        <div className="col-md-1 d-flex align-items-end">
          <button className="trnt_btn primary" type="submit">
            Salva
          </button>
        </div>
      </div>
    </form>
  );
}
