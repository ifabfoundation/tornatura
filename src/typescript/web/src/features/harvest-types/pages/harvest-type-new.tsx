import React from "react";
import { useNavigate } from "react-router-dom";
import {
  HarvestTypeCreatePayload,
  HarvestTypeUpdatePayload,
} from "@tornatura/coreapis";
import { useAppDispatch } from "../../../hooks";
import { headerbarActions } from "../../headerbar/state/headerbar-slice";
import { HarvestTypeForm } from "../components/harvest-type-form";
import { harvestTypesActions } from "../state/harvest-types-slice";

export function HarvestTypeNew() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({ title: "Nuova coltura", subtitle: "Vista amministrazione" }));
  }, [dispatch]);

  const handleSubmit = async (payload: HarvestTypeCreatePayload | HarvestTypeUpdatePayload) => {
    await dispatch(harvestTypesActions.addHarvestTypeAction(payload as HarvestTypeCreatePayload)).unwrap();
    await dispatch(harvestTypesActions.fetchHarvestTypesAction({ includeInactive: true }));
    navigate("/admin/harvest-types");
  };

  return (
    <div className="catalog-page catalog-page--form">
      <HarvestTypeForm onSubmit={handleSubmit} />
    </div>
  );
}
