import React from "react";
import { useNavigate } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { harvestTypesSelectors } from "../../harvest-types/state/harvest-types-slice";
import { BbchGroup, BbchScale, createBbchScale, listBbchScales } from "../services/bbch-scales-api";
import { bbchs } from "../../detections/pages/bbch";
import "../../catalog-admin.css";

type LegacyBbchStage = {
  name: string;
  value: string;
  thumbnail?: string;
  icon?: string | false;
};

type LegacyBbchGroup = {
  name: string;
  icon?: string | false;
  items: Record<string, LegacyBbchStage>;
};

type LegacyBbchCatalogue = { data: Record<string, LegacyBbchGroup> };

export function BbchScalesList() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const harvestTypes = useAppSelector(harvestTypesSelectors.selectHarvestTypes);
  const [scales, setScales] = React.useState<BbchScale[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState("");
  const [importing, setImporting] = React.useState(false);

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Scale BBCH", subtitle: "Vista amministrazione" }));
    listBbchScales()
      .then(setScales)
      .catch(() => setError("Impossibile caricare il catalogo BBCH."))
      .finally(() => setLoading(false));
  }, [dispatch]);

  const scaleByHarvest = React.useMemo(
    () => new Map(scales.map((scale) => [scale.harvestCode, scale])),
    [scales],
  );
  const hasLegacyScalesToImport = Object.keys(bbchs).some(
    (code) => harvestTypes.some((harvest) => harvest.code === code) && !scaleByHarvest.has(code),
  );

  const importLegacyCatalog = async () => {
    setImporting(true);
    setError("");
    try {
      const existingCodes = new Set(scales.map((scale) => scale.harvestCode));
      const registeredCodes = new Set(harvestTypes.map((item) => item.code));
      const sourceEntries = Object.entries(bbchs).filter(
        ([code]) => code !== "melo" && registeredCodes.has(code),
      );
      for (const [harvestCode, catalogue] of sourceEntries) {
        if (existingCodes.has(harvestCode)) continue;
        const groups: BbchGroup[] = Object.entries((catalogue as LegacyBbchCatalogue).data).map(
          ([groupKey, groupValue], groupIndex) => ({
            code: groupKey.replace("bbch_", ""),
            name: groupValue.name,
            icon: typeof groupValue.icon === "string" ? groupValue.icon : null,
            sortOrder: groupIndex,
            stages: Object.values(groupValue.items).map((stage, stageIndex) => ({
              code: stage.value,
              name: stage.name,
              thumbnail: stage.thumbnail || null,
              icon: typeof stage.icon === "string" ? stage.icon : null,
              sortOrder: stageIndex,
            })),
          }),
        );
        await createBbchScale({ harvestCode, groups });
        existingCodes.add(harvestCode);
      }
      if (registeredCodes.has("melo") && !existingCodes.has("melo") && existingCodes.has("pero")) {
        await createBbchScale({ harvestCode: "melo", sourceHarvestCode: "pero" });
      }
      setScales(await listBbchScales());
    } catch {
      setError("Importazione interrotta. Le scale già importate sono state conservate; puoi riprovare.");
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="catalog-page bbch-admin">
      <header className="catalog-page__intro">
        <div>
          <p className="catalog-page__eyebrow">Configurazione</p>
          <h2>Scale fenologiche BBCH</h2>
          <p>Configura stadi, descrizioni e miniature per ciascuna coltura.</p>
        </div>
        {hasLegacyScalesToImport && (
          <button className="trnt_btn outlined" type="button" disabled={importing} onClick={importLegacyCatalog}>
            {importing ? "Importazione…" : "Importa catalogo attuale"}
          </button>
        )}
      </header>

      {error && <div className="bbch-admin__message bbch-admin__message--error">{error}</div>}
      {loading ? (
        <p className="catalog-form__hint mt-4">Caricamento scale…</p>
      ) : (
        <div className="catalog-page__table bbch-scale-list">
          {harvestTypes.map((harvest) => {
            const scale = scaleByHarvest.get(harvest.code);
            const stageCount = scale?.groups.reduce((total, group) => total + group.stages.length, 0) ?? 0;
            return (
              <button
                type="button"
                className="bbch-scale-row"
                key={harvest.id}
                onClick={() => navigate(`/admin/bbch-scales/${harvest.code}`)}
              >
                <span className="bbch-scale-row__identity">
                  <strong>{harvest.label}</strong>
                  <small>{harvest.code}</small>
                </span>
                <span className={`bbch-scale-row__status ${scale ? "is-ready" : ""}`}>
                  {scale ? (scale.sourceHarvestCode ? `Usa ${scale.sourceHarvestCode}` : `${stageCount} stadi`) : "Da configurare"}
                </span>
                <span className="bbch-scale-row__action">Gestisci →</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
