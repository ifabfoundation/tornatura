import { Fragment } from "react";
import { userMenuActions } from "../features/userMenu/state/userMenu-slice";
import { useAppDispatch, useAppSelector } from "../hooks";
import keycloakInstance from "../providers/keycloak";
import { userSelectors } from "../features/users/state/user-slice";
import { fallbacks } from "../assets/images/fallback";

interface UserMenuProps {
  open: boolean;
}

export default function UserMenu({ open }: UserMenuProps) {
  const dispatch = useAppDispatch();
  const currentUser = useAppSelector(userSelectors.selectCurrentUser);

  const handleSignOut = () => {
    keycloakInstance.logout();
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
              // style={{ backgroundImage: `url(${currentUser?.avatar || fallbacks.avatar})` }}
              style={{ backgroundImage: `url(${fallbacks.avatar})` }}
            ></div>
            <div className="user-info">
              <h4 className="mt-3 mb-1">
                {currentUser?.firstName} {currentUser?.lastName}
              </h4>
              <div className="font-s-label text-center color-gray">{currentUser?.accountType}</div>
            </div>
          </div>

          <div className="user-menu-items">
            <div className="user-menu-item">Modifica profilo</div>
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
