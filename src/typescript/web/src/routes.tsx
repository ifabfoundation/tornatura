import { Navigate, RouteObject, useRoutes } from "react-router-dom";
import App, { RouteApp } from "./App";
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
import { CompanyFieldForm } from "./features/companies/pages/company-field-form";
import { FieldDetail } from "./features/fields/pages/field-detail";
import { FieldDashboard } from "./features/fields/pages/field-dashboard";
import { CompanyDetections } from "./features/companies/pages/company-detections";
import { FieldDetections } from "./features/fields/pages/field-detections";
import { FieldMap } from "./features/fields/pages/field-map";
import { DetectionForm } from "./features/detections/pages/detection-form";



const routesInitials: RouteObject[] = [
  {
    path: "/",
    element: <App />,
    children: [
      {
        index: true,
        element: <RouteApp />
      },
      {
        path: "/admin/companies",
        element: <CompanyTable />
      },
      {
        path: "/admin/users",
        element: <UserTable />
      },
      {
        path: "/admin/feedbacks",
        element: <FeedbackTable />
      },
      {
        path: "/new-feedback",
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
          },
          {
            path: "/companies/:companyId/detections",
            element: <CompanyDetections />
          },
          {
            path: "/companies/:companyId/fields/new-field",
            element: <CompanyFieldForm />
          },
          {
            path: "/companies/:companyId/fields/:fieldId",
            element: <FieldDetail />,
            children: [
              {
                index : true,
                element: <FieldDashboard />
              },
              {
                path: "detections",
                element: <FieldDetections />
              },
              {
                path: "map",
                element: <FieldMap />
              },
              {
                path: "new-detection",
                element: <DetectionForm />
              },
            ]
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
  let routes = useRoutes(routesInitials);
  return routes;
}
