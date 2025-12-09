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
      let menuEntries: MenuItemEntry[] = [];
      let menuBottomEntries: MenuItemEntry[] = [];
      menuEntries = [
        {
          id: "fields",
          icon: "grid",
          text: "Campi dell'azienda",
          path: `/companies/${companyId}/fields`,
        },
        {
          id: "detections",
          icon: "checklist",
          text: "Lista dei rilevamenti",
          path: `/companies/${companyId}/detections`,
        },
        {
          id: "invitations",
          icon: "ifab_checklist",
          text: "Inviti",
          path: `/companies/${companyId}/invitations`,
        },
        {
          id: "settings",
          icon: "cog",
          text: "Impostazioni azienda",
          path: `/companies/${companyId}/settings`,
        },
      ];
      menuBottomEntries = [
        {
          id: "feedback",
          icon: "baloon",
          text: "Invia Feedback",
          path: `/companies/${companyId}/new-feedback`,
        },
        {
          id: "my-invitations",
          icon: "ifab_grid",
          text: "I miei inviti",
          path: `/companies/${companyId}/invitations/me`,
        },
        {
          id: "user",
          icon: "users",
          text: "Profilo Utente",
          path: `/companies/${companyId}/profile`,
        },
      ];
      dispatch(SidebarActions.setMenuEntriesAction(menuEntries));
      dispatch(SidebarActions.setMenuBottomEntriesAction(menuBottomEntries));
    }
  }, [companyId, fieldId]);

  return <Outlet />;
}
