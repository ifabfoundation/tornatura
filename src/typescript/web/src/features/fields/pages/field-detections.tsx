import { useNavigate, useParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import React, { Fragment } from "react";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { Card, Col, Container, Row } from "react-bootstrap";
import { detectionsSelectors } from "../../detections/state/detections-slice";
import { GradientLineChart } from "../../../components/GradientLineChart";
import { detectionTypesActions, detectionTypesSelectors } from "../../detection-types/state/detection-types-slice";

function formatDate(value: number | string | undefined | null) {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "-";
  }
  return date.toLocaleDateString("it-IT");
}

export function FieldDetections() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { fieldId, companyId } = useParams();
  const detections = useAppSelector((state) =>
    detectionsSelectors.selectDetectionbyFieldId(state, fieldId ?? "default")
  );
  const detectionTypes = useAppSelector((state) =>
    detectionTypesSelectors.selectDetectionTypesByField(state, fieldId ?? "default")
  );

  const detectionTypeById = React.useMemo(() => {
    return new Map(detectionTypes.map((item) => [item.id, item]));
  }, [detectionTypes]);

  const groupedDetections = React.useMemo(() => {
    const groups = new Map<
      string,
      {
        typology: string;
        method: string;
        detectionTypeId?: string;
        items: typeof detections;
      }
    >();

    detections.forEach((item) => {
      const detectionType = detectionTypeById.get(item.detectionTypeId);
      const typology = detectionType?.typology ?? "Senza tipologia";
      const method = detectionType?.method ?? "Senza metodo";
      const key = `${typology}__${method}`;
      if (!groups.has(key)) {
        groups.set(key, {
          typology,
          method,
          detectionTypeId: detectionType?.id ?? item.detectionTypeId,
          items: [],
        });
      }
      groups.get(key)?.items.push(item);
    });

    return Array.from(groups.values()).sort((a, b) => {
      const typologyCompare = a.typology.localeCompare(b.typology);
      if (typologyCompare !== 0) {
        return typologyCompare;
      }
      return a.method.localeCompare(b.method);
    });
  }, [detections, detectionTypeById]);

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Tutti i rilevamenti", subtitle: "Subtitle" }));
  }, []);

  React.useEffect(() => {
    if (companyId && fieldId) {
      dispatch(detectionTypesActions.fetchDetectionTypesAction({ orgId: companyId, fieldId }));
    }
  }, [companyId, fieldId, dispatch]);

  return (
    <Fragment>
      <GradientLineChart
        height={200}
        padding={50}
        strokeWidth={20}
        dotSize={14}
        data={[
          { x: 0, y: 10, color: "#42C318" },
          { x: 2, y: 40, color: "#FFB290" },
          { x: 5, y: 25, color: "#42C318" },
          { x: 8, y: 60, color: "#FF4D4D" },
          { x: 9, y: 70, color: "#A10505" },
        ]}
      />

      <div className="my-5"></div>

      <Container>
        <Row>
          <Col>
            <div className="cardlet">
              <div className="cardlet-header">RILEVAMENTI</div>
              <div className="cardlet-content">{detections.length}</div>
            </div>
          </Col>
          <Col>
            <a
              className="cardlet-button"
              onClick={() => navigate(`/companies/${companyId}/fields/${fieldId}/new-detection`)}
            >
              <span className="d-md-none">+</span>
              <span className="d-none d-md-inline">+ Nuovo Rilevamento</span>
            </a>
          </Col>
        </Row>
        <Row className="mt-4">
          {groupedDetections.length === 0 && (
            <Col>
              <div className="text-muted">Nessun rilevamento disponibile.</div>
            </Col>
          )}
          {groupedDetections.map((group) => (
            <Col key={`${group.typology}-${group.method}`} xl={6}>
              <Card className="mb-4">
                <div className="cardlet-header">
                  <span className="title">
                    {group.typology} - {group.method}
                  </span>
                  <button
                    className="trnt_btn slim-y narrow-x primary"
                    onClick={() =>
                      navigate(`/companies/${companyId}/fields/${fieldId}/new-detection`, {
                        state: { typology: group.typology, method: group.method },
                      })
                    }
                  >
                    + Nuovo
                  </button>
                </div>
                <Card.Body>
                  <div className="d-flex justify-content-between align-items-center mb-2">
                    <div className="cardlet-content">{group.items.length}</div>
                    <div className="text-muted">Rilevamenti</div>
                  </div>
                  {group.items
                    .slice()
                    .sort((a, b) => (b.detectionTime ?? 0) - (a.detectionTime ?? 0))
                    .map((item) => (
                      <div key={item.id} className="d-flex justify-content-between py-1">
                        <div>Rilevamento</div>
                        <div>{formatDate(item.detectionTime)}</div>  {/* dati della singola detection */}
                      </div>
                    ))}
                </Card.Body>
              </Card>
            </Col>
          ))}
        </Row>
      </Container>
    </Fragment>
  );
}
