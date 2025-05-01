import React from 'react';
import {Spinner} from 'react-bootstrap';

import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';
import { authStore } from './providers/auth-providers';
import { useAppDispatch } from './hooks';
import { getUserInfo } from './features/users/utils';
import { userActions } from './features/users/state/user-slice';
import { Outlet } from 'react-router-dom';
import TopBar from './components/top-bar';
import SideBar from './components/side-bar';
import { headerbarActions } from './features/headerbar/state/headerbar-slice';
import { companiesActions } from './features/companies/state/companies-slice';



export function Demo() {
  const dispatch = useAppDispatch();

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({title: "Dashboard", subtitle: "Subtitle"}));
  }, []); 

  return (
    <div>
      <h1>Dashboard</h1>
    </div>
  );
}

export function Demo2() {
  const dispatch = useAppDispatch();

  React.useEffect(() => {
    dispatch(headerbarActions.setTitle({title: "Dashboard 2", subtitle: "Subtitle"}));
  }, []); 

  return (
    <div>
      <h1>Dashboard 2</h1>
    </div>
  );
}

function MainApp() {

  return (
    <div className="dashboard">
      <header className="header">
        <TopBar />
      </header>
      <div className="main-content">
        <aside className="sidebar">
          <SideBar />
        </aside>
        <section className="content">
          <Outlet />
        </section>
      </div>
      <footer className="footer">
        <p>©2025 Tornatura</p>
      </footer>
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
          dispatch(companiesActions.fetchCompanies());
          console.log("User profile loaded", profile);
          setLoaded(true);
        }
      });     
    }
  }, [authenticated, initialized]);

  return authenticated && initialized && loaded ? (
    <MainApp />
  ) : (
    <Spinner animation="border" role="status">
      <span className="visually-hidden">Loading...</span>
    </Spinner>
  );
}

export default App;

