import React from "react";
import { Col, Container, Row } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import TableCozy, { TableColumn, TableOptions } from "../../../components/TableCozy";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { harvestTypesActions, harvestTypesSelectors } from "../state/harvest-types-slice";
import "../../catalog-admin.css";

function formatDateTime(value?: number) {
  if (!value) {
    return "N/D";
  }
  return new Date(value).toLocaleString("it-IT");
}

export function HarvestTypesList() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const harvestTypes = useAppSelector(harvestTypesSelectors.selectHarvestTypes);

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Colture", subtitle: "Vista amministrazione" }));
    dispatch(harvestTypesActions.fetchHarvestTypesAction({ includeInactive: true }));
  }, [dispatch]);

  const options: TableOptions = {
    defaultSortCol: "sortOrderRaw",
    defaultSortDir: "asc",
  };

  const columns: TableColumn[] = [
    { headerText: "Codice", id: "code", sortable: true, type: "text", style: "normal" },
    { headerText: "Etichetta", id: "label", sortable: true, type: "text", style: "normal" },
    { headerText: "Stato", id: "activeLabel", sortable: true, type: "text", style: "normal" },
    {
      headerText: "Ordine",
      id: "sortOrder",
      sortValueId: "sortOrderRaw",
      sortable: true,
      type: "text",
      style: "normal",
    },
    {
      headerText: "Aggiornato",
      id: "lastUpdateTime",
      sortValueId: "lastUpdateTimeRaw",
      sortable: true,
      type: "text",
      style: "normal",
    },
    {
      headerText: "",
      id: "edit",
      type: "button",
      style: "secondary",
      buttonText: "Apri",
      onButtonClick: (row) => navigate(`/admin/harvest-types/${row.id}`),
    },
    {
      headerText: "",
      id: "toggle",
      type: "button",
      style: "secondary",
      buttonText: "Attiva/Disattiva",
      onButtonClick: async (row) => {
        await dispatch(
          harvestTypesActions.updateHarvestTypeAction({
            harvestTypeId: row.id,
            body: { active: !row.activeRaw },
          }),
        );
        dispatch(harvestTypesActions.fetchHarvestTypesAction({ includeInactive: true }));
      },
    },
  ];

  const data = harvestTypes.map((item) => ({
    id: item.id,
    code: item.code,
    label: item.label,
    activeLabel: item.active === false ? "Inattiva" : "Attiva",
    activeRaw: item.active !== false,
    sortOrder: String(item.sortOrder ?? 0),
    sortOrderRaw: item.sortOrder ?? 0,
    lastUpdateTime: formatDateTime(item.lastUpdateTime),
    lastUpdateTimeRaw: item.lastUpdateTime ?? 0,
  }));

  return (
    <div className="catalog-page">
      <header className="catalog-page__intro">
        <div>
          <p className="catalog-page__eyebrow">Configurazione</p>
          <h2>Registro delle colture</h2>
          <p>Gestisci i codici disponibili per i campi, l’ordine di visualizzazione e lo stato.</p>
        </div>
        <button className="trnt_btn primary catalog-page__action" onClick={() => navigate("/admin/harvest-types/new")}>
          Nuova coltura
        </button>
      </header>
      <section className="catalog-page__table mt-4">
        <Container fluid className="px-0">
          <Row>
            <Col xl={12} style={{ overflowX: "auto" }}>
              <TableCozy columns={columns} data={data} options={options} />
            </Col>
          </Row>
        </Container>
      </section>
    </div>
  );
}
