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
        icon: "grid",
        text: "Dashboard campo",
        path: `/companies/${companyId}/fields/${fieldId}`,
      },
      {
        id: "detections",
        icon: "checklist",
        text: "Rilevamenti campo",
        path: `/companies/${companyId}/fields/${fieldId}/detections`,
      },
      {
        id: "mappa",
        icon: "pin",
        text: "Mappa",
        path: `/companies/${companyId}/fields/${fieldId}/map`,
      },
      {
        id: "impostazioni",
        icon: "cog",
        text: "Impostazioni campo",
        path: `/companies/${companyId}/fields/${fieldId}/settings`,
      },
    ];
    menuBottomEntries = [
      {
        id: "feedback",
        icon: "baloon",
        text: "Invia Feedback",
        path: `/companies/${companyId}/fields/${fieldId}/new-feedback`,
      },
      {
        id: "my-invitations",
        icon: "grid",
        text: "I miei inviti",
        path: `/companies/${companyId}/fields/${fieldId}/invitations/me`,
      },
      {
        id: "user",
        icon: "users",
        text: "Profilo Utente",
        path: `/companies/${companyId}/fields/${fieldId}/profile`,
      },
    ];
    dispatch(SidebarActions.setMenuEntriesAction(menuEntries));
    dispatch(SidebarActions.setMenuBottomEntriesAction(menuBottomEntries));
  }, [companyId, fieldId]);

  return <Outlet />;
}
