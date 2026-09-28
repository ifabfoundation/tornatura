import React from "react";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import TableCozy, { TableColumn, TableOptions } from "../../../components/TableCozy";
import { AdminPagination } from "../../../components/AdminPagination";
import { feedbacksSelectors } from "../state/feedbacks-slice";
import { userSelectors } from "../../users/state/user-slice";
import "../../catalog-admin.css";



export function FeedbackTable() {
  const dispatch = useAppDispatch();
  const users = useAppSelector(userSelectors.selectAllUsers);
  const feedbacks = useAppSelector(feedbacksSelectors.selectAllFeedbacks);
  const [currentPage, setCurrentPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(10);

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Feedback", subtitle: "Vista amministrazione" }));
  }, [dispatch]);

  const options: TableOptions = {
    defaultSortCol: "creationTime",
    defaultSortDir: "desc",
  };

  const columns: TableColumn[] = [
    {
      headerText: "Categoria",
      id: "category",
      sortable: true,
      style: "normal",
      type: "text",
    },
    {
      headerText: "",
      id: "feedback",
      sortable: false,
      style: "normal",
      type: "text",
    },
    {
      headerText: "Autore",
      id: "author",
      sortable: true,
      style: "normal",
      type: "text",
    },
    {
      headerText: "Data Invio",
      id: "creationTime",
      sortValueId: "creationTimeRaw",
      sortable: true,
      style: "normal",
      type: "text",
    }
  ];

  const data = feedbacks.map((f) => {
    const d = new Date(f.creationTime);
    const u = users.find((u) => u.id === f.author);
    const c = u ? u.email : "N/A";

    return {
      "category": f.category,
      "feedback": f.feedback,
      "author": c,
      "creationTime": d.toLocaleString('it-IT'),
      "creationTimeRaw": f.creationTime,
    };
  } );
  const paginatedData = data.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  return (
    <div className="catalog-page">
      <header className="catalog-page__intro">
        <div>
          <p className="catalog-page__eyebrow">Amministrazione</p>
          <h2>Feedback</h2>
          <p>Consulta le segnalazioni inviate dagli utenti, con autore e data di ricezione.</p>
        </div>
      </header>
      <section className="catalog-page__table mt-4">
        <div className="catalog-page__table-scroll">
          <TableCozy columns={columns} data={paginatedData} options={options} />
        </div>
        <AdminPagination
          currentPage={currentPage}
          pageSize={pageSize}
          pageSizeOptions={[10, 25, 50]}
          totalItems={data.length}
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
