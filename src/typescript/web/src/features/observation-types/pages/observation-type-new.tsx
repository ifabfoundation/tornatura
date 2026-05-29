import React from "react";
import { Col, Container, Row } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import {
  ObservationTypeCreatePayload,
  ObservationTypeUpdatePayload,
} from "@tornatura/coreapis";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { harvestTypesSelectors } from "../../harvest-types/state/harvest-types-slice";
import { ObservationTypeForm } from "../components/observation-type-form";
import { observationTypesActions } from "../state/observation-types-slice";

export function ObservationTypeNew() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const harvestTypes = useAppSelector(harvestTypesSelectors.selectHarvestTypes);

  React.useEffect(() => {
    dispatch(
      headerbarActions.setTitle({
        title: "Nuovo tipo di rilevamento",
        subtitle: "Vista amministrazione",
      }),
    );
  }, [dispatch]);

  const handleSubmit = async (
    payload: ObservationTypeCreatePayload | ObservationTypeUpdatePayload,
  ) => {
    await dispatch(
      observationTypesActions.addObservationTypeAction(payload as ObservationTypeCreatePayload),
    );
    await dispatch(observationTypesActions.fetchObservationTypesAction({ page: 1, limit: 1000 }));
    navigate("/admin/observation-types");
  };

  return (
    <section className="soft pb-3">
      <Container fluid className="px-0">
        <Row className="mb-4">
          <Col xl={12}>
            <ObservationTypeForm harvestTypes={harvestTypes} onSubmit={handleSubmit} />
          </Col>
        </Row>
      </Container>
    </section>
  );
}
