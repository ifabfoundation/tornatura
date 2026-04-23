import React from "react";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import TableCozy, { TableColumn, TableOptions } from "../../../components/TableCozy";
import { feedbacksSelectors } from "../state/feedbacks-slice";
import { userSelectors } from "../../users/state/user-slice";



export function FeedbackTable() {
  const dispatch = useAppDispatch();
  const users = useAppSelector(userSelectors.selectAllUsers);
  const feedbacks = useAppSelector(feedbacksSelectors.selectAllFeedbacks);

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Feedback", subtitle: "Vista amministrazione" }));
  }, []);

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

  return (
    <TableCozy columns={columns} data={data} options={options} />
  );
}
