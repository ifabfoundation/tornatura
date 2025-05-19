import React from "react";

import "./App.css";
import { authStore } from "./providers/auth-providers";
import { useAppDispatch, useAppSelector } from "./hooks";
import { getUserInfo } from "./features/users/utils";
import { userActions, userSelectors } from "./features/users/state/user-slice";
import { Navigate, Outlet, useParams } from "react-router-dom";
import TopBar from "./components/Topbar";
import SideBar, { MenuItemEntry } from "./components/Sidebar";
import MobileHeaderBar from "./components/MobileHeaderBar";
import { companiesActions } from "./features/companies/state/companies-slice";
import logo from "./assets/images/logo.png";
import { AccountTypeEnum, AgriField } from "@tornatura/coreapis";
import { SidebarActions } from "./features/sidebar/state/sidebar-slice";
import { feedbacksActions } from "./features/feedbacks/state/feedbacks-slice";
import { fieldsActions } from "./features/fields/state/fields-slice";
import { unwrapResult } from "@reduxjs/toolkit";
import { detectionsActions } from "./features/detections/state/detections-slice";

export function Loading() {
  return (
    <>
      <div className="loading-cont">
        <div>
          <img className="blink" src={logo} alt="loading" width="50px" />
          <p className="color-white mt-2"></p>
        </div>
      </div>
    </>
  );
}

export function RouteApp() {
  const currentUser = useAppSelector(userSelectors.selectCurrentUser);
  if (currentUser.accountType === AccountTypeEnum.Admin) {
    return <Navigate to="/admin/companies" />;
  } else if (currentUser.accountType === AccountTypeEnum.Agronomist) {
    return <Navigate to="/companies" />;
  } else {
    // @ts-ignore
    const url = `/companies/${currentUser.organizations[0].id}`;
    return <Navigate to={url} />;
  }
}

function MainApp() {
  const dispatch = useAppDispatch();
  const { companyId, fieldId } = useParams();
  const currentUser = useAppSelector(userSelectors.selectCurrentUser);

  React.useEffect(() => {
    if (!companyId && !fieldId) {
      let menuEntries: MenuItemEntry[] = [];
      let menuBottomEntries: MenuItemEntry[] = [];
      if (currentUser.accountType === AccountTypeEnum.Admin) {
        menuEntries = [
          {
            id: "companies",
            icon: "ifab_grid",
            text: "Aziende",
            path: "/admin/companies",
          },
          {
            id: "users",
            icon: "ifab_users",
            text: "Utenti",
            path: "/admin/users",
          },
          {
            id: "feedbacks",
            icon: "ifab_baloon",
            text: "Feedbacks",
            path: "/admin/feedbacks",
          },
        ];
      } else if (currentUser.accountType === AccountTypeEnum.Agronomist) {
        menuEntries = [
          {
            id: "companies",
            icon: "ifab_grid",
            text: "Aziende gestite",
            path: "/companies",
          },
        ];

        menuBottomEntries = [
          {
            id: "feedback",
            icon: "ifab_baloon",
            text: "Invia Feedback",
            path: "/new-feedback",
          },
        ];
      }
      dispatch(SidebarActions.setMenuEntriesAction(menuEntries));
      dispatch(SidebarActions.setMenuBottomEntriesAction(menuBottomEntries));
    }
  }, [currentUser, companyId, fieldId]);

  return (
    <div id="app" className="main-app">
      <SideBar />
      <MobileHeaderBar />
      <div className="ui-right">
        <TopBar /* showBackButton */ />
        <div className="content-area">
          <div className="content">
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
}

function App() {
  const { initialized, authenticated } = React.useContext(authStore);
  const [loaded, setLoaded] = React.useState(false);
  const dispatch = useAppDispatch();

  const loadData = async () => {
    const profile = await getUserInfo();
    if (profile) {
      await dispatch(userActions.setCurrentUserAction(profile));
      if (profile.accountType === AccountTypeEnum.Admin) {
        await dispatch(userActions.fetchUsersAction());
        await dispatch(companiesActions.fetchCompaniesAction());
        await dispatch(feedbacksActions.fetchFeedbackAction());
      } else if (
        profile.accountType === AccountTypeEnum.Agronomist ||
        profile.accountType === AccountTypeEnum.Standard
      ) {
        if (profile.organizations) {
          for (let org of profile.organizations) {
            await dispatch(companiesActions.getCompanyAction(org.id));
            const response = await dispatch(fieldsActions.fetchCompanyFieldsAction(org.id));
            const responseData = await unwrapResult(response);
            const fields = responseData.data as AgriField[];
            for (let field of fields) {
              await dispatch(
                detectionsActions.fetchFieldDetectionsAction({
                  orgId: org.id,
                  fieldId: field.id,
                })
              );
            }
          }
        }
      }
      setLoaded(true);
    }
  };

  React.useEffect(() => {
    if (initialized && authenticated) {
      loadData();
    }
  }, [authenticated, initialized]);

  if (!initialized) {
    return <Loading />;
  } else if (!authenticated) {
    return <Navigate to="/welcome" />;
  } else if (!loaded) {
    return <Loading />;
  } else {
    return <MainApp />;
  }
}

export default App;
