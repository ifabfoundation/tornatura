import React, { Fragment } from "react";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { companiesSelectors } from "../state/companies-slice";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import TableCozy, { TableColumn, TableOptions } from "../../../components/TableCozy";


export function CompanyTable() {
  const dispatch = useAppDispatch();
  const companies = useAppSelector(companiesSelectors.selectAllCompanies);

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({title: "Aziende", subtitle: "Subtitle"}));
  }, []); 

  const options: TableOptions = {
    defaultSortCol: "name",
    defaultSortDir: 'desc',
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
      headerText: "Regione sede legale",
      id: "state",
      sortable: true,
      style: "normal",
      type: "text",
    },
    {
      headerText: "Comune sede legale",
      id: "city",
      sortable: true,
      style: "normal",
      type: "text",
    },
    {
      headerText: "Legale Rappresentante",
      id: "rapresentative",
      sortable: true,
      style: "normal",
      type: "text",
    },
    {
      headerText: "Contatto Rappresentante",
      id: "rapresentativeContact",
      sortable: true,
      style: "normal",
      type: "text",
    }
  ]

  const tableOptions = options;
  const tableColumns = columns;
  const data = companies.map((c) => { 
    return {
      "name": c.name,
      "piva": c.piva,
      "state": c.office.state,
      "city": c.office.city,
      "rapresentative": c.rapresentative,
      "rapresentativeContact": c.rapresentativeContact,
      "email": c.contacts.email,
      "phone": c.contacts.phone
    }
  });

  return (
   <Fragment>
      <TableCozy
        columns={tableColumns}
        data={data}
        options={tableOptions}
      />
   </Fragment>
  );
}