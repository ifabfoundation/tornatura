import React from "react";
import { useAppDispatch, useAppSelector } from "../../../hooks";
import { companiesSelectors } from "../state/companies-slice";
import { Outlet, useParams } from "react-router-dom";
import { MenuItemEntry } from "../../../components/Sidebar";
import { SidebarActions } from "../../sidebar/state/sidebar-slice";

export function CompanyDetail() {
  const dispatch = useAppDispatch();
  const { companyId } = useParams();
  const currentCompany = useAppSelector((state) =>
    companiesSelectors.selectCompanybyId(state, companyId ?? "default")
  );

  React.useEffect(() => {
    let menuEntries: MenuItemEntry[] = [];
    menuEntries = [
      {
        id: "fields",
        icon: "ifab_grid",
        text: "Campi dell'azienda",
        path: `/companies/${companyId}/fields`,
      },
      {
        id: "detections",
        icon: "ifab_checklist",
        text: "Lista dei rilevamenti",
        path: `/companies/${companyId}/detections`,
      },
    ];
    dispatch(SidebarActions.setMenuEntriesAction(menuEntries));
  }, [currentCompany]);

  return <Outlet />;
}
