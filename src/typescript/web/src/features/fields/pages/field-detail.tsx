import { Outlet, useParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import React from "react";
import { MenuItemEntry } from "../../../components/Sidebar";
import { SidebarActions } from "../../sidebar/state/sidebar-slice";
import { IconName } from "../../../components/Icon";
import {
  detectionTypesActions,
  detectionTypesSelectors,
} from "../../detection-types/state/detection-types-slice";
import {
  observationTypesActions,
  observationTypesSelectors,
} from "../../observation-types/state/observation-types-slice";
import { detectionsActions } from "../../detections/state/detections-slice";
import { companiesActions } from "../../companies/state/companies-slice";
import { fieldsActions, fieldsSelectors } from "../state/fields-slice";

function formatHarvestName(harvest?: string) {
  if (!harvest) {
    return "Bollettini";
  }

  return harvest
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function FieldDetail() {
  const dispatch = useAppDispatch();
  const { companyId, fieldId } = useParams();
  const currentField = useAppSelector((state) =>
    fieldsSelectors.selectFieldbyId(state, fieldId ?? "default"),
  );
  const detectionTypes = useAppSelector((state) =>
    detectionTypesSelectors.selectDetectionTypesByField(state, fieldId ?? "default"),
  );
  const observationsTypes = useAppSelector(observationTypesSelectors.selectObservationTypes);

  const fetchData = React.useCallback(() => {
    if (companyId && fieldId) {
      dispatch(companiesActions.getCompanyAction(companyId));
      dispatch(fieldsActions.fetchCompanyFieldsAction(companyId));
      dispatch(detectionTypesActions.fetchDetectionTypesAction({ orgId: companyId, fieldId }));
      dispatch(detectionsActions.fetchFieldDetectionsAction({ orgId: companyId, fieldId }));
    }
    dispatch(observationTypesActions.fetchObservationTypesAction({}));
  }, [companyId, fieldId, dispatch]);

  React.useEffect(() => {
    if (!companyId || !fieldId || !currentField) {
      return;
    }

    let detectionTypeFamilyItems = [];
    let menuEntries: MenuItemEntry[] = [];
    let menuBottomEntries: MenuItemEntry[] = [];

    for (let detectionType of detectionTypes) {
      for (let observationType of observationsTypes) {
        if (detectionType.observationTypeId === observationType.id) {
          detectionTypeFamilyItems.push({
            text: `${observationType.typology}  ›  ${observationType.method}`,
            path: `/m/companies/${companyId}/fields/${fieldId}/type/${detectionType.id}`,
          });
        }
      }
    }

    menuEntries = [
      {
        id: "fields",
        icon: "grid",
        text: "Dashboard campo",
        path: `/m/companies/${companyId}/fields/${fieldId}`,
        type: "single",
        familyItems: [],
      },
      {
        id: "field-landscape",
        icon: "sprout" as IconName,
        text: "Il tuo paesaggio",
        path: `/m/companies/${companyId}/fields/${fieldId}/landscape`,
        type: "single",
        familyItems: [],
      },
      {
        id: "new-detection",
        icon: "add",
        text: "Nuovo tipo rilevamento",
        path: `/m/companies/${companyId}/fields/${fieldId}/new-detection`,
        type: "single",
        familyItems: [],
      },
      {
        id: "field-detections",
        icon: "checklist" as IconName,
        text: "Rilevamenti",
        path: `/m/companies/${companyId}/fields/${fieldId}/type`,
        type: "family",
        familyItems: detectionTypeFamilyItems,
      },
      {
        id: "field-models",
        icon: "spark" as IconName,
        text: "Modelli previsionali",
        path: `/m/companies/${companyId}/fields/${fieldId}/models`,
        type: "family",
        familyItems: [
          {
            text: "Peronospora",
            path: `/m/companies/${companyId}/fields/${fieldId}/models/peronospora`,
          },
        ],
      },
      {
        id: "field-bulletins",
        icon: "bulletin" as IconName,
        text: "Bollettini fitosanitari",
        path: `/m/companies/${companyId}/fields/${fieldId}/bulletins`,
        type: "family",
        familyItems: [
          {
            text: formatHarvestName(currentField.harvest),
            path: `/m/companies/${companyId}/fields/${fieldId}/bulletins/${currentField.harvest}`,
          },
        ],
      },
    ];
    menuBottomEntries = [
      {
        id: "impostazioni",
        icon: "cog",
        text: "Impostazioni campo",
        path: `/m/companies/${companyId}/fields/${fieldId}/settings`,
        type: "single",
        familyItems: [],
      },
      {
        id: "feedback",
        icon: "baloon",
        text: "Invia Feedback",
        path: `/m/companies/${companyId}/fields/${fieldId}/new-feedback`,
        type: "single",
        familyItems: [],
      },
    ];
    dispatch(SidebarActions.setMenuEntriesAction(menuEntries));
    dispatch(SidebarActions.setMenuBottomEntriesAction(menuBottomEntries));
  }, [companyId, fieldId, observationsTypes, detectionTypes, currentField]);

  React.useEffect(() => {
    fetchData();
  }, [fetchData]);

  return <Outlet />;
}
