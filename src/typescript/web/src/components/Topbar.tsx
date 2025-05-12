import { useAppDispatch, useAppSelector } from "../hooks";
import { userSelectors } from "../features/users/state/user-slice";
import keycloakInstance from "../providers/keycloak";
import { headerbarSelectors } from "../features/headerbar/state/headerbar-slice";
import larr from "../assets/images/larr.svg";
import { useNavigate } from "react-router-dom";
import Icon from "./Icon";

interface TopBarProps {
  showBackButton?: boolean;
}

export default function TopBar({ showBackButton }: TopBarProps) {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const currentUser = useAppSelector(userSelectors.selectCurrentUser);
  const title = useAppSelector(headerbarSelectors.selectTitle);

  const handleSignOut = () => {
    keycloakInstance.logout();
  };

  return (
    <div className="headerbar">
      {showBackButton && (
        <div className="back" onClick={() => navigate(-1)}>
          <img src={larr} alt="back" />
        </div>
      )}
      <div className="texts">
        <div className="title">
          <h2>{title}</h2>
          <div className="title-comment"></div>
        </div>
        <div className="font-s-label">
          {currentUser?.firstName} {currentUser?.lastName}
        </div>
      </div>
      <div className="user-icon"></div>
      <a className="button secondary ml-2" data-type="round" onClick={handleSignOut}>
        <Icon iconName="logout" state="normal" />
      </a>
    </div>
  );
}
