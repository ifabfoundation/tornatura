import { useFormik } from "formik";
import * as Yup from "yup";

const defenseActionOptions = [
  "Acquisto di agrofarmaci",
  "Consulenze di agronomi",
  "Lavoro degli operatori per sopralluoghi e trattamenti",
  "Strumenti preventivi (es. centralina meteo, bollettini fitosanitari)",
  "Altro",
  "Nessuna",
];

export interface SignupImpactQuestionnaireFormData {
  employeeCount: string;
  revenueRange: string;
  damageIncidencePercent: string;
  defenseActions: string[];
  annualSpendAgrochemicals: string;
  annualSpendAgronomists: string;
  annualSpendOperators: string;
  annualSpendPreventiveTools: string;
  annualSpendOther: string;
  annualSpendNone: boolean;
  satisfactionEffectiveness: string;
  satisfactionCostBenefit: string;
  productionProblemOutcome: string;
  monitoredKpiCount: string;
  kpiUpdateFrequency: string;
  objectivesTimeHorizon: string;
  objectivesDifficulty: string;
  productionBonusBasis: string;
  workerPromotionCriteria: string;
  lowProductivityWorkerReassignmentTiming: string;
}

interface SignupImpactQuestionnaireStepProps {
  action: string;
  initialValues: SignupImpactQuestionnaireFormData;
  onBackClick?: () => Promise<void>;
  onNextClick: (data: SignupImpactQuestionnaireFormData) => Promise<void>;
}

const revenueOptions = [
  "Meno di 50.000 €",
  "Da 50.000 € a 100.000 €",
  "Da 100.001 € a 250.000 €",
  "Da 250.001 € a 500.000 €",
  "Da 500.001 € a 1 milione di €",
  "Da 1 milione di € a 2 milioni di €",
  "Da 2 milioni di € a 5 milioni di €",
  "Da 5 milioni di € a 10 milioni di €",
  "Da 10 milioni di € a 30 milioni di €",
  "Da 30 milioni di € a 50 milioni di €",
  "51 milioni di € o più",
];

const productionProblemOutcomeOptions = [
  "È stato risolto ma non sono stati presi ulteriori provvedimenti",
  "È stato risolto e sono stati presi ulteriori provvedimenti affinché non accadesse di nuovo",
  "È stato risolto, sono stati presi ulteriori provvedimenti affinché non accadesse di nuovo ed è stato intrapreso un continuo processo di miglioramento per prevenire problemi di questo tipo",
  "Non è stato preso alcun provvedimento",
  "Non si è mai presentato un problema nella produzione",
];

const monitoredKpiCountOptions = ["Da 1 a 2", "Da 3 a 9", "10 o più", "Nessuno"];

const kpiUpdateFrequencyOptions = [
  "Annualmente",
  "Trimestralmente",
  "Mensilmente",
  "Settimanalmente",
  "Giornalmente",
  "Ogni ora o più frequentemente",
  "Mai",
];

const objectivesTimeHorizonOptions = [
  "Breve termine (fino ad un anno)",
  "Lungo termine (più di un anno)",
  "Una combinazione di breve e lungo termine",
  "Non ci sono obiettivi di produzione",
];

const objectivesDifficultyOptions = [
  "È stato molto facile",
  "È stato abbastanza facile",
  "Non è stato né facile né difficile",
  "È stato abbastanza difficile",
  "È stato molto difficile",
];

const productionBonusBasisOptions = [
  "Sulle performance del singolo in rapporto agli obiettivi di produzione",
  "Sulla performance del team in rapporto agli obiettivi di produzione",
  "Sulla performance dello stabilimento in rapporto agli obiettivi di produzione",
  "Sulla performance di tutta l’impresa in rapporto agli obiettivi di produzione",
  "Non ci sono premi di produzione",
];

const workerPromotionCriteriaOptions = [
  "Promozioni basate solamente su performance e abilità",
  "Promozioni basate in parte su performance e abilità e in parte su altri fattori, come l’anzianità sul lavoro",
  "Promozioni basate principalmente su fattori diversi da performance e abilità, come l’anzianità sul lavoro",
  "Generalmente non sono previste promozioni",
];

const lowProductivityWorkerReassignmentTimingOptions = [
  "Entro 6 mesi dall’accertamento della scarsa produttività dell’impiegato",
  "Dopo 6 mesi dall’accertamento della scarsa produttività dell’impiegato",
  "Raramente o mai",
  "Nessun lavoratore si è rivelato di scarsa produttività",
];

