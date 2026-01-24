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
          icon: "sprout",
          text: "Campi",
          path: `/companies/${companyId}/fields`,
          type: 'single',
        familyItems: []
        },
        // {
        //   id: "detections",
        //   icon: "checklist",
        //   text: "Lista dei rilevamenti",
        //   path: `/companies/${companyId}/detections`,
        // },
        {
          id: "members",
          icon: "user",
          text: "Membri",
          path: `/companies/${companyId}/members`,
          type: 'single',
          familyItems: []
        },
        {
          id: "invitations",
          icon: "baloon",
          text: "Gestione inviti azienda",
          path: `/companies/${companyId}/invitations`,
          type: 'single',
          familyItems: []
        },
      ];
      menuBottomEntries = [
        {
          id: "settings",
          icon: "cog",
          text: "Impostazioni Azienda",
          path: `/companies/${companyId}/settings`,
          type: 'single',
          familyItems: []
        },
        {
          id: "feedback",
          icon: "baloon",
          text: "Invia Feedback",
          path: `/companies/${companyId}/new-feedback`,
          type: 'single',
          familyItems: []
        },
        // {
        //   id: "my-invitations",
        //   icon: "grid",
        //   text: "I miei inviti",
        //   path: `/companies/${companyId}/invitations/me`,
        // },
        // {
        //   id: "user",
        //   icon: "users",
        //   text: "Profilo Utente fcj",
        //   path: `/companies/${companyId}/profile`,
        // },
      ];
      dispatch(SidebarActions.setMenuEntriesAction(menuEntries));
      dispatch(SidebarActions.setMenuBottomEntriesAction(menuBottomEntries));
    }
  }, [companyId, fieldId]);

  return <Outlet />;
}
