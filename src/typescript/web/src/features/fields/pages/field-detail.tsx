import { Outlet, useParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import React from "react";
import { MenuItemEntry } from "../../../components/Sidebar";
import { SidebarActions } from "../../sidebar/state/sidebar-slice";
import { IconName } from "../../../components/Icon";
import { detectionTypesActions, detectionTypesSelectors } from "../../detection-types/state/detection-types-slice";
import { observationTypesSelectors } from "../../observation-types/state/observation-types-slice";
import { detectionsActions } from "../../detections/state/detections-slice";

export function FieldDetail() {
  const dispatch = useAppDispatch();
  const { companyId, fieldId } = useParams();
  const detectionTypes = useAppSelector(state => detectionTypesSelectors.selectDetectionTypesByField(state, fieldId ?? "default"));
  const observationsTypes = useAppSelector(observationTypesSelectors.selectObservationTypes);

  React.useEffect(() => {
    if (!companyId || !fieldId) {
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
            path: `/companies/${companyId}/fields/${fieldId}/type/${detectionType.id}`,
          });
        }
      }
    }

    menuEntries = [
      {
        id: "fields",
        icon: "grid",
        text: "Dashboard campo",
        path: `/companies/${companyId}/fields/${fieldId}`,
        type: 'single',
        familyItems: []
      },
      {
        id: "new-detection",
        icon: "pencil",
        text: "Nuovo tipo rilevamento",
        path: `/companies/${companyId}/fields/${fieldId}/new-detection`,
        type: 'single',
        familyItems: []
      },
      {
        id: "field-detections",
        icon: "checklist" as IconName,
        text: "Rilevamenti",
        path: `/companies/${companyId}/fields/${fieldId}/type`,
        type: 'family',
        familyItems: detectionTypeFamilyItems
      },
      {
        id: "field-models",
        icon: "spark" as IconName,
        text: "Modelli previsionali",
        path: `/companies/${companyId}/fields/${fieldId}/models`,
        type: 'family',
        familyItems: [
          {
            text: "Peronospora",
            path: `/companies/${companyId}/fields/${fieldId}/models/peronospora`,
          },
          {
            text: "Cimice asiatica",
            path: `/companies/${companyId}/fields/${fieldId}/models/cimice-asiatica`,
          },
          {
            text: "Flavescenza dorata",
            path: `/companies/${companyId}/fields/${fieldId}/models/flavescenza-dorata`
          }
        ]
      },
    ];
    menuBottomEntries = [
      {
        id: "impostazioni",
        icon: "cog",
        text: "Impostazioni campo",
        path: `/companies/${companyId}/fields/${fieldId}/settings`,
        type: 'single',
        familyItems: []
      },
      {
        id: "feedback",
        icon: "baloon",
        text: "Invia Feedback",
        path: `/companies/${companyId}/fields/${fieldId}/new-feedback`,
        type: 'single',
        familyItems: []
      }
    ];
    dispatch(SidebarActions.setMenuEntriesAction(menuEntries));
    dispatch(SidebarActions.setMenuBottomEntriesAction(menuBottomEntries));

    
  }, [companyId, fieldId, observationsTypes, detectionTypes]);


  React.useEffect(() => {
    if (companyId && fieldId) {
      dispatch(detectionTypesActions.fetchDetectionTypesAction({ orgId: companyId, fieldId }));
      dispatch(detectionsActions.fetchFieldDetectionsAction({orgId: companyId, fieldId: fieldId}));
    }
  }, [companyId, fieldId]);

  return <Outlet />;
}