export default function SignupImpactQuestionnaireStep({
  action,
  initialValues,
  onBackClick,
  onNextClick,
}: SignupImpactQuestionnaireStepProps) {
  const formik = useFormik<SignupImpactQuestionnaireFormData>({
    initialValues,
    enableReinitialize: true,
    validationSchema: Yup.object({
      employeeCount: Yup.string().required("Campo obbligatorio"),
      revenueRange: Yup.string().required("Campo obbligatorio"),
      damageIncidencePercent: Yup.number()
        .typeError("Inserisci un numero")
        .min(0, "Valore minimo 0")
        .max(100, "Valore massimo 100")
        .required("Campo obbligatorio"),
      defenseActions: Yup.array().of(Yup.string().required()).min(1, "Seleziona almeno un'opzione"),
      annualSpendAgrochemicals: Yup.string(),
      annualSpendAgronomists: Yup.string(),
      annualSpendOperators: Yup.string(),
      annualSpendPreventiveTools: Yup.string(),
      annualSpendOther: Yup.string(),
      annualSpendNone: Yup.boolean(),
      satisfactionEffectiveness: Yup.number()
        .typeError("Inserisci un numero")
        .min(1, "Valore minimo 1")
        .max(10, "Valore massimo 10")
        .required("Campo obbligatorio"),
      satisfactionCostBenefit: Yup.number()
        .typeError("Inserisci un numero")
        .min(1, "Valore minimo 1")
        .max(10, "Valore massimo 10")
        .required("Campo obbligatorio"),
      productionProblemOutcome: Yup.string().required("Campo obbligatorio"),
      monitoredKpiCount: Yup.string().required("Campo obbligatorio"),
      kpiUpdateFrequency: Yup.string().required("Campo obbligatorio"),
      objectivesTimeHorizon: Yup.string().required("Campo obbligatorio"),
      objectivesDifficulty: Yup.string().required("Campo obbligatorio"),
      productionBonusBasis: Yup.string().required("Campo obbligatorio"),
      workerPromotionCriteria: Yup.string().required("Campo obbligatorio"),
      lowProductivityWorkerReassignmentTiming: Yup.string().required("Campo obbligatorio"),
    }),
    onSubmit: async (values, { setSubmitting }) => {
      await onNextClick(values);
      setSubmitting(false);
    },
  });

  return (
    <form onSubmit={formik.handleSubmit} autoComplete="off">
      <div className="form-section">
        <div className="container px-0">
          <div className="row input-row">
            <div className="col">
              <label>
                Numero addetti ad oggi
                <input
                  id="employeeCount"
                  name="employeeCount"
                  type="number"
                  min="0"
                  placeholder="Numero addetti"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.employeeCount}
                />
              </label>
              {formik.touched.employeeCount && formik.errors.employeeCount ? (
                <div className="error">{formik.errors.employeeCount}</div>
              ) : null}
            </div>
          </div>

          <div className="row input-row">
            <div className="col">
              <label>
                Fatturato
                <select
                  id="revenueRange"
                  name="revenueRange"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.revenueRange}
                >
                  <option value="">Seleziona...</option>
                  {revenueOptions.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>
              <p className="font-s">
                Fatturato per vendita di beni e servizi della Vostra impresa nell'anno 2024?
                Includere i ricavi derivanti da: vendita di beni e/o servizi dell'impresa,
                lavorazioni eseguite per conto di terzi, vendita di prodotti rivenduti senza
                trasformazione da parte dell'impresa, prestazioni di servizi industriali
              </p>
              {formik.touched.revenueRange && formik.errors.revenueRange ? (
                <div className="error">{formik.errors.revenueRange}</div>
              ) : null}
            </div>
          </div>

          <div className="row input-row">
            <div className="col">
              <label>
                Incidenza dei danni da avversità delle piante
                <input
                  id="damageIncidencePercent"
                  name="damageIncidencePercent"
                  type="number"
                  style={{ minWidth: "180px" }}
                  min="0"
                  max="100"
                  placeholder="Percentuale"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.damageIncidencePercent}
                />
              </label>
              <p className="font-s">
                Ad oggi qual è l'incidenza di danni da malattia / insetto fitofago per le colture
                della Vostra impresa? Fate una stima basata sulla media degli ultimi 4/5 anni.
                (indicare un numero %). Per incidenza di danni si intende la percentuale di piante
                estirpate / danneggiate o la percentuale di frutti non commercializzabili per ettaro
                di terreno per flavescenza dorata, cimice asiatica, peronospora, diabrotica..
              </p>
              {formik.touched.damageIncidencePercent && formik.errors.damageIncidencePercent ? (
                <div className="error">{formik.errors.damageIncidencePercent}</div>
              ) : null}
            </div>
          </div>

          <div className="row input-row">
            <div className="col">
              <label className="mb-2">
                Attualmente quali di queste azioni state svolgendo per la difesa fitosanitaria delle
                Vostre colture?
              </label>
              {defenseActionOptions.map((option) => (
                <div className="d-flex align-items-center" key={option}>
                  <input
                    type="checkbox"
                    name="defenseActions"
                    value={option}
                    onChange={formik.handleChange}
                    onBlur={formik.handleBlur}
                    checked={formik.values.defenseActions.includes(option)}
                    className="d-inline"
                  />
                  <span className="font-m font-weight-400">{option}</span>
                </div>
              ))}
              {formik.touched.defenseActions && formik.errors.defenseActions ? (
                <div className="error">{formik.errors.defenseActions}</div>
              ) : null}
            </div>
          </div>

          <div className="row input-row">
            <div className="col">
              <label className="mb-2">
                Quanto spende la Vostra impresa annualmente per questa attività? (in Euro)
              </label>
              <div>
                <input
                  className="d-inline-block"
                  id="annualSpendAgrochemicals"
                  name="annualSpendAgrochemicals"
                  type="number"
                  min="0"
                  placeholder="Spesa in euro"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.annualSpendAgrochemicals}
                />
                <span className="ms-2">Acquisto di agrofarmaci</span>
              </div>
              <div>
                <input
                  className="d-inline-block"
                  id="annualSpendAgronomists"
                  name="annualSpendAgronomists"
                  type="number"
                  min="0"
                  placeholder="Spesa in euro"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.annualSpendAgronomists}
                />
                <span className="ms-2">Consulenze di agronomi</span>
              </div>
              <div>
                <input
                  className="d-inline-block"
                  id="annualSpendOperators"
                  name="annualSpendOperators"
                  type="number"
                  min="0"
                  placeholder="Spesa in euro"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.annualSpendOperators}
                />
                <span className="ms-2">Lavoro operatori per sopralluoghi e trattamenti</span>
              </div>
              <div>
                <input
                  className="d-inline-block"
                  id="annualSpendPreventiveTools"
                  name="annualSpendPreventiveTools"
                  type="number"
                  min="0"
                  placeholder="Spesa in euro"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.annualSpendPreventiveTools}
                />
                <span className="ms-2">Strumenti preventivi</span>
              </div>
              <div>
                <input
                  className="d-inline-block"
                  id="annualSpendOther"
                  name="annualSpendOther"
                  type="number"
                  min="0"
                  placeholder="Spesa in euro"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.annualSpendOther}
                />
                <span className="ms-2">Altro</span>
              </div>
              <div className="d-flex align-items-center">
                <input
                  id="annualSpendNone"
                  name="annualSpendNone"
                  type="checkbox"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  checked={formik.values.annualSpendNone}
                  className="d-inline"
                />
                <span className="my-2">Nessuna</span>
              </div>
            </div>
          </div>

          <div className="row input-row">
            <div className="col">
              <label>
                Soddisfazione: Inserire un punteggio per Efficacia complessiva nel ridurre le
                avversità delle piante (1-10)
                <input
                  id="satisfactionEffectiveness"
                  name="satisfactionEffectiveness"
                  type="number"
                  min="1"
                  max="10"
                  placeholder="1-10"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.satisfactionEffectiveness}
                  style={{ minWidth: "180px" }}
                />
              </label>
              {formik.touched.satisfactionEffectiveness &&
              formik.errors.satisfactionEffectiveness ? (
                <div className="error">{formik.errors.satisfactionEffectiveness}</div>
              ) : null}
            </div>
          </div>

          <div className="row input-row">
            <div className="col">
              <label>
                Soddisfazione: rapporto costo-beneficio (1-10)
                <input
                  id="satisfactionCostBenefit"
                  name="satisfactionCostBenefit"
                  type="number"
                  min="1"
                  max="10"
                  placeholder="1-10"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.satisfactionCostBenefit}
                  style={{ minWidth: "180px" }}
                />
              </label>
              {formik.touched.satisfactionCostBenefit && formik.errors.satisfactionCostBenefit ? (
                <div className="error">{formik.errors.satisfactionCostBenefit}</div>
              ) : null}
            </div>
          </div>

          <div className="row input-row">
            <div className="col">
              <label>
                Quando si presenta un problema di produzione, cosa avviene?
                <select
                  id="productionProblemOutcome"
                  name="productionProblemOutcome"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.productionProblemOutcome}
                >
                  <option value="">Seleziona tra le seguenti opzioni...</option>
                  {productionProblemOutcomeOptions.map((item, index) => (
                    <option key={item} value={item}>
                      Opzione {index + 1}
                    </option>
                  ))}
                </select>
              </label>
              <p>Opzioni</p>
              {productionProblemOutcomeOptions.map((item, index) => (
                <p key={index}>
                  <span>{`${index + 1}. ${item}`}</span>
                </p>
              ))}
              {formik.touched.productionProblemOutcome && formik.errors.productionProblemOutcome ? (
                <div className="error">{formik.errors.productionProblemOutcome}</div>
              ) : null}
            </div>
          </div>

          <div className="row input-row">
            <div className="col">
              <label>
                Quanti indicatori di performance sono monitorati?
                <select
                  id="monitoredKpiCount"
                  name="monitoredKpiCount"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.monitoredKpiCount}
                >
                  <option value="">Seleziona...</option>
                  {monitoredKpiCountOptions.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>
              {formik.touched.monitoredKpiCount && formik.errors.monitoredKpiCount ? (
                <div className="error">{formik.errors.monitoredKpiCount}</div>
              ) : null}
            </div>
          </div>

          <div className="row input-row">
            <div className="col">
              <label>
                Frequenza di aggiornamento degli indicatori di performance
                <select
                  id="kpiUpdateFrequency"
                  name="kpiUpdateFrequency"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.kpiUpdateFrequency}
                >
                  <option value="">Seleziona...</option>
                  {kpiUpdateFrequencyOptions.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>
              {formik.touched.kpiUpdateFrequency && formik.errors.kpiUpdateFrequency ? (
                <div className="error">{formik.errors.kpiUpdateFrequency}</div>
              ) : null}
            </div>
          </div>

          <div className="row input-row">
            <div className="col">
              <label>
                Orizzonte temporale dei principali obiettivi di produzione
                <select
                  id="objectivesTimeHorizon"
                  name="objectivesTimeHorizon"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.objectivesTimeHorizon}
                >
                  <option value="">Seleziona...</option>
                  {objectivesTimeHorizonOptions.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>
              {formik.touched.objectivesTimeHorizon && formik.errors.objectivesTimeHorizon ? (
                <div className="error">{formik.errors.objectivesTimeHorizon}</div>
              ) : null}
            </div>
          </div>

          <div className="row input-row">
            <div className="col">
              <label>
                Quanto è stato facile/difficile perseguire gli obiettivi?
                <select
                  id="objectivesDifficulty"
                  name="objectivesDifficulty"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.objectivesDifficulty}
                >
                  <option value="">Seleziona...</option>
                  {objectivesDifficultyOptions.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>
              {formik.touched.objectivesDifficulty && formik.errors.objectivesDifficulty ? (
                <div className="error">{formik.errors.objectivesDifficulty}</div>
              ) : null}
            </div>
          </div>

          <div className="row input-row">
            <div className="col">
              <label>
                Su cosa sono principalmente basati i premi di produzione?
                <select
                  id="productionBonusBasis"
                  name="productionBonusBasis"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.productionBonusBasis}
                >
                  <option value="">Seleziona...</option>
                  {productionBonusBasisOptions.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>
              {formik.touched.productionBonusBasis && formik.errors.productionBonusBasis ? (
                <div className="error">{formik.errors.productionBonusBasis}</div>
              ) : null}
            </div>
          </div>

          <div className="row input-row">
            <div className="col">
              <label>
                Criterio principale per le promozioni dei lavoratori
                <select
                  id="workerPromotionCriteria"
                  name="workerPromotionCriteria"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.workerPromotionCriteria}
                >
                  <option value="">Seleziona...</option>
                  {workerPromotionCriteriaOptions.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>
              {formik.touched.workerPromotionCriteria && formik.errors.workerPromotionCriteria ? (
                <div className="error">{formik.errors.workerPromotionCriteria}</div>
              ) : null}
            </div>
          </div>

          <div className="row input-row">
            <div className="col">
              <label>
                Quando un lavoratore con scarsa produttività viene spostato dal suo ruolo?
                <select
                  id="lowProductivityWorkerReassignmentTiming"
                  name="lowProductivityWorkerReassignmentTiming"
                  onChange={formik.handleChange}
                  onBlur={formik.handleBlur}
                  value={formik.values.lowProductivityWorkerReassignmentTiming}
                >
                  <option value="">Seleziona...</option>
                  {lowProductivityWorkerReassignmentTimingOptions.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>
              {formik.touched.lowProductivityWorkerReassignmentTiming &&
              formik.errors.lowProductivityWorkerReassignmentTiming ? (
                <div className="error">{formik.errors.lowProductivityWorkerReassignmentTiming}</div>
              ) : null}
            </div>
          </div>
        </div>
      </div>

      <div className="buttons-wrapper mt-4 text-center">
        <button className="trnt_btn secondary" type="button" onClick={onBackClick}>
          Indietro
        </button>
        <button type="submit" className="trnt_btn primary" disabled={formik.isSubmitting}>
          {formik.isSubmitting ? "Caricamento..." : action}
        </button>
      </div>
    </form>
  );
}
