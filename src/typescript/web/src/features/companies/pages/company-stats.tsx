import React from "react";
import { Col, Container, Row } from "react-bootstrap";
import { useNavigate, useParams } from "react-router-dom";
import {
  OrganizationStatsResponse,
  OrganizationsApi,
} from "@tornatura/coreapis";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { companiesActions, companiesSelectors } from "../state/companies-slice";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { getCoreApiConfiguration } from "../../../services/utils";
import TableCozy, { TableColumn, TableOptions } from "../../../components/TableCozy";

function formatDate(value?: number | null) {
  if (!value) {
    return "N/D";
  }

  return new Date(value).toLocaleDateString("it-IT", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

function valOrEmpty(value: string | number | null | undefined, fallback = "–") {
  if (value === null || value === undefined) {
    return fallback;
  }
  if (typeof value === "string" && value.trim() === "") {
    return fallback;
  }
  return value;
}

export function CompanyStats() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { companyId } = useParams();
  const company = useAppSelector((state) =>
    companiesSelectors.selectCompanybyId(state, companyId ?? "default"),
  );
  const [stats, setStats] = React.useState<OrganizationStatsResponse | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (companyId) {
      dispatch(companiesActions.getCompanyAction(companyId));
    }
  }, [companyId, dispatch]);

  React.useEffect(() => {
    if (!companyId) {
      return;
    }

    let ignore = false;

    const loadStats = async () => {
      setLoading(true);
      setError(null);
      try {
        const apiConfig = await getCoreApiConfiguration();
        const organizationsApi = new OrganizationsApi(apiConfig);
        const response = await organizationsApi.getOrganizationStats(companyId, 3);
        if (!ignore) {
          setStats(response.data);
        }
      } catch (err) {
        if (!ignore) {
          console.error("Error loading organization stats:", err);
          setError("Errore nel caricamento delle statistiche.");
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    };

    loadStats();

    return () => {
      ignore = true;
    };
  }, [companyId]);

  React.useEffect(() => {
    const companyName = company?.name ?? stats?.organization.name ?? "Azienda";
    dispatch(
      headerbarActions.setTitle({
        title: `Statistiche ${companyName}`,
        subtitle: "Ultimi 3 mesi",
      }),
    );
  }, [company?.name, dispatch, stats?.organization.name]);

  const totalDetectionCount = React.useMemo(
    () => stats?.agrifields.reduce((sum, field) => sum + field.detectionCount, 0) ?? 0,
    [stats],
  );

  const avgDetectionPerAgrifield = React.useMemo(() => {
    if (!stats || stats.agrifieldCount === 0) {
      return "0";
    }
    return (totalDetectionCount / stats.agrifieldCount).toFixed(1);
  }, [stats, totalDetectionCount]);

  const mostActiveAgrifield = React.useMemo(() => {
    if (!stats || stats.agrifields.length === 0) {
      return "–";
    }
    return [...stats.agrifields].sort((a, b) => b.detectionCount - a.detectionCount)[0]?.name ?? "–";
  }, [stats]);

  const columns: TableColumn[] = [
    {
      headerText: "Campo",
      id: "name",
      sortable: true,
      type: "text",
    },
    {
      headerText: "Coltura",
      id: "harvest",
      sortable: true,
      type: "text",
    },
    {
      headerText: "Data creazione",
      id: "creationTime",
      sortValueId: "creationTimeRaw",
      sortable: true,
      type: "text",
    },
    {
      headerText: "Rilevamenti ultimi 3 mesi",
      id: "detectionCount",
      sortable: true,
      type: "text",
      align: "center",
    },
    {
      headerText: "",
      id: "openField",
      type: "button",
      style: "secondary",
      buttonText: "Apri campo",
      onButtonClick: (row) => navigate(`/companies/${companyId}/fields/${row.id}`),
    },
  ];

  const options: TableOptions = {
    defaultSortCol: "detectionCount",
    defaultSortDir: "desc",
  };

  const data =
    stats?.agrifields.map((field) => ({
      id: field.id,
      name: field.name,
      harvest: valOrEmpty(field.harvest),
      creationTime: formatDate(field.creationTime),
      creationTimeRaw: field.creationTime ?? 0,
      detectionCount: field.detectionCount,
    })) ?? [];

  if (loading) {
    return <div className="narrow-container my-5">Caricamento statistiche...</div>;
  }

  if (error) {
    return <div className="narrow-container my-5 color-red">{error}</div>;
  }

  if (!stats) {
    return <div className="narrow-container my-5">Nessuna statistica disponibile.</div>;
  }

  return (
    <Container fluid>
      <Row>
        <Col xs={12}>
          <section className="soft bg-white">
            <Row>
              <Col xl={12} className="mb-4">
                <div className="font-l-600">{stats.organization.name}</div>
                <div className="font-s-label mt-2">
                  Finestra analizzata: ultimi {stats.window.months} mesi
                </div>
              </Col>

              <Col className="col-6 col-lg-3 iiinfo-col mt-2 mb-2">
                <div className="iiinfo-label font-s-label">Campi</div>
                <div className="iiinfo-value font-l-600">{stats.agrifieldCount}</div>
              </Col>
              <Col className="col-6 col-lg-3 iiinfo-col mt-2 mb-2">
                <div className="iiinfo-label font-s-label">Colture distinte</div>
                <div className="iiinfo-value font-l-600">{stats.distinctHarvestCount}</div>
              </Col>
              <Col className="col-6 col-lg-3 iiinfo-col mt-2 mb-2">
                <div className="iiinfo-label font-s-label">Rilevamenti totali</div>
                <div className="iiinfo-value font-l-600">{totalDetectionCount}</div>
              </Col>
              <Col className="col-6 col-lg-3 iiinfo-col mt-2 mb-2">
                <div className="iiinfo-label font-s-label">Media per campo</div>
                <div className="iiinfo-value font-l-600">{avgDetectionPerAgrifield}</div>
              </Col>
              <Col className="col-12 col-lg-6 iiinfo-col mt-2 mb-2">
                <div className="iiinfo-label font-s-label">Campo più monitorato</div>
                <div className="iiinfo-value font-l-600">{mostActiveAgrifield}</div>
              </Col>
              <Col className="col-12 col-lg-6 iiinfo-col mt-2 mb-2">
                <div className="iiinfo-label font-s-label">Colture presenti</div>
                <div className="iiinfo-value font-l-600">
                  {stats.distinctHarvests.length > 0 ? stats.distinctHarvests.join(", ") : "–"}
                </div>
              </Col>
            </Row>
          </section>
        </Col>
      </Row>

      <Row className="mt-4">
        <Col xs={12}>
          <section className="soft pb-3">
            <Container fluid className="px-0">
              <Row>
                <Col xl={12} style={{ overflowX: "auto" }}>
                  <TableCozy columns={columns} data={data} options={options} />
                </Col>
              </Row>
            </Container>
          </section>
        </Col>
      </Row>
    </Container>
  );
}
