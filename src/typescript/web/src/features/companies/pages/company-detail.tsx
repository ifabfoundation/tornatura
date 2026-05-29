import React from "react";
import { useAppDispatch } from "../../../hooks";
import { Outlet, useParams } from "react-router-dom";
import { MenuItemEntry } from "../../../components/Sidebar";
import { SidebarActions } from "../../sidebar/state/sidebar-slice";
import { fieldsActions } from "../../fields/state/fields-slice";
import { companiesActions } from "../state/companies-slice";

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
          path: `/m/companies/${companyId}/fields`,
          type: 'single',
        familyItems: []
        },
        {
          id: "members",
          icon: "user",
          text: "Membri",
          path: `/m/companies/${companyId}/members`,
          type: 'single',
          familyItems: []
        },
        {
          id: "stats",
          icon: "dashboard",
          text: "Statistiche",
          path: `/m/companies/${companyId}/stats`,
          type: 'single',
          familyItems: []
        },
        {
          id: "invitations",
          icon: "baloon",
          text: "Gestione inviti azienda",
          path: `/m/companies/${companyId}/invitations`,
          type: 'single',
          familyItems: []
        },
      ];
      menuBottomEntries = [
        {
          id: "settings",
          icon: "cog",
          text: "Impostazioni Azienda",
          path: `/m/companies/${companyId}/settings`,
          type: 'single',
          familyItems: []
        },
        {
          id: "feedback",
          icon: "baloon",
          text: "Invia Feedback",
          path: `/m/companies/${companyId}/new-feedback`,
          type: 'single',
          familyItems: []
        }
      ];
      dispatch(SidebarActions.setMenuEntriesAction(menuEntries));
      dispatch(SidebarActions.setMenuBottomEntriesAction(menuBottomEntries));
      dispatch(companiesActions.getCompanyAction(companyId));
      dispatch(fieldsActions.fetchCompanyFieldsAction(companyId));
    }
  }, [companyId, fieldId]);

  return <Outlet />;
}
