import React from "react";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { companiesSelectors } from "../state/companies-slice";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import TableCozy, { TableColumn, TableOptions } from "../../../components/TableCozy";
import { useNavigate } from "react-router-dom";


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
    onRowClick: (rowData) => navigate(`/companies/${rowData.orgId}`),
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
      headerText: "Creazione",
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
    <TableCozy columns={columns} data={data} options={options} />
  );
}
