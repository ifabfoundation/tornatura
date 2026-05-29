import React, { useEffect, useRef } from "react";

import "./App.css";
import { authStore } from "./providers/auth-providers";
import { useAppDispatch, useAppSelector, usePageTracking } from "./hooks";
import { getUserInfo } from "./features/users/utils";
import { userActions, userSelectors } from "./features/users/state/user-slice";
import { userMenuSelectors } from "./features/userMenu/state/userMenu-slice";
import { Navigate, Outlet, useNavigate } from "react-router-dom";
import TopBar from "./components/Topbar";
import UserMenu from "./components/UserMenu";
import SideBar, { MenuItemEntry } from "./components/Sidebar";
import MobileHeaderBar from "./components/MobileHeaderBar";
import { companiesActions } from "./features/companies/state/companies-slice";
import { AccountTypeEnum } from "@tornatura/coreapis";
import { feedbacksActions } from "./features/feedbacks/state/feedbacks-slice";
import { SidebarActions } from "./features/sidebar/state/sidebar-slice";
import Loading from "./components/Loading";
import { invitationsActions } from "./features/invitations/state/invitations-slice";
import { harvestTypesActions } from "./features/harvest-types/state/harvest-types-slice";
import { observationTypesActions } from "./features/observation-types/state/observation-types-slice";
import ReactGA from "react-ga4";
import { getBrowsingOrigin } from "./helpers/common";

export function RouteApp() {
  const currentUser = useAppSelector(userSelectors.selectCurrentUser);
  if (currentUser.accountType === AccountTypeEnum.Admin) {
    return <Navigate to="/admin/companies" />;
  } else {
    return <Navigate to="/m/companies" />;
  }
}

export function AdminApp() {
  const dispatch = useAppDispatch();

  React.useEffect(() => {
    let menuEntries: MenuItemEntry[] = [];
    let menuBottomEntries: MenuItemEntry[] = [];

    menuEntries = [
      {
        id: "companies",
        icon: "barn",
        text: "Aziende",
        path: "/admin/companies",
        type: 'single',
        familyItems: []
      },
      {
        id: "users",
        icon: "users",
        text: "Utenti",
        path: "/admin/users",
        type: 'single',
        familyItems: []
      },
      {
        id: "feedbacks",
        icon: "baloon",
        text: "Feedbacks",
        path: "/admin/feedbacks",
        type: 'single',
        familyItems: []
      },
    ];

    menuBottomEntries = [
      {
        id: "user",
        icon: "users",
        text: "Profilo Utente",
        path: "/admin/profile",
        type: 'single',
        familyItems: []
      },
    ];

    dispatch(SidebarActions.setMenuEntriesAction(menuEntries));
    dispatch(SidebarActions.setMenuBottomEntriesAction(menuBottomEntries));

  }, []);

  return <Outlet />;
}

export function MainDash() {
  const dispatch = useAppDispatch();

  React.useEffect(() => {
    let menuEntries: MenuItemEntry[] = [];
    let menuBottomEntries: MenuItemEntry[] = [];

    menuEntries = [
      {
        id: "companies",
        icon: "barn",
        text: "Aziende gestite",
        path: "/m/companies",
        type: "single",
        familyItems: [],
      },
    ];

    menuBottomEntries = [
      {
        id: "feedback",
        icon: "baloon",
        text: "Invia Feedback",
        path: "/m/new-feedback",
        type: "single",
        familyItems: [],
      }
    ];

    dispatch(SidebarActions.setMenuEntriesAction(menuEntries));
    dispatch(SidebarActions.setMenuBottomEntriesAction(menuBottomEntries));

  }, []);

  return <Outlet />;
}

function RootApp() {
  const userMenuOpen = useAppSelector(userMenuSelectors.selectIsOpen);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    contentRef.current?.scrollTo({ top: 0, left: 0, behavior: "smooth" });
  }, [location.pathname]);

  return (
    <div id="app" className="main-app">
      <SideBar />
      <MobileHeaderBar />
      <UserMenu open={userMenuOpen} />
      <div className="ui-right">
        <TopBar /* showBackButton */ />
        <div className="content-area" ref={contentRef}>
          <div className="content">
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
}

function App() {
  usePageTracking();
  const navigate = useNavigate();
  const { initialized, authenticated } = React.useContext(authStore);
  const [loaded, setLoaded] = React.useState(false);
  const dispatch = useAppDispatch();

  const loadData = async () => {
      const profile = await getUserInfo();
    if (profile) {
      await dispatch(userActions.setCurrentUserAction(profile));
      await dispatch(harvestTypesActions.fetchHarvestTypesAction({ includeInactive: true }));
      await dispatch(observationTypesActions.fetchObservationTypesAction({page: 1, limit: 1000}));
      const session = sessionStorage.getItem("pending_invitation_token");
      let invitationToken = undefined;
      if (session) {
        const invitation = JSON.parse(session);
        if (invitation.has_pending_invitation) {
          invitationToken = invitation.pending_invitation_token;
        }
        sessionStorage.removeItem("pending_invitation_token");
      }

      if (invitationToken) {
        // const redirectUri = `${window.location.origin}/invitations/accept?token=${invitationToken}`;
        navigate(`/pub/invitations/accept?token=${invitationToken}`);
      }

      if (profile.accountType === AccountTypeEnum.Admin) {
        await dispatch(userActions.fetchUsersAction());
        await dispatch(companiesActions.fetchCompaniesAction());
        await dispatch(feedbacksActions.fetchFeedbackAction());
      } else if (
        profile.accountType === AccountTypeEnum.Agronomist ||
        profile.accountType === AccountTypeEnum.Standard
      ) {
        await dispatch(invitationsActions.fetchMyInvitationsAction());
        await dispatch(harvestTypesActions.fetchHarvestTypesAction({ includeInactive: true }));
        await dispatch(observationTypesActions.fetchObservationTypesAction({}))
        if (profile.organizations) {
          for (let org of profile.organizations) {
            await dispatch(companiesActions.getCompanyAction(org.id));
          }
        }
      }
      setLoaded(true);
    }
  };

  React.useEffect(() => {
    if (initialized && authenticated) {
      loadData();
      ReactGA.event("login");
      if (getBrowsingOrigin() === "PWA") {
        ReactGA.event("login_from_mobile");
      }
    }
  }, [authenticated, initialized]);

  if (!initialized) {
    return <Loading />;
  } else if (!authenticated) {
    return <Navigate to="/pub/welcome" />;
  } else if (!loaded) {
    return <Loading />;
  } else {
    return <RootApp />;
  }
}

export default App;
