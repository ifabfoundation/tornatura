import { useAppDispatch, useAppSelector } from "../../../hooks";
import React, { Fragment } from "react";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { Col, Container, Row } from "react-bootstrap";
import { detectionsSelectors } from "../../detections/state/detections-slice";
import _ from "lodash";
import { useParams } from "react-router-dom";

export function CompanyDetections() {
  const dispatch = useAppDispatch();
  const { companyId } = useParams();
  const detections = useAppSelector(state => detectionsSelectors.selectDetectionbyOrgId(state, companyId ?? "default"));

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Tutti i rilevamenti", subtitle: "Subtitle" }));
  }, []);

  return (
    <Fragment>
      <Container>
        <Row className="mt-4">
          <Col>
            
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
}
