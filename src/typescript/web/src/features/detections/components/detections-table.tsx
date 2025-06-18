import { Fragment } from "react";
import TableCozy, { TableColumn, TableOptions } from "../../../components/TableCozy";
import { Detection, DetectionMutationPayload } from "@tornatura/coreapis";
import React from "react";
import { DetectionUpdateModalForm } from "./detection-update-modal-form";
import { useParams } from "react-router-dom";
import { detectionsActions } from "../state/detections-slice";
import { useAppDispatch } from "../../../hooks";


interface IDetection {
  detections: Detection[]
}

export function DetectionTableComponent({ detections }: IDetection) {
  const dispatch = useAppDispatch();
  const { companyId } = useParams();
  const [modalOpen, setModalOpen] = React.useState(false);
  const [modal, setModal] = React.useState<any>({});

  const options: TableOptions = {
    defaultSortCol: "detectionTime",
    defaultSortDir: 'desc'
  };

  const columns: TableColumn[] = [
    {
      headerText: "Data",
      id: "detectionTime",
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
    {
      headerText: "Azione",
      id: "button_update",
      buttonText: "Modifica data",
      type: "button",
      onButtonClick: (data) => {
        console.log("Button clicked for row:", data);
        const d = detections.find((det) => det.id === data.id);
        setModal({component: DetectionUpdateModalForm, componentProps: {
          handleModalCancel: () => setModalOpen(false),
          handleFormSubmitted: (data: any) => {
            if (companyId && d) {
              const payload: DetectionMutationPayload = {
                type: d.type,
                note: d.note,
                details: d.details,
                detectionTime: data.detectionTime,
                photos: d.photos.map((p) => {
                  const parts = p.split("?")[0];
                  return {
                    category: "data",
                    name: parts.split("/").pop() ?? "",
                  };
                }),
                position: d.position,
              }
              dispatch(detectionsActions.updateDetectionAction({
                orgId: companyId,
                fieldId: d.agrifieldId,
                detectionId: d.id,
                body: payload
              }))
            }
            setModalOpen(false);
          }
        }});
        setModalOpen(true);
      }
    },
  ]

  const tableOptions = options;
  const tableColumns = columns;
  const data = detections.map((d) => { 
    const c = new Date(d.detectionTime);
    let summary = "";
    if (d.details.desease) {
      summary = d.details.desease;
    } else if (d.details.insect) {
      summary = d.details.insect;
    } else if (d.details.parasite) {
      summary = d.details.parasite;
    }

    return {
      "detectionTime": c.toLocaleString('it-IT'),
      "note": d.note,
      "type": d.type,
      "summary": summary,
      "id": d.id
    }
  });

  return (
   <Fragment>
      {modalOpen && <modal.component  {...modal.componentProps} />}
      <TableCozy
        columns={tableColumns}
        data={data}
        options={tableOptions}
      />
   </Fragment>
  );
}