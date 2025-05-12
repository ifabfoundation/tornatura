import { useNavigate, useParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import React, { Fragment } from "react";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { Card, Col, Container, Row } from "react-bootstrap";
import { fieldsSelectors } from "../state/fields-slice";
import { DetectionTableComponent } from "../../detections/components/detections-table";
import { detectionsSelectors } from "../../detections/state/detections-slice";

export function FieldDashboard() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { fieldId } = useParams();
  const currentField = useAppSelector((state) =>
    fieldsSelectors.selectFieldbyId(state, fieldId ?? "default")
  );
  const detections = useAppSelector((state) =>
    detectionsSelectors.selectDetectionbyFieldId(state, fieldId ?? "default")
  );

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Dashboard", subtitle: "Subtitle" }));
  }, []);

  return (
    <Fragment>
      <Container>
        <Row>
          <Col md={6} xl={3}>
            <div className="cardlet">
              <header>Tipologia</header>
              <div className="cardlet-content">{currentField?.harvest ?? ""}</div>
            </div>
          </Col>
          <Col md={6} xl={3}>
            <div className="cardlet">
              <header>Dimensione del campo</header>
              <div className="cardlet-content">{currentField?.area ?? ""} he</div>
            </div>
          </Col>
          <Col md={6} xl={3}>
            <div className="cardlet">
              <header>Rilevamenti</header>
              <div className="cardlet-content">0</div>
            </div>
          </Col>
          <Col md={6} xl={3}>
            <a className="cardlet-button" onClick={() => navigate("/companies/new-company")}>
              + Nuovo Rilevamento
            </a>
          </Col>
        </Row>
      </Container>
      <DetectionTableComponent detections={detections} />
    </Fragment>
  );
}
