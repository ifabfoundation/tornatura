import React from "react";
import { useNavigate } from "react-router-dom";
import { useParams, useSearchParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { observationTypesSelectors } from "../../observation-types/state/observation-types-slice";
import { detectionTypesSelectors } from "../state/detection-types-slice";
import { detectionsSelectors } from "../../detections/state/detections-slice";
import { Container, Row, Col } from "react-bootstrap";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import TableCozy, { TableColumn, TableOptions } from "../../../components/TableCozy";

export function DetectionTypeDetail() {
  const dispatch = useAppDispatch();
  const [searchParams] = useSearchParams();
  const [tableIsOpen, setTableIsOpen] = React.useState<boolean>(false);
  const { companyId, fieldId, typeId } = useParams();

  const detectionType = useAppSelector((state) =>
    detectionTypesSelectors.selectDetectionTypeById(state, typeId ?? "default"),
  );

  const observationType = useAppSelector((state) =>
    observationTypesSelectors.selectObservationTypeById(state, detectionType.observationTypeId),
  );

  const detections = useAppSelector((state) =>
    detectionsSelectors.selectDetectionByTypeId(state, typeId ?? "default"),
  );
  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Focus Rilevamento", subtitle: "Subtitle" }));
  }, []);

  const navigate = useNavigate();

  const notes = [];
  detections.forEach((detection) => {
    console.log("detection", detection);
    // @ts-ignore
    if (detection.detectionData.notes && detection.detectionData.notes != "") {
      // @ts-ignore
      notes.push(detection.detectionData.notes);
    }
  });
  const photos = [];
  detections.forEach((detection) => {
    // @ts-ignore
    if (detection.detectionData.photos && detection.detectionData.photos.length > 0) {
      // @ts-ignore
      detection.detectionData.photos.forEach((photo) => {
        photos.push(photo);
      });
    }
  });

  function DetectionsTable() {
    const tableOptions: TableOptions = {
      defaultSortCol: "date",
      defaultSortDir: "desc",
    };

    const tableColumns: TableColumn[] = [
      {
        headerText: "Data",
        id: "detectionTime",
        sortable: true,
        style: "normal",
        type: "text",
      },
      {
        headerText: "BBCH",
        id: "bbch",
        sortable: true,
        style: "normal",
        type: "text",
      },
      {
        headerText: "Osservazioni",
        id: "pointsNum",
        sortable: true,
        style: "normal",
        type: "text",
      },
      {
        headerText: "% piante",
        id: "stat1",
        sortable: true,
        style: "normal",
        type: "text",
      },
      {
        headerText: "Intensità media",
        id: "stat2",
        sortable: true,
        style: "normal",
        type: "text",
      },
      {
        headerText: "Fotografie",
        id: "photosNum",
        sortable: true,
        style: "normal",
        type: "text",
      },
      {
        headerText: "Indice di malattia",
        id: "diseaseIndex",
        sortable: true,
        style: "normal",
        type: "text",
      },
    ];

    const tableData = detections.map((detection) => {
      const dd = detection.detectionData;
      return {
        detectionTime: new Date(detection.detectionTime).toLocaleDateString(),
        bbch: dd.bbch ?? "-",
        pointsNum: dd.points.length ?? "-",
        stat1: "Stat xyz",
        stat2: "Stat xyz",
        photosNum: dd.photos ? dd.photos.length : 0,
        diseaseIndex: "Stat xyz",
      };
    });
    return <TableCozy columns={tableColumns} data={tableData} options={tableOptions} />;
  }

  return (
    <div>
      <p>
        pagina per {observationType.typology} / {observationType.method} con numero{" "}
        {detections.length} detections
      </p>

      <Container>
        <Row className="mt-4">
          <Col xl={12}>
            <section className="soft">
              <div className="d-flex align-items-start justify-content-between">
                <Container className="px-0">
                  <Row>
                    <Col md={6} xl={9}>
                      <div className="font-l-600">{`${observationType.typology}  ›  ${observationType.method}`}</div>
                    </Col>
                    <Col md={6} xl={3}>
                      <button
                        className="trnt_btn accent wide"
                        data-type="round"
                        onClick={() =>
                          navigate(`/companies/${companyId}/fields/${fieldId}/new-detection`, {
                            state: { typeId: typeId },
                          })
                        }
                      >
                        + Rilevamento {observationType.typology}
                      </button>
                    </Col>
                  </Row>
                </Container>
              </div>
              <div className="mt-4">
                <Container className="px-0">
                  <Row className="mt-4">
                    <Col md={3}>
                      <p className="font-s-label upper">Rilevamenti</p>
                      <div className="font-l-600">
                        {detections.length}
                        <button
                          className="trnt_btn slim-y narrow-x outlined font-s-600 text-transform-none px-2"
                          data-type="rounded"
                          onClick={() => setTableIsOpen(!tableIsOpen)}
                        >{` ${tableIsOpen ? "Nascondi" : "Espandi"} lista `}</button>
                      </div>
                    </Col>
                    <Col md={3}>
                      <p className="font-s-label upper">Fotografie</p>
                      <div className="font-l-600">{photos.length}</div>
                    </Col>
                    <Col md={3}>
                      <p className="font-s-label upper">Note</p>
                      <div className="font-l-600">{notes.length}</div>
                    </Col>
                  </Row>
                  {tableIsOpen && <DetectionsTable />}
                </Container>
              </div>
            </section>
          </Col>
        </Row>
        <Row className="mt-4">
          <Col xl={12}>
            <section className="soft">
              <Row>
                <Col lg={6}>
                  <h4>Detections</h4>
                </Col>
                <Col lg={6}>
                  <h4>Map</h4>
                </Col>
              </Row>
            </section>
          </Col>
        </Row>
      </Container>
    </div>
  );
}
