import React from "react";
import { Col, Container, Row } from "react-bootstrap";
import { useNavigate, useParams } from "react-router-dom";
import { HarvestTypeUpdatePayload } from "@tornatura/coreapis";
import { HarvestTypeForm } from "../components/harvest-type-form";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { harvestTypesActions, harvestTypesSelectors } from "../state/harvest-types-slice";

export function HarvestTypeDetail() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { harvestTypeId } = useParams();
  const harvestType = useAppSelector((state) =>
    harvestTypesSelectors.selectHarvestTypeById(state, harvestTypeId ?? ""),
  );

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Dettaglio coltura", subtitle: "Vista amministrazione" }));
  }, [dispatch]);

  React.useEffect(() => {
    if (harvestTypeId) {
      dispatch(harvestTypesActions.fetchHarvestTypeAction(harvestTypeId));
    }
  }, [dispatch, harvestTypeId]);

  const handleSubmit = async (payload: HarvestTypeUpdatePayload) => {
    if (!harvestTypeId) {
      return;
    }
    await dispatch(
      harvestTypesActions.updateHarvestTypeAction({
        harvestTypeId,
        body: payload,
      }),
    );
    await dispatch(harvestTypesActions.fetchHarvestTypesAction({ includeInactive: true }));
    navigate("/admin/harvest-types");
  };

  if (!harvestType) {
    return <div>Caricamento...</div>;
  }

  return (
    <section className="soft pb-3">
      <Container fluid className="px-0">
        <Row className="mb-4">
          <Col xl={12}>
            <HarvestTypeForm harvestType={harvestType} onSubmit={handleSubmit} />
          </Col>
        </Row>
      </Container>
    </section>
  );
}
