import React, { Fragment } from "react";
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
    dispatch(headerbarActions.setTitle({title: "Feedbacks", subtitle: "Subtitle"}));
  }, []); 

  const options: TableOptions = {
    defaultSortCol: "name",
    defaultSortDir: 'desc',
  };

  const columns: TableColumn[] = [
    {
      headerText: "Categoria",
      id: "category",
      sortable: true,
      style: "normal",
      type: "text",
    }, {
      headerText: "",
      id: "feedback",
      sortable: false,
      style: "small-grey",
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
      sortable: true,
      style: "normal",
      type: "text",
    }
  ]

  const tableOptions = options;
  const tableColumns = columns;
  const data = feedbacks.map((f) => { 
    const d = new Date(f.creationTime);
    const u = users.find((u) => u.id === f.author);
    const c = u ? u.email : "N/A";

    return {
      "category": f.category,
      "feedback": f.feedback,
      "author": c,
      "creationTime": d.toLocaleString('it-IT'),
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