import React from "react";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { companiesSelectors } from "../state/companies-slice";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import TableCozy, { TableColumn, TableOptions } from "../../../components/TableCozy";
import { Col, Container, Row } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import Icon from "../../../components/Icon";

function escapeCsvValue(value: unknown) {
  const normalizedValue = String(value ?? "");
  return `"${normalizedValue.replace(/"/g, '""')}"`;
}


export function CompanyTable() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const companies = useAppSelector(companiesSelectors.selectAllCompanies);

  const formatDateTime = (value?: number) => {
    if (!value) {
      return "N/D";
    }

    return new Date(value).toLocaleString("it-IT", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Aziende", subtitle: "Vista amministrazione" }));
  }, []);

  const options: TableOptions = {
    defaultSortCol: "creationTime",
    defaultSortDir: "desc",
  };

  const columns: TableColumn[] = [
    {
      headerText: "Ragione Sociale",
      id: "name",
      sortable: true,
      style: "normal",
      type: "text",
    },
    {
      headerText: "Partita Iva",
      id: "piva",
      sortable: true,
      style: "normal",
      type: "text",
    },
    {
      headerText: "Email",
      id: "email",
      sortable: true,
      style: "normal",
      type: "text",
    },
    {
      headerText: "Telefono",
      id: "phone",
      sortable: true,
      style: "normal",
      type: "text",
    },
    {
      headerText: "Data Di Registrazione",
      id: "creationTime",
      sortValueId: "creationTimeRaw",
      sortable: true,
      style: "normal",
      type: "text",
    },
    {
      headerText: "Statistiche",
      id: "stats",
      type: "button",
      style: "secondary",
      buttonText: "Visualizza",
      onButtonClick: (row) => navigate(`/admin/companies/${row.orgId}/stats`),
    },
  ];

  const data = companies.map((c) => {
    return {
      orgId: c.orgId,
      name: c.name,
      piva: c.piva,
      email: c.contacts?.email ?? "",
      phone: c.contacts?.phone ?? "",
      creationTime: formatDateTime(c.creationTime),
      creationTimeRaw: c.creationTime ?? 0,
    };
  });

  const handleCsvDownload = () => {
    const csvHeaders = columns
      .filter((column) => column.type === "text")
      .map((column) => ({ id: column.id, headerText: column.headerText }));
    const sortedData = [...data].sort((left, right) => right.creationTimeRaw - left.creationTimeRaw);
    const csvRows = [
      csvHeaders.map((column) => escapeCsvValue(column.headerText)).join(","),
      ...sortedData.map((row) =>
        csvHeaders.map((column) => escapeCsvValue(row[column.id] ?? "")).join(","),
      ),
    ];
    const csvContent = `\uFEFF${csvRows.join("\n")}`;
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const today = new Date().toISOString().slice(0, 10);

    link.href = url;
    link.download = `aziende-${today}.csv`;
    link.click();

    URL.revokeObjectURL(url);
  };

  return (
    <div>
      <section className="soft pb-3">
        <div className="">
          <Container fluid className="px-0">
            <Row className="mb-3">
              <Col xl={12} className="d-flex justify-content-end">
                <button
                  type="button"
                  className="trnt_btn narrow-x slim-y outlined ps-1 type-rounded"
                  onClick={handleCsvDownload}
                >
                  <Icon iconName={"download"} color={"black"} />
                  CSV
                </button>
              </Col>
            </Row>
            <Row>
              <Col xl={12} className="mt-0" style={{ overflowX: "auto" }}>
                <TableCozy columns={columns} data={data} options={options} />
              </Col>
            </Row>
          </Container>
        </div>
      </section>
    </div>
  );
}
