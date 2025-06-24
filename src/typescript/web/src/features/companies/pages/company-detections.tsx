import { useAppDispatch, useAppSelector } from "../../../hooks";
import React, { Fragment } from "react";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { Col, Container, Row } from "react-bootstrap";
import { DetectionTableComponent } from "../../detections/components/detections-table";
import { detectionsSelectors } from "../../detections/state/detections-slice";
import _ from "lodash";

export function CompanyDetections() {
  const dispatch = useAppDispatch();
  const detections = useAppSelector(detectionsSelectors.selectDetections);

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Tutti i rilevamenti", subtitle: "Subtitle" }));
  }, []);

  return (
    <Fragment>
      <Container>
        <Row className="mt-4">
          <Col>
            <DetectionTableComponent detections={detections} />
          </Col>
        </Row>
      </Container>
    </Fragment>
  );
}
