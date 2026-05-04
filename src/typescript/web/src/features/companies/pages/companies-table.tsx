import React from "react";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { companiesSelectors } from "../state/companies-slice";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import TableCozy, { TableColumn, TableOptions } from "../../../components/TableCozy";
import { Col, Container, Row } from "react-bootstrap";


export function CompanyTable() {
  const dispatch = useAppDispatch();
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
  ];

  const data = companies.map((c) => {
    return {
      "orgId": c.orgId,
      "name": c.name,
      "piva": c.piva,
      "email": c.contacts?.email ?? "",
      "phone": c.contacts?.phone ?? "",
      "creationTime": formatDateTime(c.creationTime),
      "creationTimeRaw": c.creationTime ?? 0,
    };
  });

  return (
    <div>
      <section className="soft pb-3">
        <div className="">
          <Container fluid className="px-0">
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
