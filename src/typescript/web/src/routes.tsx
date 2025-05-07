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
import { Welcome } from "./pages/welcome";
import { Signup } from "./pages/auth";
import { CompanyForm } from "./features/companies/pages/company-form";
import { FeedbackForm } from "./features/feedbacks/pages/feedback-form";
import { CompanyDetail } from "./features/companies/pages/company-detail";
import { CompanyFields } from "./features/companies/pages/company-fields";


const routesInitials = [
  {
    path: "/",
    element: <App />,
  },
  {
    path: "/welcome",
    element: <Welcome />,
  },
  {
    path: "/signup",
    element: <Signup />,
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
  {
    path: "/welcome",
    element: <Welcome />,
  },
  {
    path: "/signup",
    element: <Signup />,
  }
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
        path: "/feedback",
        element: <FeedbackForm />
      },
      {
        path: "/companies",
        element: <CompaniesList />
      },
      {
        path: "/companies/new-company",
        element: <CompanyForm />
      },
      {
        path: "/companies/:companyId",
        element: <CompanyDetail />,
        children: [
          {
            index : true,
            element: <Navigate to="fields" />
          },
          {
            path: "/companies/:companyId/fields",
            element: <CompanyFields />
          }
        ]
      },
    ]
  },
  {
    path: "/welcome",
    element: <Welcome />,
  },
  {
    path: "/signup",
    element: <Signup />
  }
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
