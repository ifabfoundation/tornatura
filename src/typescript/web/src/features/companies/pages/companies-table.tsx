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
      headerText: "Nome",
      id: "name",
      sortable: true,
      style: "normal",
      type: "text",
    }, {
      headerText: "",
      id: "description",
      sortable: false,
      style: "small-grey",
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
    }
  ]

  const tableOptions = options;
  const tableColumns = columns;
  const data = companies.map((c) => { 
    return {
      "name": c.name,
      "description": c.description,
      "email": c.contacts.email,
      "phone": c.contacts.phone
    }
  } );

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