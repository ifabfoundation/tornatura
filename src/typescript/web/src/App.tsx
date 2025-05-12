import React from "react";

import "./App.css";
import { authStore } from "./providers/auth-providers";
import { useAppDispatch, useAppSelector } from "./hooks";
import { getUserInfo } from "./features/users/utils";
import { userActions, userSelectors } from "./features/users/state/user-slice";
import { Navigate, Outlet } from "react-router-dom";
import TopBar from "./components/Topbar";
import SideBar, { MenuItemEntry } from "./components/Sidebar";
import { companiesActions } from "./features/companies/state/companies-slice";
import logo from "./assets/images/logo.svg";
import { AccountTypeEnum } from "@tornatura/coreapis";
import { SidebarActions } from "./features/sidebar/state/sidebar-slice";
import { feedbacksActions } from "./features/feedbacks/state/feedbacks-slice";
import { fieldsActions } from "./features/fields/state/fields-slice";

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

function MainApp() {
  const dispatch = useAppDispatch();
  const currentUser = useAppSelector(userSelectors.selectCurrentUser);

  React.useEffect(() => {
    let menuEntries: MenuItemEntry[] = [];
    let menuBottomEntries: MenuItemEntry[] = [];
    if (currentUser.accountType === AccountTypeEnum.Admin) {
      menuEntries = [
        {
          id: "companies",
          icon: "ifab_grid",
          text: "Aziende",
          path: "/companies",
        },
        {
          id: "users",
          icon: "ifab_users",
          text: "Utenti",
          path: "/users",
        },
        {
          id: "feedbacks",
          icon: "ifab_baloon",
          text: "Feedbacks",
          path: "/feedbacks",
        },
      ];
      dispatch(userActions.fetchUsersAction());
      dispatch(companiesActions.fetchCompaniesAction());
      dispatch(feedbacksActions.fetchFeedbackAction());
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
          path: "/feedback",
        },
      ];

      if (currentUser.organizations) {
        for (let org of currentUser.organizations) {
          dispatch(companiesActions.getCompanyAction(org.id));
          dispatch(fieldsActions.fetchCompanyFieldsAction(org.id));
        }
      }
    }
    dispatch(SidebarActions.setMenuEntriesAction(menuEntries));
    dispatch(SidebarActions.setMenuBottomEntriesAction(menuBottomEntries));
  }, [currentUser]);

  return (
    <div id="app" className="main-app">
      <SideBar />
      <div className="ui-right">
        <TopBar showBackButton={true} />
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
  // const location = useLocation();
  const { initialized, authenticated } = React.useContext(authStore);
  const [loaded, setLoaded] = React.useState(false);
  const dispatch = useAppDispatch();

  const loadData = async () => {
    const profile = await getUserInfo();
    if (profile) {
      await dispatch(userActions.setCurrentUserAction(profile));
      console.log("User profile loaded", profile);
      setLoaded(true);
    }
  };

  React.useEffect(() => {
    if (initialized && authenticated) {
      loadData();
    }
  }, [authenticated, initialized]);

  console.log("App initialized", initialized, authenticated, loaded);

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
