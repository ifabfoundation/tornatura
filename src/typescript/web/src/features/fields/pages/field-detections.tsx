import { useNavigate, useParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import React, { Fragment } from "react";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { Card, Col, Container, Row } from "react-bootstrap";
import { DetectionTableComponent } from "../../detections/components/detections-table";
import { detectionsSelectors } from "../../detections/state/detections-slice";
import _ from "lodash";



export function FieldDetections() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const {fieldId, companyId } = useParams();
  const detections = useAppSelector(state => detectionsSelectors.selectDetectionbyFieldId(state, fieldId ?? "default"));

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({title: "Tutti i rilevamenti", subtitle: "Subtitle"}));
  }, []); 
  
  return (
    <Fragment>
      <Container>
        <Row>
          <Col md={1} xl={9}>
            <Card>
              <Card.Header>RILEVAMENTI</Card.Header>
              <Card.Body style={{margin: "20px", fontSize: "40px"}}>
                <h1>{detections.length}</h1>
              </Card.Body>
            </Card>
          </Col>
          <Col md={1} xl={3}>
            <Card onClick={() => navigate(`/companies/${companyId}/fields/${fieldId}/new-detection`)}>
              <Card.Body style={{margin: "20px", fontSize: "40px"}}>
                <h1>+ Nuovo Rilevamento</h1>
              </Card.Body>
            </Card>
          </Col>
        </Row>
        <Row className="mt-4">
          <Col md={1} xl={12}>
            <DetectionTableComponent detections={detections}/>
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
}