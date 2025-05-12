import { Fragment } from "react";
import TableCozy, { TableColumn, TableOptions } from "../../../components/TableCozy";
import { Detection } from "@tornatura/coreapis";


interface IDetection {
  detections: Detection[]
}

export function DetectionTableComponent({ detections }: IDetection) {

  const options: TableOptions = {
    defaultSortCol: "creationTime",
    defaultSortDir: 'desc',
  };

  const columns: TableColumn[] = [
    {
      headerText: "Data",
      id: "creationTime",
      sortable: true,
      style: "normal",
      type: "text",
    }, 
    {
      headerText: "Tipo",
      id: "type",
      sortable: true,
      style: "normal",
      type: "text",
    },
    {
      headerText: "",
      id: "note",
      sortable: false,
      style: "small-grey",
      type: "text",
    }, 
    
  ]

  const tableOptions = options;
  const tableColumns = columns;
  const data = detections.map((d) => { 
    const c = new Date(d.creationTime);
    return {
      "creationTime": c.toLocaleDateString(),
      "note": d.note,
      "type": d.type
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