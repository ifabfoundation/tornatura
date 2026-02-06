import { useAppDispatch } from "../../../hooks";
import React, { Fragment } from "react";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { Col, Container, Row } from "react-bootstrap";
import _ from "lodash";
;

export function CompanyDetections() {
  const dispatch = useAppDispatch();


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
