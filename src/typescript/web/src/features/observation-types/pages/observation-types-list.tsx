import React from "react";
import { Col, Container, Row } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import { ModalConfirm } from "../../../components/ModalConfirm";
import TableCozy, { TableColumn, TableOptions } from "../../../components/TableCozy";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { harvestTypesSelectors } from "../../harvest-types/state/harvest-types-slice";
import {
  observationTypesActions,
  observationTypesSelectors,
} from "../state/observation-types-slice";

export function ObservationTypesList() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const observationTypes = useAppSelector(observationTypesSelectors.selectObservationTypes);
  const harvestTypes = useAppSelector(harvestTypesSelectors.selectHarvestTypes);
  const [categoryFilter, setCategoryFilter] = React.useState("");
  const [typologyFilter, setTypologyFilter] = React.useState("");
  const [harvestFilter, setHarvestFilter] = React.useState("");
  const [observationTypeToDelete, setObservationTypeToDelete] = React.useState<{
    id: string;
    typology: string;
    method: string;
  } | null>(null);

  React.useEffect(() => {
    dispatch(
      headerbarActions.setTitle({
        title: "Tipi di rilevamento",
        subtitle: "Vista amministrazione",
      }),
    );
    dispatch(observationTypesActions.fetchObservationTypesAction({ page: 1, limit: 1000 }));
  }, [dispatch]);

  const categories = React.useMemo(
    () => Array.from(new Set(observationTypes.map((item) => item.category))).sort(),
    [observationTypes],
  );
  const typologies = React.useMemo(
    () => Array.from(new Set(observationTypes.map((item) => item.typology))).sort(),
    [observationTypes],
  );

  const filteredObservationTypes = React.useMemo(
    () =>
      observationTypes.filter((item) => {
        if (categoryFilter !== "" && item.category !== categoryFilter) {
          return false;
        }
        if (typologyFilter !== "" && item.typology !== typologyFilter) {
          return false;
        }
        if (
          harvestFilter !== "" &&
          !(item.supportedHarvestCodes ?? []).includes(harvestFilter)
        ) {
          return false;
        }
        return true;
      }),
    [categoryFilter, harvestFilter, observationTypes, typologyFilter],
  );

  const options: TableOptions = {
    defaultSortCol: "category",
    defaultSortDir: "asc",
  };

  const columns: TableColumn[] = [
    { headerText: "Categoria", id: "category", sortable: true, type: "text", style: "normal" },
    { headerText: "Tipologia", id: "typology", sortable: true, type: "text", style: "normal" },
    { headerText: "Metodo", id: "method", sortable: true, type: "text", style: "normal" },
    { headerText: "Formato", id: "observationType", sortable: true, type: "text", style: "normal" },
    { headerText: "Colture", id: "supportedHarvestCodes", sortable: true, type: "text", style: "normal" },
    {
      headerText: "",
      id: "edit",
      type: "button",
      style: "secondary",
      buttonText: "Apri",
      onButtonClick: (row) => navigate(`/admin/observation-types/${row.id}`),
    },
    {
      headerText: "",
      id: "delete",
      type: "button",
      style: "secondary",
      buttonText: "Elimina",
      onButtonClick: (row) => {
        setObservationTypeToDelete({
          id: row.id,
          typology: row.typology,
          method: row.method,
        });
      },
    },
  ];

  const data = filteredObservationTypes.map((item) => ({
    id: item.id,
    typology: item.typology,
    method: item.method,
    category: item.category,
    observationType: item.observationType,
    supportedHarvestCodes: (item.supportedHarvestCodes ?? []).join(", "),
  }));

  return (
    <>
      {observationTypeToDelete && (
        <ModalConfirm
          handleCancel={() => setObservationTypeToDelete(null)}
          title="Conferma eliminazione"
          content={
            <p>
              Sei sicuro di voler eliminare <strong>{observationTypeToDelete.typology}</strong>
              {" > "}
              <strong>{observationTypeToDelete.method}</strong>?
            </p>
          }
          action="Elimina"
          actionBtnClass="danger1"
          handleConfirm={async () => {
            await dispatch(
              observationTypesActions.deleteObservationTypeAction(
                observationTypeToDelete.id,
              ),
            );
            setObservationTypeToDelete(null);
            dispatch(
              observationTypesActions.fetchObservationTypesAction({ page: 1, limit: 1000 }),
            );
          }}
        />
      )}
      <section className="pb-3">
        <Container fluid className="px-0">
          <Row className="mb-4">
            <Col md={3}>
              <label>
                Categoria
                <select value={categoryFilter} onChange={(event) => setCategoryFilter(event.target.value)}>
                  <option value="">Tutte</option>
                  {categories.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>
            </Col>
            <Col md={3}>
              <label>
                Tipologia
                <select value={typologyFilter} onChange={(event) => setTypologyFilter(event.target.value)}>
                  <option value="">Tutte</option>
                  {typologies.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>
            </Col>
            <Col md={3}>
              <label>
                Coltura supportata
                <select value={harvestFilter} onChange={(event) => setHarvestFilter(event.target.value)}>
                  <option value="">Tutte</option>
                  {harvestTypes.map((item) => (
                    <option key={item.id} value={item.code}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </label>
            </Col>
            <Col md={3} className="d-flex justify-content-end align-items-end">
              <button
                className="trnt_btn primary"
                onClick={() => navigate("/admin/observation-types/new")}
              >
                Nuovo tipo rilevamento
              </button>
            </Col>
          </Row>
        </Container>
      </section>
      <section className="soft pb-3">
        <Container fluid className="px-0">
          <Row>
            <Col xl={12} style={{ overflowX: "auto" }}>
              <TableCozy columns={columns} data={data} options={options} />
            </Col>
          </Row>
        </Container>
      </section>
    </>
  );
}
