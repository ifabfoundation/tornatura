import React from "react";
import { useAppDispatch } from "../../../hooks";
import { Outlet, useParams } from "react-router-dom";
import { MenuItemEntry } from "../../../components/Sidebar";
import { SidebarActions } from "../../sidebar/state/sidebar-slice";

export function CompanyDetail() {
  const dispatch = useAppDispatch();
  const { companyId, fieldId } = useParams();

  React.useEffect(() => {
    if (companyId && !fieldId) {
      let menuEntries : MenuItemEntry[] = [];
      let menuBottomEntries : MenuItemEntry[] = [];
      menuEntries = [
        {
          "id": "fields",
          "icon": "ifab_grid",
          "text": "Campi dell'azienda",
          "path":  `/companies/${companyId}/fields`,
        }, 
        {
          "id": "detections",
          "icon": "ifab_checklist",
          "text": "lista dei rilevamenti",
          "path":  `/companies/${companyId}/detections`,
        }, 
      ];  
      menuBottomEntries = [
        {
          "id": "feedback",
          "icon": "ifab_baloon",
          "text": "Invia Feedback",
          "path":  "/new-feedback",
        }, 
      ];
      dispatch(SidebarActions.setMenuEntriesAction(menuEntries));
      dispatch(SidebarActions.setMenuBottomEntriesAction(menuBottomEntries));
    }
  }, [companyId, fieldId]);
  
  return (
    <Outlet />
  );
}
