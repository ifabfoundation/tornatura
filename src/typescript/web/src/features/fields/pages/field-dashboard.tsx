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
  const {fieldId } = useParams();
  const currentField = useAppSelector(state => fieldsSelectors.selectFieldbyId(state, fieldId ?? "default"));
  const detections = useAppSelector(state => detectionsSelectors.selectDetectionbyFieldId(state, fieldId ?? "default"));


  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({title: "Dashboard", subtitle: "Subtitle"}));
  }, []); 
  
  return (
    <Fragment>
      <Container>
        <Row>
          <Col md={1} xl={3}>
            <Card>
              <Card.Header>TIPOLOGIA</Card.Header>
              <Card.Body style={{margin: "20px", fontSize: "40px"}}>
                <h1>{currentField?.name ?? ""}</h1>
              </Card.Body>
            </Card>
          </Col>
          <Col md={1} xl={3}>
            <Card>
              <Card.Header>DIMENSIONE DEL CAMPO</Card.Header>
              <Card.Body style={{margin: "20px", fontSize: "40px"}}>
                <h1>{currentField?.area ?? ""} he</h1>
              </Card.Body>
            </Card>
          </Col>
          <Col md={1} xl={3}>
            <Card>
              <Card.Header>RILEVAMENTI</Card.Header>
              <Card.Body style={{margin: "20px", fontSize: "40px"}}>
                <h1>0</h1>
              </Card.Body>
            </Card>
          </Col>
          <Col md={1} xl={3}>
            <Card onClick={() => navigate("/companies/new-company")}>
              <Card.Body style={{margin: "20px", fontSize: "40px"}}>
                <h1>+ Nuovo Rilevamento</h1>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
      <DetectionTableComponent detections={detections}/>
    </Fragment>
  );
}