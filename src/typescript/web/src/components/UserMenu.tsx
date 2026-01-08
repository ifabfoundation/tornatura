import React, { Fragment } from "react";
import { userMenuActions } from "../features/userMenu/state/userMenu-slice";
import { useAppDispatch, useAppSelector } from "../hooks";
import keycloakInstance from "../providers/keycloak";
import { userSelectors } from "../features/users/state/user-slice";
import { fallbacks } from "../assets/images/fallback";
import { useNavigate, useParams } from "react-router-dom";
import {
  invitationsActions,
  invitationsSelectors,
} from "../features/invitations/state/invitations-slice";

interface UserMenuProps {
  open: boolean;
}

export default function UserMenu({ open }: UserMenuProps) {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { fieldId, companyId } = useParams();
  const currentUser = useAppSelector(userSelectors.selectCurrentUser);
  const invitations = useAppSelector(invitationsSelectors.selectMyInvitations);

  const notificationsNum = invitations.length;

  React.useEffect(() => {
    dispatch(invitationsActions.fetchMyInvitationsAction());
  }, []);

  const handleSignOut = () => {
    keycloakInstance.logout();
  };

  const handleProfile = () => {
    dispatch(userMenuActions.toggle());
    if (fieldId && companyId) {
      navigate(`/companies/${companyId}/fields/${fieldId}/profile`);
    } else if (companyId) {
      navigate(`/companies/${companyId}/profile`);
    } else {
      navigate("/profile");
    }
  };

  const handleInvitiRicevuti = () => {
    dispatch(userMenuActions.toggle());
    if (fieldId && companyId) {
      navigate(`/companies/${companyId}/fields/${fieldId}/invitations/me`);
    } else if (companyId) {
      navigate(`/companies/${companyId}/invitations/me`);
    } else {
      navigate("/invitations/me");
    }
  };

  const accountTypeString = (accountType: string | undefined) => {
    switch (accountType?.toLowerCase()) {
      case "agronomist":
        return "Agronomo";
      case "standard":
        return "Profilo aziendale";
      default:
        return "Utente generico?";
    }
  };

  return (
    <Fragment>
      {open && (
        <div className="user-menu-bg" onClick={() => dispatch(userMenuActions.toggle())}></div>
      )}
      {open && (
        <div className="user-menu">
          <div className="d-flex flex-column justify-content-start align-items-center pt-2 mt-4 mb-4">
            <div
              className="large-user-avatar"
              style={{ backgroundImage: `url(${currentUser?.avatar || fallbacks.avatar})` }}
              // style={{ backgroundImage: `url(${fallbacks.avatar})` }}
            ></div>
            <div className="user-info">
              <h4 className="mt-3 mb-1 font-m-600">
                {currentUser?.firstName} {currentUser?.lastName}
              </h4>
              <div className="font-s-label text-center color-gray">
                {accountTypeString(currentUser?.accountType)}
              </div>
            </div>
          </div>

          <div className="user-menu-items">
            <div
              className={`user-menu-item ${notificationsNum > 0 ? "notification" : ""}`}
              data-notifications={notificationsNum}
              onClick={handleInvitiRicevuti}
            >
              Inviti utente ricevuti
            </div>
            <div className="user-menu-item" onClick={handleProfile}>
              Modifica profilo
            </div>
            {/* <hr className="my-1" /> */}
            <div className="user-menu-item" onClick={handleSignOut}>
              Logout
            </div>
          </div>
        </div>
      )}
    </Fragment>
  );
}
