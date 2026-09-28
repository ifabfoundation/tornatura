import React from "react";
import { HarvestType, HarvestTypeCreatePayload, HarvestTypeUpdatePayload } from "@tornatura/coreapis";
import "../../catalog-admin.css";

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
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState("");

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
    setSubmitting(true);
    setError("");
    try {
      await onSubmit(payload);
    } catch {
      setError("Salvataggio non riuscito. Controlla i dati e riprova.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="catalog-form">
      <header className="catalog-form__header">
        <p className="catalog-form__eyebrow">Registro colture</p>
        <h2>{harvestType ? "Modifica coltura" : "Aggiungi una coltura"}</h2>
        <p className="catalog-form__lead">
          Il codice identifica stabilmente la coltura nei campi e nelle configurazioni di rilevamento.
        </p>
      </header>
      <div className="catalog-form__panel">
        <section className="catalog-form__section">
          <div className="catalog-form__section-heading">
            <h3>Identità e disponibilità</h3>
            <p>Usa un codice breve, in minuscolo e con underscore se necessario.</p>
          </div>
          <div className="row input-row">
            <div className="col-md-3">
              <label>
                Codice
                <input
                  value={values.code}
                  required
                  disabled={Boolean(harvestType)}
                  placeholder="es. vite"
                  onChange={(event) => setValues((prev) => ({ ...prev, code: event.target.value }))}
                />
              </label>
            </div>
            <div className="col-md-4">
              <label>
                Etichetta
                <input
                  value={values.label}
                  required
                  placeholder="es. Vite"
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
          </div>
        </section>
        {error && <div className="bbch-admin__message bbch-admin__message--error">{error}</div>}
        <footer className="catalog-form__footer">
          <button className="trnt_btn primary" type="submit" disabled={submitting}>{submitting ? "Salvataggio…" : "Salva coltura"}</button>
        </footer>
      </div>
    </form>
  );
}
