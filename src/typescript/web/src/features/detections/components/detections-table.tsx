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
      headerText: "Tipologia",
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
    {
      headerText: "Dettaglio",
      id: "summary",
      sortable: true,
      style: "normal",
      type: "text",
    },
    
  ]

  const tableOptions = options;
  const tableColumns = columns;
  const data = detections.map((d) => { 
    const c = new Date(d.creationTime);
    let summary = "";
    if (d.details.desease) {
      summary = d.details.desease;
    } else if (d.details.insect) {
      summary = d.details.insect;
    } else if (d.details.parasite) {
      summary = d.details.parasite;
    }

    return {
      "creationTime": c.toLocaleString('it-IT'),
      "note": d.note,
      "type": d.type,
      "summary": summary,
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