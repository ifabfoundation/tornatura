import React from "react";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import TableCozy, { TableColumn, TableOptions } from "../../../components/TableCozy";
import { AdminPagination } from "../../../components/AdminPagination";
import { userSelectors } from "../state/user-slice";
import "../../catalog-admin.css";


export function UserTable() {
  const dispatch = useAppDispatch();
  const users = useAppSelector(userSelectors.selectAllUsers);
  const [currentPage, setCurrentPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(10);

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Utenti", subtitle: "Vista amministrazione" }));
  }, [dispatch]);

  const options: TableOptions = {
    defaultSortCol: "lastName",
    defaultSortDir: "asc",
  };

  const paginatedUsers = users.slice((currentPage - 1) * pageSize, currentPage * pageSize);

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
    }
  ];

  return (
    <div className="catalog-page">
      <header className="catalog-page__intro">
        <div>
          <p className="catalog-page__eyebrow">Amministrazione</p>
          <h2>Utenti</h2>
          <p>Consulta gli account registrati e i relativi recapiti.</p>
        </div>
      </header>
      <section className="catalog-page__table mt-4">
        <div className="catalog-page__table-scroll">
          <TableCozy columns={columns} data={paginatedUsers} options={options} />
        </div>
        <AdminPagination
          currentPage={currentPage}
          pageSize={pageSize}
          pageSizeOptions={[10, 25, 50]}
          totalItems={users.length}
          onPageChange={setCurrentPage}
          onPageSizeChange={(size) => {
            setPageSize(size);
            setCurrentPage(1);
          }}
        />
      </section>
    </div>
  );
}
