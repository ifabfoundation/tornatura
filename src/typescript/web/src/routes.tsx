import { Navigate, RouteObject, useRoutes } from "react-router-dom";
import App, { RouteApp } from "./App";
import { CompanyTable } from "./features/companies/pages/companies-table";
import { UserTable } from "./features/users/pages/users-table";
import { FeedbackTable } from "./features/feedbacks/pages/feedbacks-table";
import { CompaniesList } from "./features/companies/pages/companies-list";
import { Welcome } from "./pages/welcome";
import { Signup } from "./pages/auth";
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
import { FieldSettings } from "./features/fields/pages/field-settings";
import { CompanySettings } from "./features/companies/pages/company-settings";
import { UserProfile } from "./features/users/pages/user-profile";
import { InvitationsList } from "./features/invitations/pages/invitations-list";
import { SendInvitation } from "./features/invitations/pages/send-invitation";
import { InvitationAccept } from "./features/invitations/pages/invitation-accept";
import { MyInvitations } from "./features/invitations/pages/my-invitations";
import { InviteCompanyOwner } from "./features/invitations/pages/invite-company-owner";



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
        path: "/profile",
        element: <UserProfile />
      },
      {
        path: "/invitations/me",
        element: <MyInvitations />
      },
      {
        path: "/invitations/invite-company-owner",
        element: <InviteCompanyOwner />
      },
      {
        path: "/companies",
        element: <CompaniesList />
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
            path: "fields",
            element: <CompanyFields />
          },
          {
            path: "detections",
            element: <CompanyDetections />
          },
          {
            path: "settings",
            element: <CompanySettings />
          },
          {
            path: "invitations",
            element: <InvitationsList />
          },
          {
            path: "send-invitation",
            element: <SendInvitation />
          },
          {
            path: "new-field",
            element: <CompanyFieldForm />
          },
          {
            path: "new-feedback",
            element: <FeedbackForm />
          },
          {
            path: "invitations/me",
            element: <MyInvitations />
          },
          {
            path: "profile",
            element: <UserProfile />
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
              {
                path: "settings",
                element: <FieldSettings />
              },
              {
                path: "new-feedback",
                element: <FeedbackForm />
              },
              {
                path: "profile",
                element: <UserProfile />
              },
              {
                path: "invitations/me",
                element: <MyInvitations />
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
  },
  {
    path: "/invitations/accept",
    element: <InvitationAccept />
  },
]


export function AppRoutes() {
  let routes = useRoutes(routesInitials);
  return routes;
}
