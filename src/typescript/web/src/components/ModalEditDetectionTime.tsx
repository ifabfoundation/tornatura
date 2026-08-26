import React from "react";
import Modal from "./Modal";

interface ModalEditDetectionTimeProps {
  handleCancel: () => void;
  /** Valore attuale del rilevamento, in millisecondi. */
  detectionTime: number;
  /**
   * Vero se il rilevamento fa parte di una sessione multipla: quei rilevamenti
   * condividono una sola data, quindi si muovono insieme e va detto prima di confermare.
   */
  isSession?: boolean;
  /**
   * Quanti rilevamenti verranno spostati, se lo sappiamo. E' un minimo, non una
   * certezza: il conteggio viene dallo store del browser, che con un link diretto alla
   * pagina puo' non avere ancora tutti i rilevamenti del campo. Il server sposta sempre
   * tutta la sessione, quindi qui il numero si mostra solo quando e' informativo.
   */
  affectedCount?: number;
  /**
   * Salva. Se torna una stringa, e' un messaggio d'errore: la modale resta aperta e lo
   * mostra, invece di chiudersi facendo credere che il salvataggio sia andato a buon fine.
   */
  handleConfirm: (detectionTime: number) => void | Promise<string | void>;
}

/**
 * Converte i millisecondi nel formato che vuole `<input type="datetime-local">`
 * (`YYYY-MM-DDTHH:mm`), nell'ora locale di chi guarda.
 *
 * `toISOString()` non va bene: restituisce UTC, quindi in Italia mostrerebbe un
 * orario spostato di una o due ore rispetto a quello scritto nella tabella.
 */
function toPickerDateTime(ms: number): string {
  const d = new Date(ms);
  const pad = (n: number) => String(n).padStart(2, "0");
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` +
    `T${pad(d.getHours())}:${pad(d.getMinutes())}`
  );
}

export function ModalEditDetectionTime({
  handleCancel,
  detectionTime,
  isSession = false,
  affectedCount = 0,
  handleConfirm,
}: ModalEditDetectionTimeProps) {
  const [value, setValue] = React.useState(() => toPickerDateTime(detectionTime));
  const [error, setError] = React.useState("");
  const [saving, setSaving] = React.useState(false);

  // Non si puo' scegliere un momento futuro: un rilevamento non puo' essere ancora
  // avvenuto. Il server accetta una tolleranza di 24 ore per gli orologi sfasati,
  // ma qui non c'e' motivo di offrirla.
  const maxValue = toPickerDateTime(Date.now());

  const onConfirm = async () => {
    if (value === "") {
      setError("Inserisci data e ora del rilevamento.");
      return;
    }
    const parsed = new Date(value).getTime();
    if (Number.isNaN(parsed)) {
      setError("Data non valida.");
      return;
    }
    if (parsed > Date.now()) {
      setError("Il rilevamento non può essere nel futuro.");
      return;
    }
    setSaving(true);
    const message = await handleConfirm(parsed);
    setSaving(false);
    if (message) {
      setError(message);
    }
  };

  return (
    <Modal closeModal={handleCancel} title="Data del rilevamento">
      <section>
        <div className="font-m">
          {isSession && (
            <div className="mb-3">
              {affectedCount > 1
                ? `Questo rilevamento fa parte di una sessione di ${affectedCount} rilevamenti fatti nella stessa uscita: la data verrà corretta per tutti.`
                : "Questo rilevamento fa parte di una sessione di rilevamenti fatti nella stessa uscita: la data verrà corretta per tutti."}
            </div>
          )}
          <div className="input-row position-relative">
            <label className="position-relative">Quando è stato fatto il rilevamento?</label>
            <input
              type="datetime-local"
              className="pe-2"
              style={{ width: "100%" }}
              value={value}
              max={maxValue}
              disabled={saving}
              onChange={(event) => {
                setValue(event.target.value);
                setError("");
              }}
            />
            <small className="d-block mt-2 text-muted">
              Cambia solo quando il rilevamento è avvenuto. La data in cui è stato inserito nel
              sistema resta registrata e non viene toccata.
            </small>
          </div>
          {error !== "" && <div className="mt-3 font-m-600 text-danger">{error}</div>}
        </div>
        <hr />
        <div className="buttons-wrapper text-center">
          <button className="trnt_btn secondary" onClick={handleCancel} disabled={saving}>
            Annulla
          </button>
          <button className="trnt_btn primary" onClick={onConfirm} disabled={saving}>
            {saving ? "Salvataggio…" : "Salva"}
          </button>
        </div>
      </section>
    </Modal>
  );
}
