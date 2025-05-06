import React from 'react';

import './App.css';
import { authStore } from './providers/auth-providers';
import { useAppDispatch, useAppSelector } from './hooks';
import { getUserInfo } from './features/users/utils';
import { userActions, userSelectors } from './features/users/state/user-slice';
import { Outlet } from 'react-router-dom';
import TopBar from './components/Topbar';
import SideBar, { MenuItemEntry } from './components/Sidebar';
import { companiesActions } from './features/companies/state/companies-slice';
import logo from './assets/images/logo.svg';
import { AccountTypeEnum } from '@tornatura/coreapis';
import { SidebarActions } from './features/sidebar/state/sidebar-slice';
import { feedbacksActions } from './features/feedbacks/state/feedbacks-slice';


export function Loading() {
  return (
    <>
      <div className="loading-cont">
        <div>
          <img className="blink" src={logo} alt="loading"  width="50px"/>
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
    let menuEntries : MenuItemEntry[] = []
    if (currentUser.accountType === AccountTypeEnum.Admin) {
      menuEntries = [
        {
          "id": "companies",
          "icon": "chart",
          "text": "Aziende",
          "path":  "/companies",
        }, 
        {
        
          "id": "users",
          "icon": "pages",
          "text": "Utenti",
          "path": "/users" ,
        },
        {
          "id": "feedbacks",
          "icon": "diamond",
          "text": "Feedbacks",
          "path": "/feedbacks" ,
        },
        {
          "id": "aziende",
          "icon": "diamond",
          "text": "Aziende",
          "path": "/aziende" ,
        },
      ];
      dispatch(userActions.fetchUsersAction());
      dispatch(companiesActions.fetchCompanies());
      dispatch(feedbacksActions.fetchFeedbackAction());
    } else if (currentUser.accountType === AccountTypeEnum.Agronomist) {
      menuEntries = [
        {
          "id": "companies",
          "icon": "chart",
          "text": "Aziende",
          "path":  "/companies",
        }, 
        {
          "id": "users",
          "icon": "pages",
          "text": "Utenti",
          "path": "/users" ,
        },
        {
          "id": "feedbacks",
          "icon": "diamond",
          "text": "Feedbacks",
          "path": "/feedbacks" ,
        }
      ];
      dispatch(userActions.fetchUsersAction());
      dispatch(companiesActions.fetchCompanies());
      dispatch(feedbacksActions.fetchFeedbackAction());
    }
    dispatch(SidebarActions.setMenuEntriesAction(menuEntries));
  }, [currentUser]);

  
  return (
    <div id="app" className="main-app">
      <SideBar />
      <div className="ui-right">
        <TopBar />
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

  React.useEffect(() => {
    if (initialized && authenticated) {
      getUserInfo().then((profile) => {
        if (profile) {
          dispatch(userActions.setCurrentUserAction(profile)); 
          console.log("User profile loaded", profile);
          setLoaded(true);
        }
      });    
    }
    setLoaded(true);
  }, [authenticated, initialized]);

  return authenticated && initialized && loaded ? (
    <MainApp />
  ) : (
    <Loading />
  );
}

export default App;

