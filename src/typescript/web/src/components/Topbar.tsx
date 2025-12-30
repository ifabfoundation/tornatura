import React from "react";
import { useAppDispatch, useAppSelector } from "../hooks";
import { userSelectors } from "../features/users/state/user-slice";
import { userMenuActions } from "../features/userMenu/state/userMenu-slice";
import { headerbarSelectors } from "../features/headerbar/state/headerbar-slice";
import larr from "../assets/images/larr.svg";
import { useNavigate } from "react-router-dom";
import { fallbacks } from "../assets/images/fallback";
import {
  invitationsActions,
  invitationsSelectors,
} from "../features/invitations/state/invitations-slice";

interface TopBarProps {
  showBackButton?: boolean;
}

export default function TopBar({ showBackButton }: TopBarProps) {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const currentUser = useAppSelector(userSelectors.selectCurrentUser);
  const title = useAppSelector(headerbarSelectors.selectTitle);
  const invitations = useAppSelector(invitationsSelectors.selectMyInvitations);
  const notificationsNum = invitations.length;

  React.useEffect(() => {
    dispatch(invitationsActions.fetchMyInvitationsAction());
  }, []);

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
        <div className="font-s-label pointer" onClick={() => dispatch(userMenuActions.toggle())}>
          {currentUser?.firstName} {currentUser?.lastName}
        </div>
      </div>
      <div
        className={`user-avatar pointer ${notificationsNum > 0 ? "notification" : ""}`}
        data-notifications={notificationsNum}
        onClick={() => dispatch(userMenuActions.toggle())}
        style={{ backgroundImage: `url(${currentUser?.avatar || fallbacks.avatar})` }}
        // style={{ backgroundImage: `url(${fallbacks.avatar})` }}
      ></div>
      <span>{" "}</span>
      {/* 
      <a className="button secondary" data-type="round" onClick={handleSignOut}>
        <Icon iconName="logout" color="yellow" />
      </a>
       */}
    </div>
  );
}
