import { useRoutes } from "react-router-dom";
import App, { Demo, Demo2 } from "./App";
import React from "react";
import { CompaniesList } from "./features/companies/pages/companies-list";


const routesInitials = [
  {
    path: "/",
    element: <App />,
    children: [
      {
        index: true,
        element: <Demo />
      },
      {
        path: "/companies",
        element: <CompaniesList />
      },
    ]
  },
]

const routesAfter = [
  {
    path: "/",
    element: <App />,
    children: [
      {
        index: true,
        element: <Demo2 />
      },
      {
        path: "/companies",
        element: <CompaniesList />
      },
    ]
  },
]


export function AppRoutes() {
  const [routesList, setRoutesList] = React.useState(routesInitials);
  let routes = useRoutes(routesList);

  React.useEffect(() => {
    setTimeout(() => {
      setRoutesList(routesAfter);
    }, 10000);
  }, []);

  return routes;
}
