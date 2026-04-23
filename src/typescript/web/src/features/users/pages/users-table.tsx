import React from "react";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import TableCozy, { TableColumn, TableOptions } from "../../../components/TableCozy";
import { userSelectors } from "../state/user-slice";


export function UserTable() {
  const dispatch = useAppDispatch();
  const users = useAppSelector(userSelectors.selectAllUsers);

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Utenti", subtitle: "Vista amministrazione" }));
  }, []);

  const options: TableOptions = {
    defaultSortCol: "lastName",
    defaultSortDir: "asc",
  };

  const columns: TableColumn[] = [
    {
      headerText: "Nome",
      id: "firstName",
      sortable: true,
      style: "normal",
      type: "text",
    },   {
      headerText: "Cognome",
      id: "lastName",
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
      headerText: "Tipo",
      id: "accountType",
      sortable: true,
      style: "normal",
      type: "text",
    }
  ];

  return (
    <TableCozy columns={columns} data={users} options={options} />
  );
}
