import React from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { harvestTypesSelectors } from "../../harvest-types/state/harvest-types-slice";
import {
  BbchGroup,
  BbchScale,
  createBbchScale,
  deleteBbchScale,
  duplicateBbchScale,
  getBbchScale,
  listBbchScales,
  updateBbchScale,
  uploadBbchThumbnail,
} from "../services/bbch-scales-api";
import "../../catalog-admin.css";

const OBJECT_STORAGE_ENDPOINT = process.env.REACT_APP_OBJECT_STORAGE_ENDPOINT;

const newGroup = (): BbchGroup => ({ code: "", name: "", sortOrder: 0, stages: [] });

export function BbchScaleDetail() {
  const { harvestCode = "" } = useParams();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const harvestTypes = useAppSelector(harvestTypesSelectors.selectHarvestTypes);
  const harvest = harvestTypes.find((item) => item.code === harvestCode);
  const [scale, setScale] = React.useState<BbchScale | null>(null);
  const [groups, setGroups] = React.useState<BbchGroup[]>([]);
  const [sourceCode, setSourceCode] = React.useState("");
  const [availableScales, setAvailableScales] = React.useState<BbchScale[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [message, setMessage] = React.useState("");

  const load = React.useCallback(async () => {
    setLoading(true);
    const all = await listBbchScales();
    setAvailableScales(all.filter((item) => item.harvestCode !== harvestCode));
    try {
      const current = await getBbchScale(harvestCode);
      setScale(current);
      setGroups(current.groups);
      setSourceCode(current.sourceHarvestCode ?? "");
    } catch {
      setScale(null);
      setGroups([]);
    } finally {
      setLoading(false);
    }
  }, [harvestCode]);

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: `BBCH · ${harvest?.label ?? harvestCode}`, subtitle: "Vista amministrazione" }));
    load().catch(() => {
      setMessage("Impossibile caricare la scala BBCH.");
      setLoading(false);
    });
  }, [dispatch, harvest?.label, harvestCode, load]);

  const updateGroup = (index: number, updater: (group: BbchGroup) => BbchGroup) => {
    setGroups((current) => current.map((group, itemIndex) => itemIndex === index ? updater(group) : group));
  };

  const moveGroup = (index: number, direction: -1 | 1) => {
    setGroups((current) => {
      const target = index + direction;
      if (target < 0 || target >= current.length) return current;
      const next = [...current];
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  };

  const moveStage = (groupIndex: number, stageIndex: number, direction: -1 | 1) => {
    updateGroup(groupIndex, (current) => {
      const target = stageIndex + direction;
      if (target < 0 || target >= current.stages.length) return current;
      const stages = [...current.stages];
      [stages[stageIndex], stages[target]] = [stages[target], stages[stageIndex]];
      return { ...current, stages };
    });
  };

  const handleCreate = async () => {
    setSaving(true);
    setMessage("");
    try {
      const created = await createBbchScale({
        harvestCode,
        sourceHarvestCode: sourceCode || undefined,
        groups: sourceCode ? [] : groups,
      });
      setScale(created);
      setGroups(created.groups);
      setMessage("Scala BBCH creata.");
    } catch {
      setMessage("Creazione non riuscita. Controlla i dati e riprova.");
    } finally {
      setSaving(false);
    }
  };

  const handleDuplicate = async () => {
    if (!scale?.sourceHarvestCode) return;
    setSaving(true);
    try {
      const duplicated = await duplicateBbchScale(scale.sourceHarvestCode, harvestCode);
      setScale(duplicated);
      setGroups(duplicated.groups);
      setSourceCode("");
      setMessage("Scala duplicata: ora puoi personalizzarla.");
    } catch {
      setMessage("Duplicazione non riuscita.");
    } finally {
      setSaving(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage("");
    try {
      const normalized = groups.map((group, groupIndex) => ({
        ...group,
        sortOrder: groupIndex,
        stages: group.stages.map((stage, stageIndex) => ({ ...stage, sortOrder: stageIndex })),
      }));
      const updated = await updateBbchScale(harvestCode, normalized);
      setScale(updated);
      setGroups(updated.groups);
      setMessage("Modifiche salvate.");
    } catch {
      setMessage("Salvataggio non riuscito. Verifica che codici e nomi siano compilati.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm("Eliminare questa configurazione BBCH? Le immagini nello storage non verranno rimosse.")) return;
    setSaving(true);
    try {
      await deleteBbchScale(harvestCode);
      navigate("/admin/bbch-scales");
    } catch {
      setMessage("La scala non può essere eliminata perché è usata da un’altra coltura.");
      setSaving(false);
    }
  };

  if (loading) return <p>Caricamento…</p>;

  const inherited = Boolean(scale?.sourceHarvestCode);

  return (
    <div className="catalog-page bbch-admin bbch-admin--detail">
      <button className="bbch-admin__back" type="button" onClick={() => navigate("/admin/bbch-scales")}>← Tutte le scale</button>
      <header className="catalog-form__header bbch-detail__header">
        <div>
          <p className="catalog-page__eyebrow">Scala fenologica</p>
          <h2>{harvest?.label ?? harvestCode}</h2>
          <p>{inherited ? `Questa coltura usa la scala di ${scale?.sourceHarvestCode}.` : "Organizza gruppi, stadi e miniature mostrate durante il rilevamento."}</p>
        </div>
      </header>

      <div className="catalog-form__panel bbch-editor-panel">
        {message && <div className="bbch-admin__message">{message}</div>}

        {!scale && (
          <section className="bbch-empty-config">
            <div>
              <h3>Crea la configurazione</h3>
              <p>Parti da una scala vuota oppure collega temporaneamente quella di un’altra coltura.</p>
            </div>
            <label>
              Scala di partenza
              <select value={sourceCode} onChange={(event) => setSourceCode(event.target.value)}>
                <option value="">Scala vuota</option>
                {availableScales.map((item) => <option key={item.harvestCode} value={item.harvestCode}>{item.harvestCode}</option>)}
              </select>
            </label>
            <button className="trnt_btn primary" type="button" disabled={saving} onClick={handleCreate}>Crea scala</button>
          </section>
        )}

        {scale && (
          <>
            <div className={`bbch-editor ${inherited ? "is-readonly" : ""}`}>
              {groups.map((group, groupIndex) => (
                <section className="bbch-group" key={`${group.code}-${groupIndex}`}>
              <div className="bbch-group__header">
                <span className="bbch-group__number">{String(groupIndex + 1).padStart(2, "0")}</span>
                <label>Codice gruppo<input value={group.code} disabled={inherited} onChange={(event) => updateGroup(groupIndex, (current) => ({ ...current, code: event.target.value }))} /></label>
                <label className="bbch-group__name">Nome gruppo<input value={group.name} disabled={inherited} onChange={(event) => updateGroup(groupIndex, (current) => ({ ...current, name: event.target.value }))} /></label>
                {!inherited && <div className="bbch-admin__row-actions">
                  <button type="button" className="bbch-admin__text-action" disabled={groupIndex === 0} onClick={() => moveGroup(groupIndex, -1)}>↑</button>
                  <button type="button" className="bbch-admin__text-action" disabled={groupIndex === groups.length - 1} onClick={() => moveGroup(groupIndex, 1)}>↓</button>
                  <button type="button" className="bbch-admin__text-action is-danger" onClick={() => setGroups((current) => current.filter((_, index) => index !== groupIndex))}>Rimuovi</button>
                </div>}
              </div>
              <div className="bbch-stage-list">
                {group.stages.map((stage, stageIndex) => (
                  <div className="bbch-stage-row" key={`${stage.code}-${stageIndex}`}>
                    <input aria-label="Codice stadio" value={stage.code} disabled={inherited} placeholder="00" onChange={(event) => updateGroup(groupIndex, (current) => ({ ...current, stages: current.stages.map((item, index) => index === stageIndex ? { ...item, code: event.target.value } : item) }))} />
                    <input aria-label="Nome stadio" value={stage.name} disabled={inherited} placeholder="Descrizione dello stadio" onChange={(event) => updateGroup(groupIndex, (current) => ({ ...current, stages: current.stages.map((item, index) => index === stageIndex ? { ...item, name: event.target.value } : item) }))} />
                    <div className="bbch-stage-row__thumbnail">
                      {stage.thumbnail ? <img src={`${OBJECT_STORAGE_ENDPOINT}/public/bbchs/${stage.thumbnail}`} alt="" /> : <span>Nessuna immagine</span>}
                      {!inherited && <label className="bbch-upload">Carica<input type="file" accept="image/png,image/jpeg,image/webp,image/gif" onChange={async (event) => {
                        const file = event.target.files?.[0];
                        if (!file) return;
                        const uploaded = await uploadBbchThumbnail(file);
                        updateGroup(groupIndex, (current) => ({ ...current, stages: current.stages.map((item, index) => index === stageIndex ? { ...item, thumbnail: uploaded.name } : item) }));
                      }} /></label>}
                    </div>
                    {!inherited && <div className="bbch-admin__row-actions">
                      <button type="button" className="bbch-admin__text-action" disabled={stageIndex === 0} onClick={() => moveStage(groupIndex, stageIndex, -1)}>↑</button>
                      <button type="button" className="bbch-admin__text-action" disabled={stageIndex === group.stages.length - 1} onClick={() => moveStage(groupIndex, stageIndex, 1)}>↓</button>
                      <button type="button" className="bbch-admin__text-action is-danger" onClick={() => updateGroup(groupIndex, (current) => ({ ...current, stages: current.stages.filter((_, index) => index !== stageIndex) }))}>Rimuovi</button>
                    </div>}
                  </div>
                ))}
              </div>
              {!inherited && <button type="button" className="bbch-admin__add" onClick={() => updateGroup(groupIndex, (current) => ({ ...current, stages: [...current.stages, { code: "", name: "", sortOrder: current.stages.length }] }))}>+ Aggiungi stadio</button>}
                </section>
              ))}
              {!inherited && <button type="button" className="bbch-admin__add bbch-admin__add--group" onClick={() => setGroups((current) => [...current, { ...newGroup(), sortOrder: current.length }])}>+ Aggiungi gruppo</button>}
            </div>
            <footer className="bbch-editor-panel__footer">
              <button type="button" className="bbch-admin__text-action is-danger" disabled={saving} onClick={handleDelete}>Elimina configurazione BBCH</button>
              {inherited ? (
                <button className="trnt_btn primary" type="button" disabled={saving} onClick={handleDuplicate}>Duplica e personalizza</button>
              ) : (
                <button className="trnt_btn primary" type="button" disabled={saving} onClick={handleSave}>{saving ? "Salvataggio…" : "Salva modifiche"}</button>
              )}
            </footer>
          </>
        )}
      </div>
    </div>
  );
}
