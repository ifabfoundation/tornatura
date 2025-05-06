import { Navigate, useRoutes } from "react-router-dom";
import App from "./App";
import React from "react";
import { useAppSelector } from "./hooks";
import { userSelectors } from "./features/users/state/user-slice";
import { AccountTypeEnum } from "@tornatura/coreapis";
import { CompanyTable } from "./features/companies/pages/companies-table";
import { UserTable } from "./features/users/pages/users-table";
import { FeedbackTable } from "./features/feedbacks/pages/feedbacks-table";
import { CompaniesList } from "./features/companies/pages/companies-list";
import { Welcome } from "./pages/auth";


const routesInitials = [
  {
    path: "/",
    element: <App />,
  }
]

const routesAdmin = [
  {
    path: "/",
    element: <App />,
    children: [
      {
        index: true,
        element: <Navigate to="/companies" />
      },
      {
        path: "/companies",
        element: <CompanyTable />
      },
      {
        path: "/users",
        element: <UserTable />
      },
      {
        path: "/feedbacks",
        element: <FeedbackTable />
      },
    ]
  },
]

const routesAgronomist = [
  {
    path: "/",
    element: <App />,
    children: [
      {
        index: true,
        element: <Navigate to="/companies" />
      },
      {
        path: "/companies",
        element: <CompaniesList />
      },
      {
        path: "/fields",
        element: <UserTable />
      },
    ]
  },
]


export function AppRoutes() {
  const currentUser = useAppSelector(userSelectors.selectCurrentUser);
  const [routesList, setRoutesList] = React.useState(routesInitials);
  let routes = useRoutes(routesList);

  React.useEffect(() => {
    if (currentUser.accountType === AccountTypeEnum.Admin) {
      setRoutesList(routesAdmin);
    } else if (currentUser.accountType === AccountTypeEnum.Agronomist) {
      setRoutesList(routesAgronomist);
    } else {
      setRoutesList(routesInitials);
    }
  }, [currentUser]);

  return routes;
}
