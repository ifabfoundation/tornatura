import { useNavigate, useParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import React, { Fragment } from "react";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { Col, Container, Row } from "react-bootstrap";
import { detectionsSelectors } from "../../detections/state/detections-slice";
import { GradientLineChart } from "../../../components/GradientLineChart";
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
          <Col>
            
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
}
