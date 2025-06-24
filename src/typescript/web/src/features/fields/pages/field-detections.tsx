import { useNavigate, useParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import React, { Fragment } from "react";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { Col, Container, Row } from "react-bootstrap";
import { DetectionTableComponent } from "../../detections/components/detections-table";
import { detectionsSelectors } from "../../detections/state/detections-slice";
import _ from "lodash";

export function FieldDetections() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { fieldId, companyId } = useParams();
  const detections = useAppSelector((state) =>
    detectionsSelectors.selectDetectionbyFieldId(state, fieldId ?? "default")
  );

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Tutti i rilevamenti", subtitle: "Subtitle" }));
  }, []);

  return (
    <Fragment>
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
          <Col>
            <DetectionTableComponent detections={detections} />
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
}
