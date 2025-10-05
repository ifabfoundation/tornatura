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

    let menuEntries: MenuItemEntry[] = [];
    let menuBottomEntries: MenuItemEntry[] = [];

    menuEntries = [
      {
        id: "fields",
        icon: "ifab_grid",
        text: "Dashboard campo",
        path: `/companies/${companyId}/fields/${fieldId}`,
      },
      {
        id: "detections",
        icon: "ifab_checklist",
        text: "Rilevamenti campo",
        path: `/companies/${companyId}/fields/${fieldId}/detections`,
      },
      {
        id: "mappa",
        icon: "ifab_pin",
        text: "Mappa",
        path: `/companies/${companyId}/fields/${fieldId}/map`,
      },
      {
        id: "impostazioni",
        icon: "ifab_cog",
        text: "Impostazioni",
        path: `/companies/${companyId}/fields/${fieldId}/settings`,
      },
    ];
    menuBottomEntries = [
      {
        id: "feedback",
        icon: "ifab_baloon",
        text: "Invia Feedback",
        path: `/companies/${companyId}/fields/${fieldId}/new-feedback`,
      },
      {
        id: "user",
        icon: "ifab_users",
        text: "Profilo Utente",
        path: `/companies/${companyId}/fields/${fieldId}/profile`,
      },
    ];
    dispatch(SidebarActions.setMenuEntriesAction(menuEntries));
    dispatch(SidebarActions.setMenuBottomEntriesAction(menuBottomEntries));
  }, [companyId, fieldId]);

  return <Outlet />;
}
