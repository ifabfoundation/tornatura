import { Navigate, RouteObject, useLocation, useRoutes } from "react-router-dom";
import App, { AdminApp, MainDash, RouteApp } from "./App";
import { CompanyTable } from "./features/companies/pages/companies-table";
import { UserTable } from "./features/users/pages/users-table";
import { FeedbackTable } from "./features/feedbacks/pages/feedbacks-table";
import { CompanyForm } from "./features/companies/pages/company-form";
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
import { CompanyMembers } from "./features/companies/pages/company-members";
import { CompanyStats } from "./features/companies/pages/company-stats";
import { FieldMap } from "./features/fields/pages/field-map";
import { DetectionForm } from "./features/detections/pages/detection-form";
import { FieldSettings } from "./features/fields/pages/field-settings";
import { CompanySettings } from "./features/companies/pages/company-settings";
import { UserProfile } from "./features/users/pages/user-profile";
import { InvitationsList } from "./features/invitations/pages/invitations-list";
import { SendInvitation } from "./features/invitations/pages/send-invitation";
import { InvitationAccept } from "./features/invitations/pages/invitation-accept";
import { MyInvitations } from "./features/invitations/pages/my-invitations";
import { DetectionTypeDetail } from "./features/detection-types/pages/detection-type-detail";
import { FieldModelPeronospora } from "./features/fields/pages/field-model-peronospora";
import { FieldModelBollettini } from "./features/fields/pages/field-model-bollettini";



function PrefixedRedirect({ from, to }: { from: string; to: string }) {
  const location = useLocation();
  const suffix = location.pathname.startsWith(from) ? location.pathname.slice(from.length) : "";
  return <Navigate to={`${to}${suffix}${location.search}${location.hash}`} replace />;
}

function RedirectPreservingLocation({ to }: { to: string }) {
  const location = useLocation();
  return <Navigate to={`${to}${location.search}${location.hash}`} replace />;
}


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
        path: "/admin",
        element: <AdminApp />,
        children: [
          {
            index: true,
            element: <Navigate to="companies" />
          },
          {
            path: "companies",
            element: <CompanyTable />
          },
          {
            path: "companies/:companyId/stats",
            element: <CompanyStats />
          },
          {
            path: "users",
            element: <UserTable />
          },
          {
            path: "feedbacks",
            element: <FeedbackTable />
          },
          {
            path: "profile",
            element: <UserProfile />
          },
        ]
      },
      {
        path: "/m",
        element: <MainDash />,
        children: [
          {
            index: true,
            element: <Navigate to="companies" />
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
          {
            path: "companies",
            element: <CompaniesList />
          },
          {
            path: "companies/new",
            element: <CompanyForm />
          }
        ]
      },
      {
        path: "/m/companies/:companyId",
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
            path: "members",
            element: <CompanyMembers />
          },
          {
            path: "stats",
            element: <CompanyStats />
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
          }
        ]
      },
      {
        path: "/m/companies/:companyId/fields/:fieldId",
        element: <FieldDetail />,
        children: [
          {
            index : true,
            element: <FieldDashboard />
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
          {
            path: "type/:typeId",
            element: <DetectionTypeDetail />
          },
          {
            path: "models/peronospora",
            element: <FieldModelPeronospora />
          },
          {
            path: "bulletins/:culture",
            element: <FieldModelBollettini />
          },
        ]
      }
    ]
  },
  {
    path: "/pub/welcome",
    element: <Welcome />,
  },
  {
    path: "/pub/signup",
    element: <Signup />
  },
  {
    path: "/pub/invitations/accept",
    element: <InvitationAccept />
  },
  {
    path: "/welcome",
    element: <RedirectPreservingLocation to="/pub/welcome" />,
  },
  {
    path: "/signup",
    element: <RedirectPreservingLocation to="/pub/signup" />,
  },
  {
    path: "/invitations/accept",
    element: <RedirectPreservingLocation to="/pub/invitations/accept" />,
  },
  {
    path: "/companies/*",
    element: <PrefixedRedirect from="/companies" to="/m/companies" />,
  },
  {
    path: "/new-feedback",
    element: <RedirectPreservingLocation to="/m/new-feedback" />,
  },
  {
    path: "/profile",
    element: <RedirectPreservingLocation to="/m/profile" />,
  },
  {
    path: "/invitations/me",
    element: <RedirectPreservingLocation to="/m/invitations/me" />,
  },

]


export function AppRoutes() {
  let routes = useRoutes(routesInitials);
  return routes;
}
