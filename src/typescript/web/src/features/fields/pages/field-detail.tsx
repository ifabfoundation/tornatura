import { Outlet, useParams } from "react-router-dom";
import { useAppDispatch } from "../../../hooks";
import React from "react";
import { MenuItemEntry } from "../../../components/Sidebar";
import { SidebarActions } from "../../sidebar/state/sidebar-slice";


export function FieldDetail() {
  const dispatch = useAppDispatch();
  const { companyId, fieldId } = useParams();

  React.useEffect(() => {
    if (!companyId || !fieldId) {
      return;
    }

    let menuEntries : MenuItemEntry[] = [];
    let menuBottomEntries : MenuItemEntry[] = [];

    menuEntries = [
      {
        "id": "fields",
        "icon": "chart",
        "text": "Dashboard campo",
        "path":  `/companies/${companyId}/fields/${fieldId}`,
      }, 
      {
        "id": "detections",
        "icon": "chart",
        "text": "Rilevamenti campo",
        "path":  `/companies/${companyId}/fields/${fieldId}/detections`,
      }, 
      {
        "id": "mappa",
        "icon": "chart",
        "text": "Mappa",
        "path":  `/companies/${companyId}/fields/${fieldId}/map`,
      }, 
    ];  
    menuBottomEntries = [
      {
        "id": "feedback",
        "icon": "chart",
        "text": "Invia Feedback",
        "path":  "/new-feedback",
      }, 
    ];
    dispatch(SidebarActions.setMenuEntriesAction(menuEntries));
    dispatch(SidebarActions.setMenuBottomEntriesAction(menuBottomEntries));
  }, [companyId, fieldId]);
  
  return (
    <Outlet />
  );
}
