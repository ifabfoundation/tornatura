import { useParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import React from "react";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { Col, Container, Row } from "react-bootstrap";
import { fieldsSelectors } from "../state/fields-slice";
import _ from "lodash"; 
import { FieldDetailForm } from "../forms/detail-form";


export function FieldSettings() {
  const dispatch = useAppDispatch();
  // const navigate = useNavigate();
  const { fieldId } = useParams();
  const currentField = useAppSelector((state) =>
    fieldsSelectors.selectFieldbyId(state, fieldId ?? "default")
  );

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Impostazioni", subtitle: "Subtitle" }));
  }, []);

  return (
    <Container>
      <Row className="mt-2">
        <Col xl={12} className="py-3">
          <FieldDetailForm field={currentField} />
        </Col>
      </Row>
    </Container>
  );
}
