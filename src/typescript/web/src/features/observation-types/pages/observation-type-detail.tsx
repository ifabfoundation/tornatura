import React from "react";
import { Col, Container, Row } from "react-bootstrap";
import { useNavigate, useParams } from "react-router-dom";
import { ObservationTypeUpdatePayload } from "@tornatura/coreapis";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { harvestTypesSelectors } from "../../harvest-types/state/harvest-types-slice";
import { ObservationTypeForm } from "../components/observation-type-form";
import {
  observationTypesActions,
  observationTypesSelectors,
} from "../state/observation-types-slice";

export function ObservationTypeDetail() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { observationTypeId } = useParams();
  const harvestTypes = useAppSelector(harvestTypesSelectors.selectHarvestTypes);
  const observationType = useAppSelector((state) =>
    observationTypesSelectors.selectObservationTypeById(state, observationTypeId ?? ""),
  );

  React.useEffect(() => {
    dispatch(
      headerbarActions.setTitle({
        title: "Dettaglio tipo di rilevamento",
        subtitle: "Vista amministrazione",
      }),
    );
  }, [dispatch]);

  React.useEffect(() => {
    if (!observationType) {
      dispatch(observationTypesActions.fetchObservationTypesAction({ page: 1, limit: 1000 }));
    }
  }, [dispatch, observationType]);

  const handleSubmit = async (payload: ObservationTypeUpdatePayload) => {
    if (!observationTypeId) {
      return;
    }
    await dispatch(
      observationTypesActions.updateObservationTypeAction({
        observationTypeId,
        body: payload,
      }),
    );
    await dispatch(observationTypesActions.fetchObservationTypesAction({ page: 1, limit: 1000 }));
    navigate("/admin/observation-types");
  };

  if (!observationType) {
    return <div>Caricamento...</div>;
  }

  return (
    <section className="soft pb-3">
      <Container fluid className="px-0">
        <Row className="mb-4">
          <Col xl={12}>
            <ObservationTypeForm
              observationType={observationType}
              harvestTypes={harvestTypes}
              onSubmit={handleSubmit}
            />
          </Col>
        </Row>
      </Container>
    </section>
  );
}
